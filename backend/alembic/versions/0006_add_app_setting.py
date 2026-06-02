"""add app_setting

Revision ID: 0006_add_app_setting
Revises: 0005_drop_default_voice
Create Date: 2026-06-02

Key-value table for runtime application settings edited in Settings (docs/05 §4.7), e.g.
the global roleplay prompt.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_add_app_setting"
down_revision: str | None = "0005_drop_default_voice"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_setting",
        sa.Column("key", sa.String(), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("app_setting")
