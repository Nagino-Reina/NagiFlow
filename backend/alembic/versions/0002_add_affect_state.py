"""add affect_state

Revision ID: 0002_affect_state
Revises: bb25bd50270f
Create Date: 2026-05-31

docs/04 §5.9, docs/10. Per character↔partner mood + last emotion (VAD + discrete label).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_affect_state"
down_revision: str | None = "bb25bd50270f"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "affect_state",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("character_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("counterpart_character_id", sa.String(), nullable=True),
        sa.Column("mood_v", sa.Float(), nullable=False, server_default="0"),
        sa.Column("mood_a", sa.Float(), nullable=False, server_default="0"),
        sa.Column("mood_d", sa.Float(), nullable=False, server_default="0"),
        sa.Column("emotion_v", sa.Float(), nullable=False, server_default="0"),
        sa.Column("emotion_a", sa.Float(), nullable=False, server_default="0"),
        sa.Column("emotion_d", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "emotion_label", sa.String(), nullable=False, server_default="neutral"
        ),
        sa.Column("emotion_intensity", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "character_id",
            "user_id",
            "counterpart_character_id",
            name="uq_affect_relationship",
        ),
    )
    op.create_index("ix_affect_state_character_id", "affect_state", ["character_id"])
    op.create_index("ix_affect_state_user_id", "affect_state", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_affect_state_user_id", table_name="affect_state")
    op.drop_index("ix_affect_state_character_id", table_name="affect_state")
    op.drop_table("affect_state")
