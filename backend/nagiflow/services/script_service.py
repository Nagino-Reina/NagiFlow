"""Script service — manual authoring: CRUD, duplicate, line ops, reorder, validate (FR-SM-1/2/3/4)."""

from __future__ import annotations

from ..core import errors
from ..core.ids import new_id
from ..models.script import Script, ScriptLine
from ..repositories.scripts import ScriptLineRepository, ScriptRepository
from ..schemas.script import (
    ScriptCreate,
    ScriptLineCreate,
    ScriptLineUpdate,
    ScriptUpdate,
    ValidationIssue,
)

_LINE_COPY_FIELDS = (
    "character_id",
    "character_name_raw",
    "text",
    "start_ms",
    "end_ms",
    "reference_audio_key",
    "style",
    "speech_rate",
    "pause_after_ms",
    "language",
    "notes",
    "take",
    "confidence",
)


class ScriptService:
    def __init__(self, scripts: ScriptRepository, lines: ScriptLineRepository) -> None:
        self.scripts = scripts
        self.lines = lines

    # --- script ---

    async def create(self, data: ScriptCreate) -> Script:
        script = Script(
            id=new_id("scr"),
            title=data.title,
            description=data.description,
            language=data.language,
            default_character_id=data.default_character_id,
            source_kind="manual",
            status="draft",
        )
        self.scripts.add(script)
        await self.scripts.flush()
        return script

    async def list(self) -> list[Script]:
        return await self.scripts.list()

    async def get(self, script_id: str) -> Script:
        script = await self.scripts.get(script_id)
        if script is None or script.status == "archived":
            raise errors.not_found("script", script_id)
        return script

    async def line_count(self, script_id: str) -> int:
        return await self.scripts.line_count(script_id)

    async def update(self, script_id: str, data: ScriptUpdate) -> Script:
        script = await self.get(script_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(script, key, value)
        await self.scripts.flush()
        return script

    async def archive(self, script_id: str) -> None:
        script = await self.get(script_id)
        script.status = "archived"
        await self.scripts.flush()

    async def duplicate(self, script_id: str) -> Script:
        src = await self.get(script_id)
        clone = Script(
            id=new_id("scr"),
            title=f"{src.title} (copy)",
            description=src.description,
            language=src.language,
            default_character_id=src.default_character_id,
            source_kind="manual",
            status="draft",
        )
        self.scripts.add(clone)
        for line in await self.lines.list_for_script(src.id):
            copy = ScriptLine(
                id=new_id("sl"),
                script_id=clone.id,
                order_index=line.order_index,
                **{f: getattr(line, f) for f in _LINE_COPY_FIELDS},
            )
            self.lines.add(copy)
        await self.scripts.flush()
        return clone

    # --- lines ---

    async def lines_for(self, script_id: str) -> list[ScriptLine]:
        await self.get(script_id)
        return await self.lines.list_for_script(script_id)

    async def add_line(self, script_id: str, data: ScriptLineCreate) -> ScriptLine:
        await self.get(script_id)
        line = ScriptLine(
            id=new_id("sl"),
            script_id=script_id,
            order_index=await self.lines.next_order_index(script_id),
            **data.model_dump(),
        )
        self.lines.add(line)
        await self.lines.flush()
        return line

    async def _owned_line(self, script_id: str, line_id: str) -> ScriptLine:
        line = await self.lines.get(line_id)
        if line is None or line.script_id != script_id:
            raise errors.not_found("script_line", line_id)
        return line

    async def get_line(self, script_id: str, line_id: str) -> ScriptLine:
        await self.get(script_id)
        return await self._owned_line(script_id, line_id)

    async def update_line(self, script_id: str, line_id: str, data: ScriptLineUpdate) -> ScriptLine:
        await self.get(script_id)
        line = await self._owned_line(script_id, line_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(line, key, value)
        await self.lines.flush()
        return line

    async def delete_line(self, script_id: str, line_id: str) -> None:
        await self.get(script_id)
        line = await self._owned_line(script_id, line_id)
        await self.lines.delete(line)
        await self.lines.flush()

    async def reorder(self, script_id: str, line_ids: list[str]) -> list[ScriptLine]:
        await self.get(script_id)
        current = await self.lines.list_for_script(script_id)
        by_id = {line.id: line for line in current}
        if set(line_ids) != set(by_id):
            raise errors.AppError(
                "script.reorder_mismatch",
                "Reorder must list exactly the script's current line ids.",
                status_code=422,
            )
        for index, line_id in enumerate(line_ids):
            by_id[line_id].order_index = index
        await self.lines.flush()
        return await self.lines.list_for_script(script_id)

    async def validate(self, script_id: str) -> list[ValidationIssue]:
        """Author-side checks (docs/07 §8); provider/voice checks run at render time."""
        await self.get(script_id)
        lines = await self.lines.list_for_script(script_id)
        issues: list[ValidationIssue] = []
        if not lines:
            issues.append(
                ValidationIssue(
                    severity="warning", code="empty_script", message="Script has no lines."
                )
            )
        last_end_by_speaker: dict[str, int] = {}
        for line in lines:
            if not line.text.strip():
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="empty_text",
                        message="Line has no text.",
                        line_id=line.id,
                    )
                )
            if not line.character_id and not line.character_name_raw:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="no_speaker",
                        message="Line has no assigned speaker.",
                        line_id=line.id,
                    )
                )
            if (
                line.start_ms is not None
                and line.end_ms is not None
                and line.start_ms > line.end_ms
            ):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="bad_timing",
                        message="Line start is after its end.",
                        line_id=line.id,
                    )
                )
            # Same-speaker overlap is a warning (cross-speaker overlap is allowed, docs/07 §8).
            if line.character_id and line.start_ms is not None and line.end_ms is not None:
                prev_end = last_end_by_speaker.get(line.character_id)
                if prev_end is not None and line.start_ms < prev_end:
                    issues.append(
                        ValidationIssue(
                            severity="warning",
                            code="speaker_overlap",
                            message="Overlaps a previous line from the same speaker.",
                            line_id=line.id,
                        )
                    )
                last_end_by_speaker[line.character_id] = line.end_ms
        return issues
