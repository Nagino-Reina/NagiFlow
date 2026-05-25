"""
WebSocket streaming endpoints.

Provides two streaming modes:

1. ``/ws/stream/text`` — streams LLM text deltas as JSON frames.
2. ``/ws/stream/audio`` — streams LLM + TTS pipeline, yielding raw WAV audio
   chunks that the client can feed to the Web Audio API or a media player.

Protocol (client → server):
    JSON object sent as a single text message:
    {
        "token":          "<JWT access token>",
        "character_id":   "<UUID>",
        "conversation_id": "<UUID or null>",
        "message":        "Hello!"
    }

Protocol (server → client, text stream):
    Each server message is a JSON text frame:
    { "type": "delta",      "content": "..." }
    { "type": "anim_state", "state": "talking"|"idle"|"blinking", "expression": "..." }
    { "type": "done",       "conversation_id": "..." }
    { "type": "error",      "detail": "..." }

Protocol (server → client, audio stream):
    { "type": "anim_state", "state": "talking", "expression": "..." }  — before audio
    Binary frames containing raw WAV audio data
    { "type": "anim_state", "state": "idle", "expression": "default" } — after audio
    { "type": "done" }
"""

import json
import re
from uuid import UUID

_EMOTION_RE = re.compile(r"\[(\w+)\]")
_KNOWN_EXPRESSIONS = {"happy", "sad", "angry", "surprised", "default"}


def _extract_expression(text: str) -> str:
    """Return the last emotion tag found in *text*, or 'default'."""
    matches = _EMOTION_RE.findall(text)
    for m in reversed(matches):
        if m.lower() in _KNOWN_EXPRESSIONS:
            return m.lower()
    return "default"

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.core.database import get_session
from nagiflow.core.exceptions import NagiFlowError
from nagiflow.core.security import decode_access_token
from nagiflow.services.auth import AuthService
from nagiflow.services.conversation import ConversationService

router = APIRouter(prefix="/ws", tags=["Streaming (WebSocket)"])


async def _authenticate_ws(
    websocket: WebSocket,
    db: AsyncSession,
) -> "tuple[UUID, dict]":
    """
    Read the first text message from the WebSocket, validate the JWT,
    and return (user_id, payload_dict).
    """
    raw = await websocket.receive_text()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid JSON."}))
        await websocket.close(code=1003)
        raise ValueError("Invalid JSON payload.")

    token = payload.get("token")
    if not token:
        await websocket.send_text(json.dumps({"type": "error", "detail": "Missing token."}))
        await websocket.close(code=1008)
        raise ValueError("Missing token.")

    try:
        jwt_payload = decode_access_token(token)
    except NagiFlowError as exc:
        await websocket.send_text(json.dumps({"type": "error", "detail": exc.detail}))
        await websocket.close(code=1008)
        raise

    user_id = UUID(jwt_payload["sub"])
    auth_svc = AuthService(db)
    user = await auth_svc.get_user(user_id)
    if not user.is_active:
        await websocket.send_text(json.dumps({"type": "error", "detail": "Account inactive."}))
        await websocket.close(code=1008)
        raise ValueError("Inactive account.")

    return user_id, payload


@router.websocket("/stream/text")
async def stream_text(websocket: WebSocket) -> None:
    """
    Stream LLM text deltas in real time.

    The client sends a single JSON authentication + request message and
    receives a sequence of JSON delta frames followed by a ``done`` frame.
    """
    await websocket.accept()

    # Obtain a dedicated DB session for this WS connection lifetime
    session_gen = get_session()
    db: AsyncSession = await session_gen.__anext__()

    try:
        user_id, payload = await _authenticate_ws(websocket, db)
    except Exception:
        return

    character_id_str = payload.get("character_id")
    conversation_id_str = payload.get("conversation_id")
    message = payload.get("message", "").strip()

    if not character_id_str or not message:
        await websocket.send_text(
            json.dumps({"type": "error", "detail": "character_id and message are required."})
        )
        await websocket.close(code=1003)
        return

    try:
        character_id = UUID(character_id_str)
        conversation_id = UUID(conversation_id_str) if conversation_id_str else None
    except ValueError:
        await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid UUID."}))
        await websocket.close(code=1003)
        return

    svc = ConversationService(db)
    last_conv_id: UUID | None = None
    current_expression = "default"

    try:
        async for chunk, conv_id in svc.stream_chat(
            conversation_id=conversation_id,
            user_id=user_id,
            character_id=character_id,
            user_message=message,
        ):
            if conv_id is not None:
                last_conv_id = conv_id
            await websocket.send_text(json.dumps({"type": "delta", "content": chunk}))
            # Detect emotion tags and emit anim_state
            expr = _extract_expression(chunk)
            if expr != "default" and expr != current_expression:
                current_expression = expr
                await websocket.send_text(
                    json.dumps({"type": "anim_state", "state": "talking", "expression": expr})
                )

        await db.commit()
        await websocket.send_text(
            json.dumps({"type": "done", "conversation_id": str(last_conv_id)})
        )
    except NagiFlowError as exc:
        await db.rollback()
        await websocket.send_text(json.dumps({"type": "error", "detail": exc.detail}))
    except WebSocketDisconnect:
        await db.rollback()
        logger.info(f"WS text stream disconnected (user={user_id})")
    except Exception as exc:
        await db.rollback()
        logger.error(f"WS text stream error: {exc}", exc_info=True)
        await websocket.send_text(json.dumps({"type": "error", "detail": "Internal error."}))
    finally:
        await db.close()
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/stream/audio")
async def stream_audio(websocket: WebSocket) -> None:
    """
    Concurrent LLM + TTS streaming.

    Binary WAV audio chunks are sent as binary WebSocket frames as each
    sentence is synthesised.  A final JSON text frame signals completion.
    """
    await websocket.accept()

    session_gen = get_session()
    db: AsyncSession = await session_gen.__anext__()

    try:
        user_id, payload = await _authenticate_ws(websocket, db)
    except Exception:
        return

    character_id_str = payload.get("character_id")
    conversation_id_str = payload.get("conversation_id")
    message = payload.get("message", "").strip()

    if not character_id_str or not message:
        await websocket.send_text(
            json.dumps({"type": "error", "detail": "character_id and message are required."})
        )
        await websocket.close(code=1003)
        return

    try:
        character_id = UUID(character_id_str)
        conversation_id = UUID(conversation_id_str) if conversation_id_str else None
    except ValueError:
        await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid UUID."}))
        await websocket.close(code=1003)
        return

    svc = ConversationService(db)

    try:
        first_audio = True
        async for audio_chunk in svc.stream_tts_with_llm(
            conversation_id=conversation_id,
            user_id=user_id,
            character_id=character_id,
            user_message=message,
        ):
            if first_audio:
                await websocket.send_text(
                    json.dumps({"type": "anim_state", "state": "talking", "expression": "default"})
                )
                first_audio = False
            await websocket.send_bytes(audio_chunk)

        await websocket.send_text(
            json.dumps({"type": "anim_state", "state": "idle", "expression": "default"})
        )
        await db.commit()
        await websocket.send_text(json.dumps({"type": "done"}))
    except NagiFlowError as exc:
        await db.rollback()
        await websocket.send_text(json.dumps({"type": "error", "detail": exc.detail}))
    except WebSocketDisconnect:
        await db.rollback()
        logger.info(f"WS audio stream disconnected (user={user_id})")
    except Exception as exc:
        await db.rollback()
        logger.error(f"WS audio stream error: {exc}", exc_info=True)
        await websocket.send_text(json.dumps({"type": "error", "detail": "Internal error."}))
    finally:
        await db.close()
        try:
            await websocket.close()
        except Exception:
            pass
