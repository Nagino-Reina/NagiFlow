"""Emotion & affect engine (docs/10).

Three layers: stable **personality** (Big Five) → medium-term **mood** → short-term
**emotion**. Each turn the service *appraises* the stimulus (partner + content; memory is a
seam), launches an emotion from the current mood gated by personality dynamics, decays mood
toward a personality baseline, and exposes the result as a prompt directive, a voice
style/rate nudge, and an avatar expression event (docs/10 §7).

Appraisal is **hybrid**: a cheap structured LLM call when a real model is available, falling
back to a deterministic lexicon/heuristic (and ultimately neutral) so chat works fully
offline (docs/10 §3.2). The pure functions below are deterministic and unit-tested.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from ..core.ids import new_id
from ..models.affect import AffectState
from ..models.character import Character
from ..models.conversation import Message
from ..providers.base import ChatMessage, GenRequest
from ..providers.registry import ProviderRegistry
from ..repositories.affect import AffectStateRepository

# --- representation -------------------------------------------------------------------

NEUTRAL_RADIUS = 0.15


@dataclass(frozen=True, slots=True)
class VAD:
    v: float = 0.0
    a: float = 0.0
    d: float = 0.0

    def clamp(self) -> VAD:
        return VAD(_clamp(self.v), _clamp(self.a), _clamp(self.d))

    def lerp(self, other: VAD, t: float) -> VAD:
        return VAD(
            self.v + t * (other.v - self.v),
            self.a + t * (other.a - self.a),
            self.d + t * (other.d - self.d),
        )

    def distance(self, other: VAD) -> float:
        return math.sqrt(
            (self.v - other.v) ** 2 + (self.a - other.a) ** 2 + (self.d - other.d) ** 2
        )

    def magnitude(self) -> float:
        return math.sqrt(self.v**2 + self.a**2 + self.d**2)

    def to_dict(self) -> dict[str, float]:
        return {"v": round(self.v, 4), "a": round(self.a, 4), "d": round(self.d, 4)}


# discrete labels → VAD centroid (docs/10 §2.2)
EMOTION_CENTROIDS: dict[str, VAD] = {
    "joy": VAD(0.8, 0.5, 0.3),
    "affection": VAD(0.7, 0.2, 0.1),
    "curiosity": VAD(0.4, 0.4, 0.1),
    "surprise": VAD(0.1, 0.7, -0.1),
    "sadness": VAD(-0.7, -0.4, -0.3),
    "anger": VAD(-0.6, 0.6, 0.4),
    "fear": VAD(-0.6, 0.6, -0.5),
    "disgust": VAD(-0.6, 0.2, 0.1),
}

# emotion label → voice style tag + speech-rate delta (docs/10 §7.2)
VOICE_STYLE: dict[str, tuple[str, float]] = {
    "joy": ("cheerful", 0.05),
    "affection": ("warm", -0.02),
    "curiosity": ("bright", 0.03),
    "surprise": ("surprised", 0.04),
    "sadness": ("soft", -0.08),
    "anger": ("intense", 0.05),
    "fear": ("tense", 0.03),
    "disgust": ("flat", -0.02),
    "neutral": ("", 0.0),
}

# emotion label → avatar expression event (docs/10 §7.3)
EXPRESSION_MAP: dict[str, str] = {
    "joy": "happy",
    "affection": "happy",
    "curiosity": "neutral",
    "surprise": "surprised",
    "sadness": "sad",
    "anger": "angry",
    "fear": "surprised",
    "disgust": "disgust",
    "neutral": "neutral",
}

# small affect lexicon for the deterministic fallback (docs/10 §3.2)
_POS = {
    "good",
    "great",
    "love",
    "loved",
    "happy",
    "glad",
    "thanks",
    "thank",
    "awesome",
    "nice",
    "wonderful",
    "excited",
    "amazing",
    "perfect",
    "yay",
    "haha",
    "cool",
    "fun",
}
_NEG = {
    "hate",
    "hated",
    "bad",
    "sad",
    "angry",
    "terrible",
    "awful",
    "stupid",
    "annoying",
    "worried",
    "afraid",
    "scared",
    "sorry",
    "upset",
    "horrible",
    "disgusting",
    "cry",
}
_AROUSAL = {"amazing", "wow", "urgent", "now", "help", "excited", "angry", "scared", "yay"}
_NEGATORS = {"not", "no", "never", "n't"}


@dataclass(frozen=True, slots=True)
class Dynamics:
    reactivity: float
    drift: float
    decay: float
    baseline: VAD


@dataclass(slots=True)
class Affect:
    vad: VAD
    label: str
    intensity: float
    source: str  # "llm" | "fallback"

    def to_dict(self) -> dict:
        return {
            "vad": self.vad.to_dict(),
            "label": self.label,
            "intensity": round(self.intensity, 4),
            "source": self.source,
        }


@dataclass(slots=True)
class AffectResult:
    affect: Affect
    directive: str
    voice_style: list[str] = field(default_factory=list)
    speech_rate_delta: float = 0.0
    expression: str = "neutral"


# --- pure helpers ---------------------------------------------------------------------


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _center(big_five: dict, name: str) -> float:
    """Trait score 0-100 → centered [-0.5, 0.5]."""
    score = max(0, min(100, int(big_five.get(name, 50))))
    return score / 100.0 - 0.5


def dynamics_for(big_five: dict) -> Dynamics:
    """Big Five → emotion dynamics (docs/10 §4). Personality governs *how* emotion moves."""
    n = _center(big_five, "neuroticism")
    c = _center(big_five, "conscientiousness")
    a = _center(big_five, "agreeableness")
    e = _center(big_five, "extraversion")
    reactivity = _clamp(0.5 + 0.8 * n, 0.25, 0.9)
    drift = _clamp(0.15 + 0.3 * n - 0.1 * c, 0.05, 0.3)
    decay = _clamp(0.45 - 0.4 * n + 0.2 * c, 0.2, 0.7)
    baseline = VAD(
        v=_clamp(0.5 * a + 0.3 * e - 0.3 * n),
        a=_clamp(0.4 * e),
        d=_clamp(0.4 * c - 0.3 * n),
    )
    return Dynamics(reactivity=reactivity, drift=drift, decay=decay, baseline=baseline)


def lexicon_appraise(text: str) -> VAD:
    """Deterministic keyword/heuristic appraisal → stimulus VAD (docs/10 §3.2 fallback)."""
    if not text:
        return VAD()
    lowered = text.lower()
    tokens = re.findall(r"[a-z']+", lowered)
    if not tokens:
        return VAD()
    pos = sum(1 for t in tokens if t in _POS)
    neg = sum(1 for t in tokens if t in _NEG)
    valence = (pos - neg) / (pos + neg) if (pos + neg) else 0.0
    if any(t in _NEGATORS for t in tokens) and valence != 0.0:
        valence = -0.5 * valence  # rough negation handling
    exclaim = min(3, text.count("!"))
    arousal_hits = sum(1 for t in tokens if t in _AROUSAL)
    caps_ratio = sum(1 for ch in text if ch.isupper()) / max(1, len(text))
    arousal = _clamp(0.15 * exclaim + 0.25 * min(2, arousal_hits) + 0.5 * caps_ratio)
    return VAD(_clamp(valence), arousal, 0.0)


def discretize(vad: VAD) -> tuple[str, float]:
    """VAD → (discrete label, intensity) by nearest centroid (docs/10 §2.2)."""
    magnitude = vad.magnitude()
    intensity = _clamp(magnitude / math.sqrt(3.0), 0.0, 1.0)
    if magnitude < NEUTRAL_RADIUS:
        return "neutral", round(intensity, 4)
    label = min(EMOTION_CENTROIDS, key=lambda k: vad.distance(EMOTION_CENTROIDS[k]))
    return label, round(intensity, 4)


def step(
    mood: VAD, emotion_prev: VAD, stimulus: VAD, dyn: Dynamics, idle_seconds: float = 0.0
) -> tuple[VAD, VAD]:
    """One affect update (docs/10 §6): decay residue → react → integrate mood → relax."""
    residue = emotion_prev.lerp(mood, dyn.decay)
    emotion = residue.lerp(stimulus, dyn.reactivity).clamp()
    mood = mood.lerp(emotion, dyn.drift)
    mu = min(0.6, 0.05 + (idle_seconds / 3600.0) * 0.1)
    mood = mood.lerp(dyn.baseline, mu).clamp()
    return emotion, mood


def build_directive(label: str, intensity: float, vad: VAD) -> str:
    """Prompt block describing the current emotion (docs/10 §7.1). Empty when neutral."""
    if label == "neutral" or intensity < 0.1:
        return ""
    return (
        "Current emotional state (a passing mood, not your stable personality):\n"
        f"- Feeling: {label} (intensity {intensity:.2f}). "
        f"Valence {vad.v:.2f}, arousal {vad.a:.2f}, dominance {vad.d:.2f}.\n"
        "- Let this color your tone, word choice, and length right now — but stay in "
        "character; do not narrate the emotion unless it is natural to."
    )


def voice_style_for(label: str, vad: VAD) -> tuple[list[str], float]:
    tag, rate_delta = VOICE_STYLE.get(label, ("", 0.0))
    tags = [tag] if tag else []
    return tags, rate_delta


def expression_for(label: str) -> str:
    return EXPRESSION_MAP.get(label, "neutral")


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


# --- service --------------------------------------------------------------------------

_APPRAISE_SYSTEM = (
    "You are an affect appraiser. Read the latest user message in context and rate the "
    "emotional impact it would have on a listener. Reply with ONLY compact JSON: "
    '{"valence": <-1..1>, "arousal": <-1..1>, "dominance": <-1..1>, '
    '"primary_emotion": "<neutral|joy|affection|curiosity|surprise|sadness|anger|fear|'
    'disgust>", "intensity": <0..1>}. No prose.'
)
_APPRAISE_HISTORY = 6


class AffectService:
    def __init__(
        self,
        affect: AffectStateRepository,
        registry: ProviderRegistry,
        settings,
    ) -> None:
        self.affect = affect
        self.registry = registry
        self.settings = settings

    async def process_turn(
        self,
        *,
        character: Character,
        user_id: str | None,
        user_text: str,
        history: list[Message],
    ) -> AffectResult:
        dyn = dynamics_for(character.big_five)
        now = _utcnow()
        state = await self.affect.get_for(character.id, user_id)
        if state is None:
            mood = dyn.baseline
            emotion_prev = dyn.baseline
            idle = 0.0
            state = AffectState(
                id=new_id("aff"),
                character_id=character.id,
                user_id=user_id,
                counterpart_character_id=None,
            )
            self.affect.add(state)
        else:
            mood = VAD(state.mood_v, state.mood_a, state.mood_d)
            emotion_prev = VAD(state.emotion_v, state.emotion_a, state.emotion_d)
            idle = max(0.0, (now - state.updated_at).total_seconds())

        stimulus, source = await self._appraise(character, user_text, history)
        emotion, mood = step(mood, emotion_prev, stimulus, dyn, idle)
        label, intensity = discretize(emotion)

        state.mood_v, state.mood_a, state.mood_d = mood.v, mood.a, mood.d
        state.emotion_v, state.emotion_a, state.emotion_d = emotion.v, emotion.a, emotion.d
        state.emotion_label = label
        state.emotion_intensity = intensity
        state.updated_at = now
        # State is added/mutated but not flushed here: the caller persists it in its own
        # unit-of-work, keeping slow per-turn compute (LLM/TTS) out of an open write txn
        # so the single SQLite writer lock is not held across those awaits (docs/04 §3).

        affect = Affect(vad=emotion, label=label, intensity=intensity, source=source)
        tags, rate_delta = voice_style_for(label, emotion)
        return AffectResult(
            affect=affect,
            directive=build_directive(label, intensity, emotion),
            voice_style=tags,
            speech_rate_delta=rate_delta,
            expression=expression_for(label),
        )

    async def _appraise(
        self, character: Character, user_text: str, history: list[Message]
    ) -> tuple[VAD, str]:
        mode = getattr(self.settings, "affect_appraisal", "hybrid")
        if mode != "deterministic":
            llm = self.registry.get_llm()
            # echo provider can't produce JSON; skip straight to the deterministic path.
            if getattr(llm, "name", "") != "echo":
                try:
                    vad = await self._llm_appraise(llm, user_text, history)
                    if vad is not None:
                        return vad, "llm"
                except Exception:  # noqa: BLE001 - any provider failure → fallback
                    pass
        return lexicon_appraise(user_text), "fallback"

    async def _llm_appraise(self, llm, user_text: str, history: list[Message]) -> VAD | None:
        context: list[ChatMessage] = [ChatMessage(role="system", content=_APPRAISE_SYSTEM)]
        for msg in history[-_APPRAISE_HISTORY:]:
            if msg.role in ("user", "character"):
                role = "assistant" if msg.role == "character" else "user"
                context.append(ChatMessage(role=role, content=msg.content))
        context.append(ChatMessage(role="user", content=user_text))

        req = GenRequest(messages=context, temperature=0.0, max_tokens=120, stream=True)
        parts: list[str] = []
        async for chunk in llm.generate(req):
            if chunk.delta:
                parts.append(chunk.delta)
        return _parse_vad("".join(parts))


def _parse_vad(text: str) -> VAD | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except (ValueError, TypeError):
        return None
    try:
        return VAD(
            _clamp(float(data["valence"])),
            _clamp(float(data["arousal"])),
            _clamp(float(data.get("dominance", 0.0))),
        )
    except (KeyError, TypeError, ValueError):
        return None
