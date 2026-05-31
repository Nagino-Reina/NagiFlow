"""Shared schema helpers (docs/05 §1)."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Cursor-paginated list response (docs/05 §1)."""

    items: list[T]
    next_cursor: str | None = None
