"""Key-value application settings (docs/05 §4.7).

Runtime overrides edited in Settings (e.g. the global roleplay prompt). One row per key; the
value falls back to a built-in default when no row exists.
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class AppSetting(Base, TimestampMixin):
    __tablename__ = "app_setting"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
