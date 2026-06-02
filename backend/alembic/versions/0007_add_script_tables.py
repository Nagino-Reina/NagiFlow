"""add script + script_line

Revision ID: 0007_add_script
Revises: 0006_add_app_setting
Create Date: 2026-06-02

Manual script authoring (docs/04 §5.3-5.4, docs/07): an ordered set of lines with per-line
voice direction. ASR-import and render columns (timestamps, confidence) are present now and
populated by later phases.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_add_script"
down_revision: str | None = "0006_add_app_setting"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "script",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("language", sa.String(), nullable=False, server_default="en"),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("source_kind", sa.String(), nullable=False, server_default="manual"),
        sa.Column("default_character_id", sa.String(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "script_line",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "script_id",
            sa.String(),
            sa.ForeignKey("script.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.String(), nullable=True),
        sa.Column("character_name_raw", sa.String(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("start_ms", sa.Integer(), nullable=True),
        sa.Column("end_ms", sa.Integer(), nullable=True),
        sa.Column("reference_audio_key", sa.String(), nullable=True),
        sa.Column("style", sa.Text(), nullable=True),
        sa.Column("speech_rate", sa.Float(), nullable=True),
        sa.Column("pause_after_ms", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("take", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_script_line_script_id", "script_line", ["script_id"])


def downgrade() -> None:
    op.drop_index("ix_script_line_script_id", table_name="script_line")
    op.drop_table("script_line")
    op.drop_table("script")
