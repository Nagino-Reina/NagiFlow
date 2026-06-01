"""Media-asset storage + owner-checked retrieval (docs/04 §5.6, docs/11 §4.6).

P1 stores one audio asset per synthesized chat reply under the workspace `media/` tree and
gates downloads by the owner of the linked message's conversation.
"""

from __future__ import annotations

import io
import wave
from pathlib import Path

from ..core import errors
from ..core.ids import new_id
from ..models.media import MediaAsset
from ..repositories.conversations import ConversationRepository, MessageRepository
from ..repositories.media import MediaAssetRepository

_MEDIA_TYPES = {"audio": "audio/wav", "video": "video/mp4", "subtitle": "text/vtt"}


def _wav_meta(data: bytes) -> tuple[int | None, int | None]:
    """(duration_ms, sample_rate) parsed from a WAV payload; (None, None) if unreadable."""
    try:
        with wave.open(io.BytesIO(data)) as w:
            frames, rate = w.getnframes(), w.getframerate()
    except (wave.Error, EOFError, OSError):
        return None, None
    duration_ms = int(frames * 1000 / rate) if rate else None
    return duration_ms, rate or None


class MediaService:
    def __init__(
        self,
        media: MediaAssetRepository,
        messages: MessageRepository,
        conversations: ConversationRepository,
        workspace_dir: Path,
    ) -> None:
        self.media = media
        self.messages = messages
        self.conversations = conversations
        self.workspace_dir = workspace_dir

    async def store_message_audio(self, *, message_id: str, audio: bytes) -> MediaAsset:
        aid = new_id("media")
        key = f"media/{aid}/audio.wav"
        dest = self.workspace_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(audio)

        duration_ms, sample_rate = _wav_meta(audio)
        asset = MediaAsset(
            id=aid,
            kind="audio",
            storage_key=key,
            source_type="message",
            source_id=message_id,
            duration_ms=duration_ms,
            meta={"sample_rate": sample_rate} if sample_rate else {},
        )
        self.media.add(asset)
        await self.media.flush()
        return asset

    async def resolve_owned(self, media_id: str, user_id: str) -> tuple[Path, str]:
        """Return (path, media_type) if `user_id` owns the asset, else raise."""
        asset = await self.media.get(media_id)
        if asset is None:
            raise errors.not_found("media", media_id)

        owned = False
        if asset.source_type == "message" and asset.source_id:
            message = await self.messages.get(asset.source_id)
            conversation = (
                await self.conversations.get(message.conversation_id) if message else None
            )
            owned = conversation is not None and conversation.user_id == user_id
        if not owned:
            raise errors.forbidden(message="Not your media.")

        path = self.workspace_dir / asset.storage_key
        if not path.is_file():
            raise errors.not_found("media", media_id)
        return path, _MEDIA_TYPES.get(asset.kind, "application/octet-stream")
