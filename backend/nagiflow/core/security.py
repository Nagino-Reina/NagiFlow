"""Password hashing + opaque session tokens (docs/05 §2, docs/15 §3).

- Passwords: Argon2id (memory-hard). Never stored/logged in plaintext.
- Sessions: opaque random tokens; only the SHA-256 hash is persisted.
"""

from __future__ import annotations

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(hashed: str, password: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(hashed: str) -> bool:
    return _ph.check_needs_rehash(hashed)


def generate_session_token() -> tuple[str, str]:
    """Return (clear_token, token_hash). Only the hash is stored."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
