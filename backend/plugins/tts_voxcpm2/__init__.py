"""VoxCPM2 TTS plugin."""

from nagiflow.plugin.base import BasePlugin, PluginMeta
from nagiflow.plugin.registry import registry


class TTSVoxCPM2Plugin(BasePlugin):
    meta = PluginMeta(
        name="tts_voxcpm2",
        version="1.0.0",
        description="VoxCPM2 local TTS provider (tokenizer-free, 30 languages).",
    )

    async def setup(self) -> None:
        from .provider import VoxCPM2Provider

        registry.register_tts("voxcpm2", VoxCPM2Provider)
