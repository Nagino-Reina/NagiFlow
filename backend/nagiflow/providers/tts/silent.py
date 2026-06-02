"""Offline stub TTS (docs/06 §12 fallback, mirrors the echo LLM).

No external dependency — lets the whole voice pipeline run without a VoxCPM server. Emits a
short, soft sine tone whose length scales with the text, so playback/preview is demonstrable
end to end. Advertises clone/design so those editor flows stay testable offline.
"""

from __future__ import annotations

import array
import io
import math
import wave

from ..base import TTSCaps, VoiceRef

_SR = 24000
_FREQ = 220.0


class SilentTTS:
    name = "silent"
    model: str | None = None
    capabilities = TTSCaps(
        streaming=False, voice_clone=True, voice_design=True, fine_tune=False, sample_rate=_SR,
    )

    async def synthesize(
        self,
        *,
        text: str,
        voice: VoiceRef,
        style: str | None = None,
        speech_rate: float = 1.0,
    ) -> bytes:
        rate = max(0.5, speech_rate)
        duration = max(0.5, min(6.0, 0.06 * len(text) + 0.4)) / rate
        n = int(_SR * duration)
        fade = int(_SR * 0.05)

        def sample(i: int) -> int:
            env = min(1.0, i / fade, (n - i) / fade) if fade else 1.0
            return int(3000 * env * math.sin(2 * math.pi * _FREQ * i / _SR))

        pcm = array.array("h", (sample(i) for i in range(n)))

        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(_SR)
            w.writeframes(pcm.tobytes())
        return buf.getvalue()

    async def health(self) -> bool:
        return True
