"""
Audio and static asset serving endpoints.

All audio files and character assets are served from the workspace via these
endpoints.  Access is gated on JWT authentication so users cannot access each
other's cached audio files.
"""

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from nagiflow.api.deps import get_current_active_user
from nagiflow.core.exceptions import NotFoundError
from nagiflow.core.workspace import workspace
from nagiflow.models.user import User

router = APIRouter(prefix="/audio", tags=["Audio"])


@router.get("/{file_path:path}")
async def serve_audio(
    file_path: str,
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """
    Serve a workspace-relative audio file.

    The *file_path* parameter is the workspace-relative path returned by
    the TTS generation endpoints (e.g. ``audio_cache/<uuid>/file.wav``).
    """
    abs_path = workspace.abs_path(file_path)

    # Prevent directory traversal
    try:
        abs_path.resolve().relative_to(workspace.base.resolve())
    except ValueError:
        raise NotFoundError("File not found.")

    if not abs_path.exists() or not abs_path.is_file():
        raise NotFoundError(f"Audio file '{file_path}' not found.")

    suffix = abs_path.suffix.lower()
    media_type_map = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }
    media_type = media_type_map.get(suffix, "application/octet-stream")

    return FileResponse(abs_path, media_type=media_type, filename=abs_path.name)
