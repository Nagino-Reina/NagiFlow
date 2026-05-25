"""VOICEVOX TTS plugin."""

from nagiflow.plugin.base import BasePlugin, PluginMeta
from nagiflow.plugin.registry import registry


class TTSVoicevoxPlugin(BasePlugin):
    meta = PluginMeta(
        name="tts_voicevox",
        version="1.0.0",
        description="VOICEVOX high-quality Japanese TTS provider.",
    )

    async def setup(self) -> None:
        from .provider import VoicevoxProvider

        registry.register_tts("voicevox", VoicevoxProvider)
