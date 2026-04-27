from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field

from koda_engine.events import Event
from koda_engine.thalamus import Thalamus


@dataclass
class Synapse:
    target: str
    weight: float = 0.2


@dataclass
class Neuron:
    """Minimal stateful unit. Most neurons never call the LLM — they just
    accumulate, fire, and propagate. Interpretive neurons (those with a
    `concept`) can ask the motor to score incoming text."""

    region: str
    concept: str = ""
    id: str = field(default_factory=lambda: f"n_{uuid.uuid4().hex[:8]}")
    activation: float = 0.0
    threshold: float = 0.55
    decay: float = 0.92  # per tick
    refractory_ms: int = 80
    last_fired_at: float = 0.0
    synapses: list[Synapse] = field(default_factory=list)
    fire_count: int = 0
    recent_input: str = ""

    def step(self) -> None:
        self.activation *= self.decay
        if self.activation < 1e-3:
            self.activation = 0.0

    def receive(self, intensity: float, source_text: str = "") -> None:
        self.activation = min(1.5, self.activation + intensity)
        if source_text:
            self.recent_input = source_text

    def can_fire(self) -> bool:
        if self.activation < self.threshold:
            return False
        return (time.time() - self.last_fired_at) * 1000 >= self.refractory_ms

    async def fire(self, thalamus: Thalamus, plasticity: float = 1.0) -> list[tuple[str, float]]:
        self.last_fired_at = time.time()
        self.fire_count += 1
        intensity = float(min(1.0, self.activation))
        self.activation = 0.0  # spent
        await thalamus.publish(
            Event(
                type="neuron.fire",
                payload={"id": self.id, "region": self.region, "concept": self.concept, "intensity": intensity},
            )
        )
        delivered: list[tuple[str, float]] = []
        for syn in self.synapses:
            payload_intensity = intensity * syn.weight
            if payload_intensity < 0.02:
                continue
            await thalamus.publish(
                Event(
                    type="synapse.signal",
                    payload={
                        "from": self.id,
                        "to": syn.target,
                        "weight": syn.weight,
                        "intensity": payload_intensity,
                    },
                )
            )
            delivered.append((syn.target, payload_intensity))
        # Hebbian: caller will report back which targets fired soon after, and
        # we'll strengthen those synapses via `reinforce()`.
        _ = plasticity
        return delivered

    def reinforce(self, target_id: str, delta: float) -> float:
        for syn in self.synapses:
            if syn.target == target_id:
                syn.weight = max(0.01, min(1.5, syn.weight + delta))
                return syn.weight
        # form new synapse if none exists
        syn = Synapse(target=target_id, weight=max(0.05, delta))
        self.synapses.append(syn)
        return syn.weight

    def prune(self, floor: float = 0.04) -> int:
        before = len(self.synapses)
        self.synapses = [s for s in self.synapses if s.weight >= floor]
        return before - len(self.synapses)


def hebbian_delta(pre_intensity: float, post_intensity: float, lr: float = 0.05) -> float:
    """Simple Hebbian rule with saturation."""
    return lr * pre_intensity * post_intensity * (1.0 - math.tanh(pre_intensity * post_intensity))
