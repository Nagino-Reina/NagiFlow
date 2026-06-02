"""Minimal in-process event bus (docs/03 §5, docs/06 §9).

Modules and core subscribe to lifecycle/domain events (e.g. `conversation.turn.post`,
`memory.write.pre`). This is the seam; richer veto/mutate contracts come later.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

Handler = Callable[[dict[str, Any]], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def on(self, event: str, handler: Handler) -> Callable[[], None]:
        self._handlers[event].append(handler)
        return lambda: self._handlers[event].remove(handler)

    async def emit(self, event: str, payload: dict[str, Any]) -> None:
        # Errors in a handler are isolated to that handler (docs/06 §9).
        for handler in list(self._handlers.get(event, ())):
            try:
                await handler(payload)
            except Exception:  # noqa: BLE001 - isolation by design
                import logging

                logging.getLogger("nagiflow.events").exception("event handler failed for %s", event)


event_bus = EventBus()


async def gather_emit(events: list[tuple[str, dict[str, Any]]]) -> None:
    await asyncio.gather(*(event_bus.emit(e, p) for e, p in events))
