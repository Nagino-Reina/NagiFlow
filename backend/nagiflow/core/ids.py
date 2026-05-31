"""Opaque, URL-safe, time-sortable IDs (docs/04 §2 — ULID-style).

`new_id("c")` -> "c_01HX3...": a prefix + 26-char Crockford base32 of a 48-bit
millisecond timestamp followed by 80 bits of randomness. Lexicographically sortable
by creation time, collision-resistant, no external dependency.
"""

from __future__ import annotations

import os
import time

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode(value: int, length: int) -> str:
    out = []
    for _ in range(length):
        value, rem = divmod(value, 32)
        out.append(_CROCKFORD[rem])
    return "".join(reversed(out))


def _ulid() -> str:
    ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand = int.from_bytes(os.urandom(10), "big")  # 80 bits
    return _encode(ts_ms, 10) + _encode(rand, 16)


def new_id(prefix: str) -> str:
    """Return a prefixed ULID, e.g. `new_id("c")` -> 'c_01HX...'."""
    return f"{prefix}_{_ulid()}"
