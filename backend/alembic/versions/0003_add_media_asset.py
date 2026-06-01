"""add media_asset

Revision ID: 0003_media_asset
Revises: 0002_affect_state
Create Date: 2026-06-01

docs/04 §5.6, docs/11 §4.6. Produced audio/video/subtitle artifacts; P1 stores one audio
asset per synthesized chat reply, linked from message.media_asset_id.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_media_asset"
down_revision: str | None = "0002_affect_state"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "media_asset",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_media_asset_source_id", "media_asset", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_media_asset_source_id", table_name="media_asset")
    op.drop_table("media_asset")
