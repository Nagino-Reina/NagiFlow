"""Character endpoints (docs/05 §4.1).

Guests may list/read only guest-visible characters; create/edit/delete are user-gated.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from ...schemas.character import (
    CharacterCreate,
    CharacterOut,
    CharacterUpdate,
    PersonalitySchemaOut,
)
from ...schemas.common import Page
from ...services import personality
from ..deps import Characters, CurrentPrincipal, RequireUser

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("/personality/schema", response_model=PersonalitySchemaOut)
async def personality_schema(_user: RequireUser) -> PersonalitySchemaOut:
    """The Big Five → behavior mapping spec. Fetched once; the client computes the
    per-profile explainability view locally (no per-edit round-trips)."""
    return PersonalitySchemaOut.model_validate(personality.spec())


@router.get("", response_model=Page[CharacterOut])
async def list_characters(
    principal: CurrentPrincipal, svc: Characters, cursor: str | None = None
) -> Page[CharacterOut]:
    guest_only = principal.kind != "user"
    items = await svc.list(guest_visible_only=guest_only, cursor=cursor)
    next_cursor = items[-1].id if len(items) == 50 else None
    return Page(items=[CharacterOut.model_validate(c) for c in items], next_cursor=next_cursor)


@router.post("", response_model=CharacterOut, status_code=status.HTTP_201_CREATED)
async def create_character(
    body: CharacterCreate, _user: RequireUser, svc: Characters
) -> CharacterOut:
    character = await svc.create(body)
    return CharacterOut.model_validate(character)


@router.get("/{character_id}", response_model=CharacterOut)
async def get_character(
    character_id: str, principal: CurrentPrincipal, svc: Characters
) -> CharacterOut:
    character = await svc.get(character_id, guest=principal.kind != "user")
    return CharacterOut.model_validate(character)


@router.patch("/{character_id}", response_model=CharacterOut)
async def update_character(
    character_id: str, body: CharacterUpdate, _user: RequireUser, svc: Characters
) -> CharacterOut:
    character = await svc.update(character_id, body)
    return CharacterOut.model_validate(character)


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(character_id: str, _user: RequireUser, svc: Characters) -> None:
    await svc.archive(character_id)


@router.post("/{character_id}:duplicate", response_model=CharacterOut)
async def duplicate_character(
    character_id: str, _user: RequireUser, svc: Characters
) -> CharacterOut:
    character = await svc.duplicate(character_id)
    return CharacterOut.model_validate(character)
