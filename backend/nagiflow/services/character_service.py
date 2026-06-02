"""Character service — CRUD + duplicate + portrait (docs/08, FR-CM-1/2)."""

from __future__ import annotations

from pathlib import Path

from ..core import errors
from ..core.ids import new_id
from ..models.character import Character
from ..repositories.characters import CharacterRepository
from ..schemas.character import CharacterCreate, CharacterUpdate

# Accepted portrait image types → stored file extension (docs/04 §5.2, FR-CM-2).
_PORTRAIT_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
_PORTRAIT_TYPES_INV = {ext: ct for ct, ext in _PORTRAIT_TYPES.items()}


class CharacterService:
    def __init__(self, repo: CharacterRepository, workspace_dir: Path) -> None:
        self.repo = repo
        self.workspace_dir = workspace_dir

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
        self.repo.add(character)
        await self.repo.flush()
        return character

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
        await self.repo.flush()
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
        self.repo.add(clone)
        await self.repo.flush()
        return clone

    async def set_portrait(self, character_id: str, *, data: bytes, content_type: str) -> Character:
        ext = _PORTRAIT_TYPES.get(content_type)
        if ext is None:
            raise errors.AppError(
                "media.unsupported_type",
                f"Unsupported portrait type: {content_type or 'unknown'}.",
                status_code=415,
            )
        character = await self.repo.get(character_id)
        if character is None:
            raise errors.not_found("character", character_id)

        old_key = character.portrait_key
        key = f"characters/{character_id}/portrait.{ext}"
        dest = self.workspace_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        # A different source type changes the extension; drop the stale file.
        if old_key and old_key != key:
            (self.workspace_dir / old_key).unlink(missing_ok=True)

        character.portrait_key = key
        await self.repo.flush()
        return character

    async def clear_portrait(self, character_id: str) -> None:
        character = await self.repo.get(character_id)
        if character is None:
            raise errors.not_found("character", character_id)
        if character.portrait_key:
            (self.workspace_dir / character.portrait_key).unlink(missing_ok=True)
            character.portrait_key = None
            await self.repo.flush()

    async def portrait_file(self, character_id: str, *, guest: bool) -> tuple[Path, str]:
        """Return (path, media_type) for the character's portrait, honoring guest visibility."""
        character = await self.get(character_id, guest=guest)
        if not character.portrait_key:
            raise errors.not_found("portrait", character_id)
        path = self.workspace_dir / character.portrait_key
        if not path.is_file():
            raise errors.not_found("portrait", character_id)
        media_type = _PORTRAIT_TYPES_INV.get(path.suffix.lstrip("."), "application/octet-stream")
        return path, media_type
