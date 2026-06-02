"""Application settings endpoints (docs/05 §4.7).

Runtime overrides edited in Settings. P1 exposes the global roleplay prompt; the effective
value and the system default are both returned so the UI can offer a reset.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..deps import RequireUser, SettingsSvc

router = APIRouter(prefix="/settings", tags=["settings"])


class RoleplayPromptOut(BaseModel):
    roleplay_prompt: str
    default: str


class RoleplayPromptIn(BaseModel):
    value: str = Field(max_length=8000)


@router.get("/roleplay-prompt", response_model=RoleplayPromptOut)
async def get_roleplay_prompt(_user: RequireUser, svc: SettingsSvc) -> RoleplayPromptOut:
    return RoleplayPromptOut(
        roleplay_prompt=await svc.roleplay_prompt(), default=svc.default_roleplay_prompt()
    )


@router.put("/roleplay-prompt", response_model=RoleplayPromptOut)
async def set_roleplay_prompt(
    body: RoleplayPromptIn, _user: RequireUser, svc: SettingsSvc
) -> RoleplayPromptOut:
    # A blank value clears the override (resets to the system default).
    return RoleplayPromptOut(
        roleplay_prompt=await svc.set_roleplay_prompt(body.value),
        default=svc.default_roleplay_prompt(),
    )


@router.delete("/roleplay-prompt", response_model=RoleplayPromptOut)
async def reset_roleplay_prompt(_user: RequireUser, svc: SettingsSvc) -> RoleplayPromptOut:
    return RoleplayPromptOut(
        roleplay_prompt=await svc.reset_roleplay_prompt(), default=svc.default_roleplay_prompt()
    )
