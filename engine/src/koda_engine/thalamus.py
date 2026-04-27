from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable

from koda_engine.events import Event, EventType

Subscriber = Callable[[Event], Awaitable[None]]


class Thalamus:
    """Async pub/sub bus. Every signal between regions flows through it.

    Also broadcasts to a fan-out queue used by the WebSocket layer so the
    visualizer sees the same stream the brain sees.
    """

    def __init__(self) -> None:
        self._subs: dict[str, list[Subscriber]] = defaultdict(list)
        self._fanout: list[asyncio.Queue[Event]] = []

    def subscribe(self, event_type: EventType | str, fn: Subscriber) -> None:
        self._subs[event_type].append(fn)

    def fanout(self) -> asyncio.Queue[Event]:
        q: asyncio.Queue[Event] = asyncio.Queue(maxsize=4096)
        self._fanout.append(q)
        return q

    def drop_fanout(self, q: asyncio.Queue[Event]) -> None:
        if q in self._fanout:
            self._fanout.remove(q)

    async def publish(self, event: Event) -> None:
        for q in self._fanout:
            if not q.full():
                q.put_nowait(event)
        targets = list(self._subs.get(event.type, ())) + list(self._subs.get("*", ()))
        if not targets:
            return
        await asyncio.gather(*(fn(event) for fn in targets), return_exceptions=True)
