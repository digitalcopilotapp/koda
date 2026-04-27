from __future__ import annotations

import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "neuron.create",
    "neuron.fire",
    "synapse.signal",
    "synapse.strengthen",
    "memory.encode",
    "region.activate",
    "thought.surface",
    "user.turn",
    "broca.utterance",
]


class Event(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    type: EventType
    t: float = Field(default_factory=time.time)
    payload: dict[str, Any] = Field(default_factory=dict)

    def to_wire(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.type, "t": self.t, **self.payload}
