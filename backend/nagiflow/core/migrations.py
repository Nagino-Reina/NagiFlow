"""Programmatic Alembic upgrade at startup (docs/14 §6).

The app brings the DB to `head` on boot so the **migration chain is the single source
of truth** for schema — replacing the `create_all` bootstrap. Paths are resolved from the
package location, not cwd, so it works under uvicorn, the launcher, and tests alike.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from .logging import get_logger

log = get_logger("nagiflow.migrations")

# nagiflow/core/migrations.py -> nagiflow/core -> nagiflow -> backend
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


def _alembic_config() -> Config:
    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    return cfg


def run_migrations() -> None:
    """Upgrade the workspace DB to head. Synchronous (Alembic uses a sync engine)."""
    command.upgrade(_alembic_config(), "head")
    log.info("migrations applied (head)")
