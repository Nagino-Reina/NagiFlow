"""Shared TTS resolution helper for services."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nagiflow.plugin.base import BaseTTSProvider, TTSConfig


def resolve_tts(
    character: Any = None,
    *,
    speaker_id_override: int | None = None,
) -> "tuple[BaseTTSProvider, TTSConfig]":
    """
    Return (tts_provider, TTSConfig) resolved from an optional character object.

    Priority: explicit override > character fields > settings defaults.
    """
    from nagiflow.config import settings
    from nagiflow.plugin.base import TTSConfig
    from nagiflow.plugin.registry import registry

    provider_name = (
        getattr(character, "tts_provider", None) or settings.DEFAULT_TTS_PROVIDER
    )
    speaker_id = (
        speaker_id_override
        or getattr(character, "tts_speaker_id", None)
        or settings.DEFAULT_VOICEVOX_SPEAKER
    )
    return registry.get_tts(provider_name), TTSConfig(speaker_id=speaker_id)
