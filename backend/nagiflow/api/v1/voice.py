"""Voice endpoints — voice models + TTS preview (docs/05 §4.1, docs/08 §4).

Creating/managing voice models is user-gated. Preview streams a complete WAV payload for
immediate playback. Capability flags let the UI hide unsupported flows (docs/06 §5.1).
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, Response, UploadFile

from ...core import errors
from ...schemas.voice import (
    TTSCapsOut,
    VoiceDesignCreate,
    VoiceModelOut,
    VoicePreviewRequest,
)
from ..deps import Registry, RequireUser, Voices

router = APIRouter(prefix="/characters", tags=["voice"])

_MAX_REFERENCE_BYTES = 20 * 1024 * 1024  # 20 MB


@router.get("/voice/capabilities", response_model=TTSCapsOut)
async def tts_capabilities(_user: RequireUser, registry: Registry) -> TTSCapsOut:
    provider = registry.get_tts()
    caps = provider.capabilities
    return TTSCapsOut(
        name=provider.name,
        streaming=caps.streaming,
        voice_clone=caps.voice_clone,
        voice_design=caps.voice_design,
        fine_tune=caps.fine_tune,
        sample_rate=caps.sample_rate,
    )


@router.get("/{character_id}/voice-models", response_model=list[VoiceModelOut])
async def list_voice_models(
    character_id: str, _user: RequireUser, svc: Voices
) -> list[VoiceModelOut]:
    models = await svc.list(character_id)
    return [VoiceModelOut.model_validate(m) for m in models]


@router.post("/{character_id}/voice-models", response_model=VoiceModelOut, status_code=201)
async def create_voice_design(
    character_id: str, body: VoiceDesignCreate, _user: RequireUser, svc: Voices
) -> VoiceModelOut:
    model = await svc.create_voice_design(character_id, description=body.design_description)
    return VoiceModelOut.model_validate(model)


@router.post("/{character_id}/voice-models:clone", response_model=VoiceModelOut, status_code=201)
async def clone_voice(
    character_id: str,
    _user: RequireUser,
    svc: Voices,
    reference: UploadFile = File(...),
    sample_text: str | None = Form(default=None),
) -> VoiceModelOut:
    data = await reference.read()
    if len(data) > _MAX_REFERENCE_BYTES:
        raise errors.AppError(
            "upload.too_large", "Reference clip exceeds 20 MB.", status_code=413,
        )
    model = await svc.create_zero_shot(character_id, reference=data, sample_text=sample_text)
    return VoiceModelOut.model_validate(model)


@router.post("/{character_id}/voice-models/{voice_model_id}:setDefault", response_model=VoiceModelOut)
async def set_default_voice(
    character_id: str, voice_model_id: str, _user: RequireUser, svc: Voices
) -> VoiceModelOut:
    model = await svc.set_default(character_id, voice_model_id)
    return VoiceModelOut.model_validate(model)


@router.delete("/{character_id}/voice-models/{voice_model_id}", status_code=204)
async def delete_voice_model(
    character_id: str, voice_model_id: str, _user: RequireUser, svc: Voices
) -> None:
    await svc.delete(character_id, voice_model_id)


@router.post("/{character_id}/voice:preview")
async def preview_voice(
    character_id: str, body: VoicePreviewRequest, _user: RequireUser, svc: Voices
) -> Response:
    audio = await svc.preview(
        character_id,
        text=body.text,
        voice_model_id=body.voice_model_id,
        style=body.style,
        speech_rate=body.speech_rate,
    )
    return Response(content=audio, media_type="audio/wav")
