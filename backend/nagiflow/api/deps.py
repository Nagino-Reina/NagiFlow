"""FastAPI dependencies — DI for session, providers, principals, services (docs/03 §5)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..core import errors
from ..core.database import get_session
from ..providers.registry import ProviderRegistry
from ..repositories.affect import AffectStateRepository
from ..repositories.characters import CharacterRepository
from ..repositories.conversations import ConversationRepository, MessageRepository
from ..repositories.media import MediaAssetRepository
from ..repositories.scripts import ScriptLineRepository, ScriptRepository
from ..repositories.settings import SettingsRepository
from ..repositories.usage import UsageRepository
from ..repositories.users import SessionRepository, UserRepository
from ..repositories.voice_models import VoiceModelRepository
from ..services.affect import AffectService
from ..services.auth_service import AuthService, Principal
from ..services.character_service import CharacterService
from ..services.conversation_service import ConversationService
from ..services.media_service import MediaService
from ..services.script_service import ScriptService
from ..services.settings_service import SettingsService
from ..services.usage_service import UsageService
from ..services.voice_service import VoiceService

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
    return CharacterService(CharacterRepository(session), get_settings().workspace_dir)


Characters = Annotated[CharacterService, Depends(get_character_service)]


def get_media_service(session: Session) -> MediaService:
    return MediaService(
        MediaAssetRepository(session),
        MessageRepository(session),
        ConversationRepository(session),
        get_settings().workspace_dir,
    )


Media = Annotated[MediaService, Depends(get_media_service)]


def get_usage_service(session: Session) -> UsageService:
    return UsageService(UsageRepository(session))


Usage = Annotated[UsageService, Depends(get_usage_service)]


def get_settings_service(session: Session) -> SettingsService:
    return SettingsService(SettingsRepository(session))


SettingsSvc = Annotated[SettingsService, Depends(get_settings_service)]


def get_script_service(session: Session) -> ScriptService:
    return ScriptService(ScriptRepository(session), ScriptLineRepository(session))


Scripts = Annotated[ScriptService, Depends(get_script_service)]


def get_conversation_service(session: Session, registry: Registry) -> ConversationService:
    settings = get_settings()
    affect = AffectService(AffectStateRepository(session), registry, settings)
    voice = VoiceService(
        VoiceModelRepository(session),
        CharacterRepository(session),
        registry,
        settings.workspace_dir,
    )
    media = get_media_service(session)
    usage = get_usage_service(session)
    settings_svc = SettingsService(SettingsRepository(session))
    return ConversationService(
        ConversationRepository(session),
        MessageRepository(session),
        CharacterRepository(session),
        registry,
        affect,
        voice,
        media,
        usage,
        settings_svc,
        synthesize_replies=settings.synthesize_replies,
    )


Conversations = Annotated[ConversationService, Depends(get_conversation_service)]


def get_voice_service(session: Session, registry: Registry) -> VoiceService:
    return VoiceService(
        VoiceModelRepository(session),
        CharacterRepository(session),
        registry,
        get_settings().workspace_dir,
    )


Voices = Annotated[VoiceService, Depends(get_voice_service)]


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
