"""Authentication & session service (docs/05 §2, docs/09 §2, docs/16 §3).

Opaque hashed session tokens, Argon2id passwords, no silent account creation.
Returns the clear token only at issue time; only the hash is persisted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ..config import get_settings
from ..core import errors, security
from ..core.ids import new_id
from ..models.user import Session, User
from ..repositories.users import SessionRepository, UserRepository


@dataclass
class Principal:
    user_id: str
    kind: str  # guest | user
    is_admin: bool
    session_id: str


@dataclass
class IssuedSession:
    token: str
    session: Session


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Only persist last_seen_at when it is this stale, so frequent polling (e.g. the system
# status bar) does not write to the DB on every request and contend for the SQLite writer.
_TOUCH_INTERVAL = timedelta(seconds=60)


class AuthService:
    def __init__(self, users: UserRepository, sessions: SessionRepository) -> None:
        self.users = users
        self.sessions = sessions

    async def create_guest(self) -> IssuedSession:
        settings = get_settings()
        user = User(id=new_id("u"), kind="guest", status="active")
        self.users.add(user)
        return self._issue(user, kind="guest", ttl=settings.guest_ttl)

    async def register(self, username: str, password: str, display_name: str | None) -> User:
        existing = await self.users.get_by_username(username)
        if existing is not None:
            raise errors.conflict("auth.username_taken", "Username already taken.")
        user = User(
            id=new_id("u"),
            kind="local",
            username=username,
            password_hash=security.hash_password(password),
            display_name=display_name or username,
            status="active",
        )
        self.users.add(user)
        return user

    async def login(self, username: str, password: str) -> IssuedSession:
        user = await self.users.get_by_username(username)
        if user is None or not user.password_hash:
            raise errors.AppError(
                "auth.invalid_credentials", "Invalid username or password.", status_code=401
            )
        if not security.verify_password(user.password_hash, password):
            raise errors.AppError(
                "auth.invalid_credentials", "Invalid username or password.", status_code=401
            )
        settings = get_settings()
        return self._issue(user, kind="user", ttl=settings.session_ttl)

    async def resolve(self, token: str) -> Principal | None:
        token_hash = security.hash_token(token)
        session = await self.sessions.get_by_token_hash(token_hash)
        if session is None:
            return None
        if _aware(session.expires_at) < _now():
            return None
        user = await self.users.get(session.user_id)
        if user is None or user.status != "active":
            return None
        now = _now()
        if session.last_seen_at is None or _aware(session.last_seen_at) < now - _TOUCH_INTERVAL:
            await self.sessions.touch(session, now)
        return Principal(
            user_id=user.id, kind=session.kind, is_admin=user.is_admin, session_id=session.id
        )

    async def logout(self, session_id: str) -> None:
        await self.sessions.delete_by_id(session_id)

    async def logout_all(self, user_id: str) -> None:
        await self.sessions.delete_for_user(user_id)

    def _issue(self, user: User, *, kind: str, ttl: int) -> IssuedSession:
        token, token_hash = security.generate_session_token()
        session = Session(
            id=new_id("s"),
            user_id=user.id,
            token_hash=token_hash,
            kind=kind,
            expires_at=_now() + timedelta(seconds=ttl),
            last_seen_at=_now(),
        )
        self.sessions.add(session)
        return IssuedSession(token=token, session=session)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
