"""Workspace folder layout (docs/04 §2).

A single local folder holds everything for an installation. The DB stores **storage keys**,
never absolute paths, so a workspace stays relocatable.
"""

from __future__ import annotations

from pathlib import Path

SUBDIRS = (
    "config",
    "characters",
    "scripts",
    "media",
    "memory/index",
    "modules",
    "jobs",
    "exports",
    "backups",
    "logs",
)


class Workspace:
    def __init__(self, root: Path) -> None:
        self.root = root

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for sub in SUBDIRS:
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)
