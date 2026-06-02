"""Voice service — voice models + TTS preview (docs/08 §4, FR-CM-5/7).

Owns voice-model lifecycle (zero-shot clone, voice design), reference-clip storage under the
workspace, default selection, and turning text into audio through the active TTS provider.
Fine-tune training (`fine_tuned`) is deferred to P6.
"""

from __future__ import annotations

from pathlib import Path

from ..core import errors
from ..core.ids import new_id
from ..core.logging import get_logger
from ..models.character import Character, VoiceModel
from ..providers.base import ProviderError, VoiceRef
from ..providers.registry import ProviderRegistry
from ..repositories.characters import CharacterRepository
from ..repositories.voice_models import VoiceModelRepository
from . import personality

_SAMPLE_TEXT = "Hi, this is how I sound."

log = get_logger("nagiflow.voice")


class VoiceService:
    def __init__(
        self,
        voices: VoiceModelRepository,
        characters: CharacterRepository,
        registry: ProviderRegistry,
        workspace_dir: Path,
    ) -> None:
        self.voices = voices
        self.characters = characters
        self.registry = registry
        self.workspace_dir = workspace_dir

    async def _require_character(self, character_id: str) -> None:
        character = await self.characters.get(character_id)
        if character is None or character.status == "archived":
            raise errors.not_found("character", character_id)

    async def list(self, character_id: str) -> list[VoiceModel]:
        await self._require_character(character_id)
        return await self.voices.list_for_character(character_id)

    async def _is_first(self, character_id: str) -> bool:
        return not await self.voices.list_for_character(character_id)

    def _reference_key(self, character_id: str, voice_model_id: str) -> str:
        return f"characters/{character_id}/voice/reference/{voice_model_id}.wav"

    async def create_zero_shot(
        self, character_id: str, *, reference: bytes, sample_text: str | None = None
    ) -> VoiceModel:
        """Clone from a reference clip; stores the clip under the workspace."""
        await self._require_character(character_id)
        provider = self.registry.get_tts()
        if not provider.capabilities.voice_clone:
            raise errors.capability_unsupported("voice_clone")

        vid = new_id("vm")
        key = self._reference_key(character_id, vid)
        dest = self.workspace_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(reference)

        model = VoiceModel(
            id=vid,
            character_id=character_id,
            kind="zero_shot",
            provider=provider.name,
            version=1,
            reference_keys=[key],
            params={"sample_text": sample_text} if sample_text else {},
            status="ready",
            is_default=await self._is_first(character_id),
        )
        self.voices.add(model)
        await self.voices.flush()
        return model

    async def create_voice_design(self, character_id: str, *, description: str) -> VoiceModel:
        await self._require_character(character_id)
        provider = self.registry.get_tts()
        if not provider.capabilities.voice_design:
            raise errors.capability_unsupported("voice_design")

        model = VoiceModel(
            id=new_id("vm"),
            character_id=character_id,
            kind="voice_design",
            provider=provider.name,
            version=1,
            reference_keys=[],
            design_description=description,
            params={},
            status="ready",
            is_default=await self._is_first(character_id),
        )
        self.voices.add(model)
        await self.voices.flush()
        return model

    async def set_default(self, character_id: str, voice_model_id: str) -> VoiceModel:
        await self._require_character(character_id)
        models = await self.voices.list_for_character(character_id)
        target = next((m for m in models if m.id == voice_model_id), None)
        if target is None:
            raise errors.not_found("voice_model", voice_model_id)
        for m in models:
            m.is_default = m.id == voice_model_id
        await self.voices.flush()
        return target

    async def delete(self, character_id: str, voice_model_id: str) -> None:
        await self._require_character(character_id)
        models = await self.voices.list_for_character(character_id)
        target = next((m for m in models if m.id == voice_model_id), None)
        if target is None:
            raise errors.not_found("voice_model", voice_model_id)

        for key in target.reference_keys or []:
            try:
                (self.workspace_dir / key).unlink(missing_ok=True)
            except OSError:
                pass  # storage cleanup is best-effort

        was_default = target.is_default
        await self.voices.delete(target)
        if was_default:
            remaining = [m for m in models if m.id != voice_model_id]
            if remaining:
                remaining[0].is_default = True
        await self.voices.flush()

    def _voice_ref(self, model: VoiceModel | None) -> VoiceRef:
        if model is None:
            return VoiceRef(kind="voice_design", design_description="default")
        return VoiceRef(
            kind=model.kind,
            reference_paths=[str(self.workspace_dir / k) for k in (model.reference_keys or [])],
            design_description=model.design_description,
            artifact_path=str(self.workspace_dir / model.artifact_key)
            if model.artifact_key
            else None,
            params=dict(model.params or {}),
        )

    async def _default_voice_model(self, character_id: str) -> VoiceModel | None:
        models = await self.voices.list_for_character(character_id)
        return next((m for m in models if m.is_default), models[0] if models else None)

    async def synthesize_reply(
        self, character: Character, *, text: str, style: str | None = None, speech_rate: float = 1.0
    ) -> bytes | None:
        """Render a chat reply to WAV with the character's default voice (docs/11 §4.6).

        Best-effort: returns None (logged) when there is nothing to say or the provider fails,
        so a TTS problem never blocks the text reply.
        """
        if not text.strip():
            return None
        model = await self._default_voice_model(character.id)
        provider = self.registry.get_tts(model.provider if model else None)
        try:
            return await provider.synthesize(
                text=text, voice=self._voice_ref(model), style=style, speech_rate=speech_rate
            )
        except (ProviderError, OSError) as exc:
            log.warning("reply TTS synthesis failed (character=%s): %s", character.id, exc)
            return None

    async def synthesize_line(
        self,
        character: Character,
        *,
        text: str,
        line_style: str | None = None,
        line_speech_rate: float | None = None,
    ) -> bytes:
        """Render a script line with the speaker's voice (docs/07 §3.2, FR-SM-8).

        Considers the speaker: their default voice model (timbre) plus personality-derived
        voice style and base speech rate, with the line's own `style` / `speech_rate` layered
        on top. Errors surface as a provider envelope (unlike best-effort reply synthesis)."""
        if not text.strip():
            raise errors.AppError(
                "script.empty_line", "Line has no text to synthesize.", status_code=422
            )
        mapping = personality.resolve(character.big_five)
        tags = [*mapping.voice_style, line_style] if line_style else list(mapping.voice_style)
        style = ", ".join(t for t in tags if t) or None
        speech_rate = line_speech_rate if line_speech_rate is not None else mapping.speech_rate
        model = await self._default_voice_model(character.id)
        provider = self.registry.get_tts(model.provider if model else None)
        try:
            return await provider.synthesize(
                text=text, voice=self._voice_ref(model), style=style, speech_rate=speech_rate
            )
        except (ProviderError, OSError) as exc:
            log.warning("line TTS synthesis failed (character=%s): %s", character.id, exc)
            raise errors.provider_error(provider.name, str(exc)) from exc

    async def preview(
        self,
        character_id: str,
        *,
        text: str | None = None,
        voice_model_id: str | None = None,
        style: str | None = None,
        speech_rate: float = 1.0,
    ) -> bytes:
        await self._require_character(character_id)

        model: VoiceModel | None = None
        if voice_model_id:
            model = await self.voices.get(voice_model_id)
            if model is None or model.character_id != character_id:
                raise errors.not_found("voice_model", voice_model_id)

        provider = self.registry.get_tts(model.provider if model else None)
        try:
            return await provider.synthesize(
                text=text or _SAMPLE_TEXT,
                voice=self._voice_ref(model),
                style=style,
                speech_rate=speech_rate,
            )
        except (ProviderError, OSError) as exc:
            # Surfaced as a 502 envelope; also logged since AppError carries no traceback.
            log.warning("voice preview failed (character=%s): %s", character_id, exc)
            raise errors.provider_error(provider.name, str(exc)) from exc
