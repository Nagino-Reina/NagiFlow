"""FastAPI dependencies — DI for session, providers, principals, services (docs/03 §5)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import errors
from ..core.database import get_session
from ..providers.registry import ProviderRegistry
from ..repositories.characters import CharacterRepository
from ..repositories.conversations import ConversationRepository, MessageRepository
from ..repositories.users import SessionRepository, UserRepository
from ..services.auth_service import AuthService, Principal
from ..services.character_service import CharacterService
from ..services.conversation_service import ConversationService

COOKIE_NAME = "nf_session"


async def db_session() -> AsyncIterator[AsyncSession]:
    async for s in get_session():
        yield s


Session = Annotated[AsyncSession, Depends(db_session)]


def get_registry(request: Request) -> ProviderRegistry:
    return request.app.state.registry


Registry = Annotated[ProviderRegistry, Depends(get_registry)]


def get_auth_service(session: Session) -> AuthService:
    return AuthService(UserRepository(session), SessionRepository(session))


Auth = Annotated[AuthService, Depends(get_auth_service)]


def get_character_service(session: Session) -> CharacterService:
    return CharacterService(CharacterRepository(session))


Characters = Annotated[CharacterService, Depends(get_character_service)]


def get_conversation_service(session: Session, registry: Registry) -> ConversationService:
    return ConversationService(
        ConversationRepository(session),
        MessageRepository(session),
        CharacterRepository(session),
        registry,
    )


Conversations = Annotated[ConversationService, Depends(get_conversation_service)]


def _extract_token(request: Request) -> str | None:
    header = request.headers.get("Authorization")
    if header and header.lower().startswith("bearer "):
        return header[7:].strip()
    return request.cookies.get(COOKIE_NAME)


async def current_principal(request: Request, auth: Auth) -> Principal:
    """Require any valid session (guest or user). Issue a guest session via POST /auth/guest."""
    token = _extract_token(request)
    if not token:
        raise errors.auth_required()
    principal = await auth.resolve(token)
    if principal is None:
        raise errors.auth_required()
    return principal


CurrentPrincipal = Annotated[Principal, Depends(current_principal)]


async def require_user(principal: CurrentPrincipal) -> Principal:
    """Gate advanced operations to authenticated (non-guest) users (docs/09 §3)."""
    if principal.kind != "user":
        raise errors.guest_upgrade_required()
    return principal


RequireUser = Annotated[Principal, Depends(require_user)]
