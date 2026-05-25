"""
PNGTuber avatar provider.

Characters have a set of PNG images stored under their workspace avatar folder:
    workspace/characters/{id}/avatar/
        idle_default.png
        talking_default.png
        blinking_default.png
        idle_happy.png         (optional expression variants)
        talking_happy.png
        ...

The provider computes the current AvatarState from audio activity and
expression context.  The actual image rendering is done in the browser.

Expression tags in LLM text ([happy], [sad], etc.) are detected by the
parent AvatarProvider interface and mapped to expression names.
"""

from nagiflow.plugin.base import AvatarState, BaseAvatarProvider

STATES = ["idle", "talking", "blinking"]
EXPRESSIONS = ["default", "happy", "sad", "angry", "surprised"]


class PNGTuberProvider(BaseAvatarProvider):
    provider_name = "pngtuber"

    def get_states(self) -> list[str]:
        return STATES

    def get_expressions(self) -> list[str]:
        return EXPRESSIONS

    def compute_state(self, audio_active: bool, expression: str = "default") -> AvatarState:
        state = "talking" if audio_active else "idle"
        expr = expression if expression in EXPRESSIONS else "default"
        return AvatarState(state=state, expression=expr)

    def asset_filename(self, state: str, expression: str = "default") -> str:
        """Return the expected PNG filename for a given state+expression pair."""
        expr = expression if expression in EXPRESSIONS else "default"
        return f"{state}_{expr}.png"

    def fallback_filename(self, state: str) -> str:
        """Fallback filename when specific expression variant is not uploaded."""
        return f"{state}_default.png"
