"""Character service — CRUD + duplicate (docs/08, FR-CM-1)."""

from __future__ import annotations

from ..core import errors
from ..core.ids import new_id
from ..models.character import Character
from ..repositories.characters import CharacterRepository
from ..schemas.character import CharacterCreate, CharacterUpdate


class CharacterService:
    def __init__(self, repo: CharacterRepository) -> None:
        self.repo = repo

    async def create(self, data: CharacterCreate) -> Character:
        character = Character(
            id=new_id("c"),
            name=data.name,
            description=data.description,
            persona=data.persona,
            big_five=data.big_five.model_dump(),
            default_language=data.default_language,
            aliases=data.aliases,
            tags=data.tags,
            guest_visible=data.guest_visible,
            avatar_renderer=data.avatar_renderer,
            status="draft",
        )
        return self.repo.add(character)

    async def list(self, *, guest_visible_only: bool, cursor: str | None) -> list[Character]:
        return await self.repo.list(guest_visible_only=guest_visible_only, cursor=cursor)

    async def get(self, character_id: str, *, guest: bool) -> Character:
        character = await self.repo.get(character_id)
        if character is None or character.status == "archived":
            raise errors.not_found("character", character_id)
        if guest and not character.guest_visible:
            raise errors.not_found("character", character_id)
        return character

    async def update(self, character_id: str, data: CharacterUpdate) -> Character:
        character = await self.repo.get(character_id)
        if character is None:
            raise errors.not_found("character", character_id)
        patch = data.model_dump(exclude_unset=True)
        if "big_five" in patch and patch["big_five"] is not None:
            character.big_five = data.big_five.model_dump()
            patch.pop("big_five")
        for key, value in patch.items():
            setattr(character, key, value)
        return character

    async def archive(self, character_id: str) -> None:
        character = await self.repo.get(character_id)
        if character is None:
            raise errors.not_found("character", character_id)
        character.status = "archived"

    async def duplicate(self, character_id: str) -> Character:
        src = await self.repo.get(character_id)
        if src is None:
            raise errors.not_found("character", character_id)
        clone = Character(
            id=new_id("c"),
            name=f"{src.name} (copy)",
            description=src.description,
            persona=src.persona,
            big_five=dict(src.big_five),
            default_language=src.default_language,
            aliases=list(src.aliases),
            tags=list(src.tags),
            guest_visible=False,
            avatar_renderer=src.avatar_renderer,
            status="draft",
        )
        return self.repo.add(clone)
