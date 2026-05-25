"""
Workspace manager.

At runtime NagiFlow keeps all dynamic assets (character models, voice samples,
knowledge files, plugin source, audio cache) under a single ``workspace``
directory on the host.  This module is responsible for bootstrapping that
directory tree and providing path helpers used throughout the application.
"""

import shutil
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import aiofiles
import aiofiles.os
from loguru import logger

from nagiflow.config import settings
from nagiflow.core.exceptions import UnsupportedFileTypeError, WorkspaceError

if TYPE_CHECKING:
    pass

# Allowed MIME / extension sets per asset category
ALLOWED_MODEL_EXTENSIONS = {".model3.json", ".moc3", ".zip", ".vrm", ".glb", ".gltf"}
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_DOCUMENT_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".json", ".csv"}

MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB


class WorkspaceManager:
    """Singleton-like class for all workspace I/O operations."""

    def __init__(self, base: Path) -> None:
        self.base = base
        self._subdirs = [
            "characters",
            "knowledge",
            "plugins",
            "audio_cache",
            "training",
            "temp",
        ]

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    def ensure_structure(self) -> None:
        """Create the workspace directory tree if it doesn't exist (sync)."""
        self.base.mkdir(parents=True, exist_ok=True)
        for sub in self._subdirs:
            (self.base / sub).mkdir(exist_ok=True)
        logger.info(f"Workspace ready at '{self.base.resolve()}'")

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def character_dir(self, character_id: UUID) -> Path:
        return self.base / "characters" / str(character_id)

    def character_models_dir(self, character_id: UUID) -> Path:
        return self.character_dir(character_id) / "models"

    def character_voice_dir(self, character_id: UUID) -> Path:
        return self.character_dir(character_id) / "voice_samples"

    def character_avatar_dir(self, character_id: UUID) -> Path:
        return self.character_dir(character_id) / "avatar"

    def knowledge_dir(self) -> Path:
        return self.base / "knowledge"

    def plugins_dir(self) -> Path:
        return self.base / "plugins"

    def audio_cache_dir(self) -> Path:
        return self.base / "audio_cache"

    def temp_dir(self) -> Path:
        return self.base / "temp"

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    async def ensure_dir(self, path: Path) -> None:
        await aiofiles.os.makedirs(path, exist_ok=True)

    async def save_file(
        self,
        dest: Path,
        data: bytes,
        allowed_extensions: set[str] | None = None,
    ) -> Path:
        """Write *data* to *dest*, optionally validating the extension."""
        if allowed_extensions:
            ext = "".join(dest.suffixes).lower()
            if ext not in allowed_extensions:
                raise UnsupportedFileTypeError(
                    f"File extension '{ext}' is not allowed. "
                    f"Accepted: {sorted(allowed_extensions)}"
                )
        if len(data) > MAX_UPLOAD_BYTES:
            raise WorkspaceError(
                f"File exceeds maximum upload size of {MAX_UPLOAD_BYTES // 1_048_576} MB."
            )
        await self.ensure_dir(dest.parent)
        async with aiofiles.open(dest, "wb") as f:
            await f.write(data)
        logger.debug(f"Saved file: {dest}")
        return dest

    async def delete_file(self, path: Path) -> None:
        try:
            await aiofiles.os.remove(path)
            logger.debug(f"Deleted file: {path}")
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise WorkspaceError(f"Could not delete '{path}': {exc}") from exc

    async def delete_character_workspace(self, character_id: UUID) -> None:
        """Remove the entire directory tree for a character."""
        char_dir = self.character_dir(character_id)
        if char_dir.exists():
            shutil.rmtree(char_dir, ignore_errors=True)
            logger.info(f"Removed workspace for character {character_id}")

    def relative_to_workspace(self, path: Path) -> str:
        """Return a path string relative to the workspace root (for storage in DB)."""
        try:
            return str(path.relative_to(self.base))
        except ValueError:
            return str(path)

    def abs_path(self, relative: str) -> Path:
        """Reconstruct an absolute path from a workspace-relative string."""
        return self.base / relative


# Module-level singleton, initialised in main.py
workspace: WorkspaceManager = WorkspaceManager(settings.WORKSPACE_DIR)
