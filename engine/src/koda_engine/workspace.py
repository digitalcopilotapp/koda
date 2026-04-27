from __future__ import annotations

import time
from dataclasses import dataclass, field

from koda_engine.events import Event
from koda_engine.thalamus import Thalamus


@dataclass
class WorkspaceItem:
    content: str
    intensity: float
    source: str  # neuron id or region
    t: float = field(default_factory=time.time)


class Workspace:
    """Global workspace: a tiny buffer where the strongest patterns surface
    and become 'conscious'. Only items here can be spoken by Broca."""

    def __init__(self, thalamus: Thalamus, capacity: int = 4, threshold: float = 0.55) -> None:
        self.thalamus = thalamus
        self.capacity = capacity
        self.threshold = threshold
        self.items: list[WorkspaceItem] = []
        self.user_turn: str = ""
        thalamus.subscribe("neuron.fire", self._on_fire)

    def has_content(self) -> bool:
        return bool(self.items)

    def snapshot(self) -> list[str]:
        return [i.content for i in self.items if i.content]

    def clear(self) -> None:
        self.items = []

    async def _on_fire(self, ev: Event) -> None:
        intensity = ev.payload.get("intensity", 0.0)
        if intensity < self.threshold:
            return
        concept = ev.payload.get("concept") or ""
        if not concept:
            return
        # cooldown: avoid the same concept hammering the workspace
        for it in self.items:
            if it.content == concept:
                it.intensity = max(it.intensity, intensity)
                return
        item = WorkspaceItem(content=concept, intensity=intensity, source=ev.payload.get("id", ""))
        self.items.append(item)
        # prune to capacity, keeping strongest
        self.items.sort(key=lambda i: i.intensity, reverse=True)
        self.items = self.items[: self.capacity]
        await self.thalamus.publish(
            Event(
                type="thought.surface",
                payload={"content": concept, "intensity": intensity, "source": item.source},
            )
        )
