"""Application settings (docs/05 §4.7) — runtime overrides with built-in defaults.

P1 exposes the global **roleplay prompt** (the base instruction prepended to every character's
persona, docs/03 §4). An unset/blank override falls back to the system default from config.
"""

from __future__ import annotations

from ..config import get_settings
from ..repositories.settings import SettingsRepository

_ROLEPLAY_KEY = "roleplay_prompt"


class SettingsService:
    def __init__(self, repo: SettingsRepository) -> None:
        self.repo = repo

    def default_roleplay_prompt(self) -> str:
        return get_settings().roleplay_prompt

    async def roleplay_prompt(self) -> str:
        return await self.repo.get(_ROLEPLAY_KEY) or self.default_roleplay_prompt()

    async def set_roleplay_prompt(self, value: str) -> str:
        """Store an override, or clear it (reset to default) when blank. Returns the effective
        prompt now in use."""
        cleaned = value.strip()
        if cleaned:
            await self.repo.set(_ROLEPLAY_KEY, cleaned)
            return cleaned
        await self.repo.delete(_ROLEPLAY_KEY)
        return self.default_roleplay_prompt()

    async def reset_roleplay_prompt(self) -> str:
        await self.repo.delete(_ROLEPLAY_KEY)
        return self.default_roleplay_prompt()
