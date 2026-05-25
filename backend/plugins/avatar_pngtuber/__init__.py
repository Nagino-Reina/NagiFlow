"""PNGTuber avatar plugin."""

from nagiflow.plugin.base import BasePlugin, PluginMeta
from nagiflow.plugin.registry import registry


class AvatarPNGTuberPlugin(BasePlugin):
    meta = PluginMeta(
        name="avatar_pngtuber",
        version="1.0.0",
        description="PNGTuber avatar provider — state-machine PNG animation.",
    )

    async def setup(self) -> None:
        from .provider import PNGTuberProvider

        registry.register_avatar("pngtuber", PNGTuberProvider)
