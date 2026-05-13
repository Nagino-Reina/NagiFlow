"""NagiFlow TTS layer."""

from loguru import logger

from nagiflow.config import settings
from nagiflow.tts.base import BaseTTSProvider, TTSConfig, TTSResult
from nagiflow.tts.providers.voicevox import VoicevoxProvider

_TTS_PROVIDER_MAP: dict[str, type[BaseTTSProvider]] = {
    "voicevox": VoicevoxProvider,
}


def register_tts_provider(name: str, cls: type[BaseTTSProvider]) -> None:
    """Register a custom TTS provider (called from plugins)."""
    _TTS_PROVIDER_MAP[name] = cls
    logger.info(f"Registered TTS provider: '{name}'")


def get_tts_provider(name: str | None = None) -> BaseTTSProvider:
    provider_name = name or settings.DEFAULT_TTS_PROVIDER
    cls = _TTS_PROVIDER_MAP.get(provider_name)
    if cls is None:
        raise ValueError(
            f"Unknown TTS provider '{provider_name}'. "
            f"Available: {list(_TTS_PROVIDER_MAP)}"
        )
    return cls()


__all__ = [
    "BaseTTSProvider",
    "TTSConfig",
    "TTSResult",
    "VoicevoxProvider",
    "register_tts_provider",
    "get_tts_provider",
]
