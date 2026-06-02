"""Unit tests for the offline stub TTS (docs/06 §12, docs/14 §6)."""

from __future__ import annotations

import io
import wave

from nagiflow.providers.base import VoiceRef
from nagiflow.providers.tts.silent import SilentTTS


def _frames(payload: bytes) -> int:
    with wave.open(io.BytesIO(payload), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 24000
        return w.getnframes()


async def test_returns_a_valid_wav() -> None:
    payload = await SilentTTS().synthesize(text="hello world", voice=VoiceRef())
    assert payload[:4] == b"RIFF"
    assert payload[8:12] == b"WAVE"
    assert _frames(payload) > 0


async def test_length_scales_with_text() -> None:
    tts = SilentTTS()
    short = await tts.synthesize(text="hi", voice=VoiceRef())
    long = await tts.synthesize(text="hi " * 40, voice=VoiceRef())
    assert _frames(long) > _frames(short)


async def test_faster_speech_rate_shortens_output() -> None:
    tts = SilentTTS()
    base = await tts.synthesize(text="a steady sentence here", voice=VoiceRef(), speech_rate=1.0)
    fast = await tts.synthesize(text="a steady sentence here", voice=VoiceRef(), speech_rate=2.0)
    assert _frames(fast) < _frames(base)


def test_capabilities_advertise_clone_and_design() -> None:
    caps = SilentTTS().capabilities
    assert caps.voice_clone and caps.voice_design
    assert not caps.fine_tune
