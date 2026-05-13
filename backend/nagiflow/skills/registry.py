"""
Global skill registry.

Skills are registered at startup (built-ins) and when plugins load (custom).
The registry provides lookups by name and can sync its state to the database.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from nagiflow.skills.base import BaseSkill, SkillMeta

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SkillRegistry:
    """Singleton registry for all available skills."""

    def __init__(self) -> None:
        self._skills: dict[str, type[BaseSkill]] = {}

    def register(self, skill_cls: type[BaseSkill]) -> type[BaseSkill]:
        """Register a skill class.  Can be used as a decorator."""
        name = skill_cls.meta.name
        if name in self._skills:
            logger.warning(f"Skill '{name}' is being overwritten.")
        self._skills[name] = skill_cls
        logger.debug(f"Registered skill: '{name}'")
        return skill_cls

    def get(self, name: str) -> type[BaseSkill] | None:
        return self._skills.get(name)

    def get_or_raise(self, name: str) -> type[BaseSkill]:
        cls = self.get(name)
        if cls is None:
            raise KeyError(f"Skill '{name}' is not registered.")
        return cls

    def all(self) -> list[type[BaseSkill]]:
        return list(self._skills.values())

    def instantiate(
        self, name: str, config: dict | None = None
    ) -> BaseSkill:
        cls = self.get_or_raise(name)
        return cls(config=config)

    def instantiate_for_character(
        self, skill_names: list[str], configs: dict[str, dict] | None = None
    ) -> list[BaseSkill]:
        """Return instantiated skill objects for the given names and configs."""
        configs = configs or {}
        result: list[BaseSkill] = []
        for name in skill_names:
            cls = self.get(name)
            if cls is None:
                logger.warning(f"Skill '{name}' not found in registry; skipping.")
                continue
            result.append(cls(config=configs.get(name)))
        return result

    async def sync_to_db(self, db: "AsyncSession") -> None:
        """
        Upsert all registered built-in skills into the database.

        Called at application startup so the DB always reflects the current
        set of available skills.
        """
        from sqlalchemy import select

        from nagiflow.models.skill import Skill

        for skill_cls in self._skills.values():
            meta: SkillMeta = skill_cls.meta
            stmt = select(Skill).where(Skill.name == meta.name)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing is None:
                db.add(Skill(**meta.to_db_dict()))
                logger.info(f"Inserted skill '{meta.name}' into database.")
            else:
                for k, v in meta.to_db_dict().items():
                    setattr(existing, k, v)

        await db.commit()
        logger.info(f"Synced {len(self._skills)} skills to database.")


# Module-level singleton
skill_registry = SkillRegistry()
