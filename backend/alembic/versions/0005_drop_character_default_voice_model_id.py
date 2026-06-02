"""drop character.default_voice_model_id

Revision ID: 0005_drop_default_voice
Revises: 0004_usage_record
Create Date: 2026-06-01

The default voice is tracked solely by voice_model.is_default; the redundant
character.default_voice_model_id pointer was never read or written (docs/04 §5.2).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_drop_default_voice"
down_revision: str | None = "0004_usage_record"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # SQLite requires batch mode to drop a column.
    with op.batch_alter_table("character") as batch:
        batch.drop_column("default_voice_model_id")


def downgrade() -> None:
    with op.batch_alter_table("character") as batch:
        batch.add_column(sa.Column("default_voice_model_id", sa.String(), nullable=True))
