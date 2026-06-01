"""Media endpoints (docs/05 §4.6).

P1 exposes owner-checked download of synthesized reply audio (docs/11 §4.6); the media
library (list/metadata) and script-render assets land in P2.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..deps import CurrentPrincipal, Media

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{media_id}:download")
async def download_media(media_id: str, principal: CurrentPrincipal, svc: Media) -> FileResponse:
    path, media_type = await svc.resolve_owned(media_id, principal.user_id)
    return FileResponse(path, media_type=media_type)
