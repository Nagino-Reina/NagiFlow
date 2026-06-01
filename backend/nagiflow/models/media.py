"""MediaAsset — produced audio/video/subtitle artifact (docs/04 §5.6).

P1 records one `audio` asset per synthesized chat reply (`source_type = "message"`,
`source_id = message.id`); `storage_key` is the workspace-relative path to the bytes.
Script renders (`script_render`) and video/subtitle kinds land in P2.
"""

from __future__ import annotations

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class MediaAsset(Base, TimestampMixin):
    __tablename__ = "media_asset"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # audio | video | subtitle
    storage_key: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)  # message | script_render
    source_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
