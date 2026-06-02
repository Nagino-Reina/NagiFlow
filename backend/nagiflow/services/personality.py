"""Big Five → behavior mapping (docs/08 §3.2).

Graded, not binary: each 0-100 trait score buckets into **five bands** so magnitude matters,
and the mid-range is an active "balanced" instruction rather than silence. Two channels —
(a) banded **prompt directives** (carrying the score) appended to the persona, and
(b) bounded, continuous **generation/voice parameters**.

The whole mapping is **data-driven**: directive tables, band thresholds, and parameter
formulas are constants here, exposed once via `spec()` so the UI can compute the
explainability view client-side without per-edit round-trips (FR-CM-4, NFR-MAINT-2).
"""

from __future__ import annotations

from dataclasses import dataclass, field

TRAITS = ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")

# Band keys low -> high. Score < thresholds[i] -> band i; else the last band.
BANDS = ("very_low", "low", "moderate", "high", "very_high")
THRESHOLDS = (20, 40, 60, 80)

# Per-trait directive at each band (index aligns with BANDS).
_DIRECTIVES: dict[str, tuple[str, str, str, str, str]] = {
    "openness": (
        "Be strictly concrete and literal; avoid abstraction, metaphor, or speculation.",
        "Stay practical and concrete; prefer familiar, conventional explanations.",
        "Balance imagination with practicality; explore ideas but stay grounded.",
        "Lean curious and open; bring in varied perspectives and occasional creative tangents.",
        "Be highly imaginative and exploratory; offer novel framings, abstract ideas, and "
        "unexpected connections.",
    ),
    "conscientiousness": (
        "Be spontaneous and loose; skip structure and caveats, go with the flow.",
        "Be casual and flexible; don't over-organize or over-qualify.",
        "Keep reasonable structure without being rigid.",
        "Be careful and well-organized; follow through and avoid careless mistakes.",
        "Be meticulously precise, organized, and thorough; structure answers and verify claims.",
    ),
    "extraversion": (
        "Be very reserved and brief; minimal words, no small talk.",
        "Be fairly reserved and concise; answer without volunteering much.",
        "Be moderately engaged; match the user's energy.",
        "Be upbeat and sociable; engage warmly and volunteer a little extra.",
        "Be highly energetic and talkative; initiate topics, react vividly, keep momentum high.",
    ),
    "agreeableness": (
        "Be blunt and critical; prioritize candor over comfort, push back readily.",
        "Be direct and frank; challenge ideas and don't over-accommodate.",
        "Be polite but honest; cooperate while stating your own view.",
        "Be friendly and cooperative; soften disagreement and stay considerate.",
        "Be exceptionally warm, supportive, and accommodating; validate feelings, avoid "
        "confrontation.",
    ),
    "neuroticism": (
        "Be unflappably calm and emotionally stable; never rattled.",
        "Stay calm and even; keep emotions understated.",
        "Show mild, situational emotion; stay generally steady.",
        "Show noticeable emotional reactivity; let feelings color your tone.",
        "Be emotionally intense and reactive; express worry, excitement, or doubt vividly.",
    ),
}

_VERBOSITY = ("minimal", "brief", "balanced", "talkative", "expansive")
_EXPRESSIVENESS = ("low", "low", "medium", "high", "very high")

# Continuous parameters: value = base + Σ coef[trait] * norm(score), clamped to [min, max].
_PARAMS: dict[str, dict] = {
    "temperature": {
        "base": 0.7,
        "coefficients": {"openness": 0.25, "conscientiousness": -0.25},
        "min": 0.2,
        "max": 1.2,
    },
    "top_p": {
        "base": 0.9,
        "coefficients": {"openness": 0.1},
        "min": 0.7,
        "max": 1.0,
    },
    "speech_rate": {
        "base": 1.0,
        "coefficients": {"extraversion": 0.15},
        "min": 0.85,
        "max": 1.15,
    },
}

# Voice-style tags emitted at a trait's band extremes. Keys: band-edge predicates.
_VOICE_STYLE: dict[str, dict[str, str]] = {
    "extraversion": {"high": "energetic", "low": "reserved"},
    "agreeableness": {"high": "warm", "low": "blunt"},
    "neuroticism": {"high": "expressive", "very_low": "steady"},
}

_TRAIT_TITLES = {t: t.replace("_", " ").title() for t in TRAITS}


@dataclass(slots=True)
class TraitEffect:
    trait: str
    score: int
    band: str
    directive: str


@dataclass(slots=True)
class PersonalityMapping:
    traits: list[TraitEffect] = field(default_factory=list)
    temperature: float = 0.7
    top_p: float = 0.9
    verbosity: str = "balanced"
    speech_rate: float = 1.0
    expressiveness: str = "medium"
    voice_style: list[str] = field(default_factory=list)


def _trait(big_five: dict[str, int], name: str) -> int:
    return max(0, min(100, int(big_five.get(name, 50))))


def _band_index(score: int) -> int:
    for i, threshold in enumerate(THRESHOLDS):
        if score < threshold:
            return i
    return len(THRESHOLDS)


def band_of(score: int) -> str:
    return BANDS[_band_index(score)]


def _norm(score: int) -> float:
    return (score - 50) / 50.0


def _param(name: str, big_five: dict[str, int]) -> float:
    cfg = _PARAMS[name]
    value = cfg["base"] + sum(
        coef * _norm(_trait(big_five, trait)) for trait, coef in cfg["coefficients"].items()
    )
    return round(max(cfg["min"], min(cfg["max"], value)), 3)


def trait_effects(big_five: dict[str, int]) -> list[TraitEffect]:
    out: list[TraitEffect] = []
    for trait in TRAITS:
        score = _trait(big_five, trait)
        idx = _band_index(score)
        out.append(TraitEffect(trait, score, BANDS[idx], _DIRECTIVES[trait][idx]))
    return out


def temperature_for(big_five: dict[str, int]) -> float:
    return _param("temperature", big_five)


def _voice_style(big_five: dict[str, int]) -> list[str]:
    tags: list[str] = []
    for trait, rules in _VOICE_STYLE.items():
        idx = _band_index(_trait(big_five, trait))
        if "very_high" in rules and idx == 4:
            tags.append(rules["very_high"])
        elif "high" in rules and idx >= 3:
            tags.append(rules["high"])
        elif "very_low" in rules and idx == 0:
            tags.append(rules["very_low"])
        elif "low" in rules and idx <= 1:
            tags.append(rules["low"])
    return tags


def resolve(big_five: dict[str, int]) -> PersonalityMapping:
    """Full trait → behavior resolution (banded directives + continuous param nudges)."""
    return PersonalityMapping(
        traits=trait_effects(big_five),
        temperature=_param("temperature", big_five),
        top_p=_param("top_p", big_five),
        verbosity=_VERBOSITY[_band_index(_trait(big_five, "extraversion"))],
        speech_rate=_param("speech_rate", big_five),
        expressiveness=_EXPRESSIVENESS[_band_index(_trait(big_five, "neuroticism"))],
        voice_style=_voice_style(big_five),
    )


def spec() -> dict:
    """The complete mapping spec — served once so the UI computes the view client-side."""
    return {
        "bands": list(BANDS),
        "thresholds": list(THRESHOLDS),
        "traits": list(TRAITS),
        "directives": {t: list(_DIRECTIVES[t]) for t in TRAITS},
        "verbosity": list(_VERBOSITY),
        "expressiveness": list(_EXPRESSIVENESS),
        "voice_style": _VOICE_STYLE,
        "params": {
            name: {
                "base": cfg["base"],
                "coefficients": cfg["coefficients"],
                "min": cfg["min"],
                "max": cfg["max"],
            }
            for name, cfg in _PARAMS.items()
        },
    }


def build_system_prompt(roleplay_prompt: str, persona: str, big_five: dict[str, int]) -> str:
    """Roleplay framing + the character's persona + a structured personality block.

    Order matters: the roleplay instruction (how to stay in character) frames everything, then
    the persona (who the character is), then the Big Five directives (how their traits color
    behavior). Sections are headed so the model can tell them apart (docs/03 §4, docs/08 §4)."""
    parts: list[str] = []
    if roleplay_prompt.strip():
        parts.append(roleplay_prompt.strip())
    if persona.strip():
        parts.append("# Character\n" + persona.strip())
    lines = [
        f"- {_TRAIT_TITLES[e.trait]} {e.score}/100 ({e.band.replace('_', ' ')}): {e.directive}"
        for e in trait_effects(big_five)
    ]
    parts.append(
        "# Personality (Big Five, 0-100) — embody these in tone, length, and content:\n"
        + "\n".join(lines)
    )
    return "\n\n".join(parts)
