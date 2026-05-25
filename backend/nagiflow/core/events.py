"""
In-process async event bus.

Provides lightweight pub/sub for coordinating WebSocket streaming
(LLM text → TTS synthesis → avatar state changes).

Usage::

    # Publisher
    await event_bus.publish("stream:anim", {"state": "talking", "expression": "default"})

    # Subscriber (async generator)
    async for payload in event_bus.subscribe("stream:anim"):
        ...
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncGenerator
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[Any]]] = defaultdict(list)

    async def publish(self, channel: str, payload: Any) -> None:
        """Broadcast *payload* to all active subscribers of *channel*."""
        for q in list(self._queues.get(channel, [])):
            await q.put(payload)

    async def subscribe(
        self, channel: str, timeout: float | None = None
    ) -> AsyncGenerator[Any, None]:
        """
        Yield payloads published to *channel*.

        The generator exits when a ``None`` sentinel is received or when
        *timeout* seconds elapse without a new event.
        """
        q: asyncio.Queue[Any] = asyncio.Queue()
        self._queues[channel].append(q)
        try:
            while True:
                try:
                    item = await asyncio.wait_for(q.get(), timeout=timeout)
                except TimeoutError:
                    break
                if item is None:
                    break
                yield item
        finally:
            try:
                self._queues[channel].remove(q)
            except ValueError:
                pass

    async def close_channel(self, channel: str) -> None:
        """Send the None sentinel to all subscribers of *channel*."""
        for q in list(self._queues.get(channel, [])):
            await q.put(None)


# Module-level singleton
event_bus = EventBus()
