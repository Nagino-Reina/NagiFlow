"""Script endpoints (docs/05 §4.2, docs/07). User-only — guests cannot author scripts."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from ...core import errors
from ...schemas.script import (
    ReorderIn,
    ScriptCreate,
    ScriptLineCreate,
    ScriptLineOut,
    ScriptLineUpdate,
    ScriptOut,
    ScriptUpdate,
    ValidationOut,
)
from ..deps import Characters, RequireUser, Scripts, Voices

router = APIRouter(prefix="/scripts", tags=["scripts"])


async def _out(svc: Scripts, script) -> ScriptOut:  # noqa: ANN001 - ORM model
    out = ScriptOut.model_validate(script)
    out.line_count = await svc.line_count(script.id)
    return out


@router.get("", response_model=list[ScriptOut])
async def list_scripts(_user: RequireUser, svc: Scripts) -> list[ScriptOut]:
    return [await _out(svc, s) for s in await svc.list()]


@router.post("", response_model=ScriptOut, status_code=status.HTTP_201_CREATED)
async def create_script(body: ScriptCreate, _user: RequireUser, svc: Scripts) -> ScriptOut:
    return await _out(svc, await svc.create(body))


@router.get("/{script_id}:validate", response_model=ValidationOut)
async def validate_script(script_id: str, _user: RequireUser, svc: Scripts) -> ValidationOut:
    return ValidationOut(issues=await svc.validate(script_id))


@router.get("/{script_id}", response_model=ScriptOut)
async def get_script(script_id: str, _user: RequireUser, svc: Scripts) -> ScriptOut:
    return await _out(svc, await svc.get(script_id))


@router.patch("/{script_id}", response_model=ScriptOut)
async def update_script(
    script_id: str, body: ScriptUpdate, _user: RequireUser, svc: Scripts
) -> ScriptOut:
    return await _out(svc, await svc.update(script_id, body))


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(script_id: str, _user: RequireUser, svc: Scripts) -> None:
    await svc.archive(script_id)


@router.post("/{script_id}:duplicate", response_model=ScriptOut)
async def duplicate_script(script_id: str, _user: RequireUser, svc: Scripts) -> ScriptOut:
    return await _out(svc, await svc.duplicate(script_id))


# --- lines ---


@router.get("/{script_id}/lines", response_model=list[ScriptLineOut])
async def list_lines(script_id: str, _user: RequireUser, svc: Scripts) -> list[ScriptLineOut]:
    return [ScriptLineOut.model_validate(line) for line in await svc.lines_for(script_id)]


@router.post(
    "/{script_id}/lines", response_model=ScriptLineOut, status_code=status.HTTP_201_CREATED
)
async def add_line(
    script_id: str, body: ScriptLineCreate, _user: RequireUser, svc: Scripts
) -> ScriptLineOut:
    return ScriptLineOut.model_validate(await svc.add_line(script_id, body))


@router.patch("/{script_id}/lines/{line_id}", response_model=ScriptLineOut)
async def update_line(
    script_id: str, line_id: str, body: ScriptLineUpdate, _user: RequireUser, svc: Scripts
) -> ScriptLineOut:
    return ScriptLineOut.model_validate(await svc.update_line(script_id, line_id, body))


@router.delete("/{script_id}/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_line(script_id: str, line_id: str, _user: RequireUser, svc: Scripts) -> None:
    await svc.delete_line(script_id, line_id)


@router.post("/{script_id}/lines:reorder", response_model=list[ScriptLineOut])
async def reorder_lines(
    script_id: str, body: ReorderIn, _user: RequireUser, svc: Scripts
) -> list[ScriptLineOut]:
    lines = await svc.reorder(script_id, body.line_ids)
    return [ScriptLineOut.model_validate(line) for line in lines]


@router.post("/{script_id}/lines/{line_id}:preview")
async def preview_line(
    script_id: str,
    line_id: str,
    _user: RequireUser,
    svc: Scripts,
    characters: Characters,
    voices: Voices,
) -> Response:
    """Synthesize a single line with its speaker's voice + personality (docs/07 §3.2, FR-SM-8)."""
    line = await svc.get_line(script_id, line_id)
    if not line.character_id:
        raise errors.AppError(
            "script.no_speaker", "Assign a speaker before generating audio.", status_code=422
        )
    character = await characters.get(line.character_id, guest=False)
    audio = await voices.synthesize_line(
        character, text=line.text, line_style=line.style, line_speech_rate=line.speech_rate
    )
    return Response(content=audio, media_type="audio/wav")
