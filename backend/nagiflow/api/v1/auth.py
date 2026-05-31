"""Auth endpoints (docs/05 §2)."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from ...schemas.auth import LoginRequest, MeResponse, RegisterRequest, SessionResponse
from ...services.auth_service import IssuedSession
from ..deps import COOKIE_NAME, Auth, CurrentPrincipal, RequireUser

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookie(response: Response, issued: IssuedSession) -> None:
    response.set_cookie(
        COOKIE_NAME,
        issued.token,
        httponly=True,
        samesite="lax",
        secure=False,  # local dev over http; set True behind TLS (docs/15 §6)
    )


def _to_response(issued: IssuedSession) -> SessionResponse:
    return SessionResponse(
        token=issued.token,
        user_id=issued.session.user_id,
        kind=issued.session.kind,
        expires_at=issued.session.expires_at,
    )


@router.post("/guest", response_model=SessionResponse)
async def guest(auth: Auth, response: Response) -> SessionResponse:
    issued = await auth.create_guest()
    _set_cookie(response, issued)
    return _to_response(issued)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, auth: Auth) -> dict[str, str]:
    user = await auth.register(body.username, body.password, body.display_name)
    return {"id": user.id, "username": user.username or ""}


@router.post("/login", response_model=SessionResponse)
async def login(body: LoginRequest, auth: Auth, response: Response) -> SessionResponse:
    issued = await auth.login(body.username, body.password)
    _set_cookie(response, issued)
    return _to_response(issued)


@router.post("/logout")
async def logout(principal: CurrentPrincipal, auth: Auth, response: Response) -> dict[str, bool]:
    await auth.logout(principal.session_id)
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.post("/logout-all")
async def logout_all(principal: RequireUser, auth: Auth, response: Response) -> dict[str, bool]:
    await auth.logout_all(principal.user_id)
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(principal: CurrentPrincipal, auth: Auth) -> MeResponse:
    user = await auth.users.get(principal.user_id)
    return MeResponse(
        user_id=principal.user_id,
        kind=principal.kind,
        is_admin=principal.is_admin,
        username=user.username if user else None,
        display_name=user.display_name if user else None,
    )
