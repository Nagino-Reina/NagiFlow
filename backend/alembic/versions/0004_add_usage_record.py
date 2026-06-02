"""add usage_record

Revision ID: 0004_usage_record
Revises: 0003_media_asset
Create Date: 2026-06-01

docs/04 §5, docs/12 §3. Per-call token/audio accounting for FR-OBS-3 totals + breakdowns.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_usage_record"
down_revision: str | None = "0003_media_asset"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usage_record",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("character_id", sa.String(), nullable=True),
        sa.Column("conversation_id", sa.String(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("audio_seconds", sa.Float(), nullable=True),
        sa.Column("est_cost", sa.Float(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("correlation_id", sa.String(), nullable=True),
    )
    op.create_index("ix_usage_record_user_id", "usage_record", ["user_id"])
    op.create_index("ix_usage_record_character_id", "usage_record", ["character_id"])
    op.create_index("ix_usage_record_occurred_at", "usage_record", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_usage_record_occurred_at", table_name="usage_record")
    op.drop_index("ix_usage_record_character_id", table_name="usage_record")
    op.drop_index("ix_usage_record_user_id", table_name="usage_record")
    op.drop_table("usage_record")
