from __future__ import annotations

from typing import TYPE_CHECKING

from koda_engine.events import Event
from koda_engine.motor import Motor
from koda_engine.neurons import Neuron, hebbian_delta
from koda_engine.thalamus import Thalamus

if TYPE_CHECKING:
    from koda_engine.workspace import Workspace


class Region:
    """A population of neurons with characteristic dynamics."""

    name: str = "region"
    anatomy: tuple[float, float, float] = (0.0, 0.0, 0.0)  # x, y, z layout hint
    color: str = "#888888"

    def __init__(self, motor: Motor, thalamus: Thalamus, workspace: "Workspace | None" = None) -> None:
        self.motor = motor
        self.thalamus = thalamus
        self.workspace = workspace
        self.neurons: dict[str, Neuron] = {}
        self.activation_level: float = 0.0
        self._fired_recently: list[tuple[str, float, float]] = []  # (neuron_id, intensity, t)
        thalamus.subscribe("synapse.signal", self._on_signal)
        thalamus.subscribe("neuron.fire", self._track_fire)

    # ------------------------------------------------------------------ wiring
    async def add_neuron(self, neuron: Neuron) -> Neuron:
        neuron.region = self.name
        self.neurons[neuron.id] = neuron
        await self.thalamus.publish(
            Event(
                type="neuron.create",
                payload={
                    "id": neuron.id,
                    "region": self.name,
                    "concept": neuron.concept,
                    "anatomy": list(self.anatomy),
                    "color": self.color,
                },
            )
        )
        return neuron

    # ------------------------------------------------------------------ ticks
    async def step(self) -> None:
        for n in self.neurons.values():
            n.step()
        # fire whoever crossed threshold
        ready = [n for n in self.neurons.values() if n.can_fire()]
        for n in ready:
            delivered = await n.fire(self.thalamus)
            # Hebbian: strengthen synapse if target fired in the last window
            for target_id, intensity in delivered:
                post = self._recent_intensity(target_id, window=0.4)
                if post > 0:
                    delta = hebbian_delta(intensity, post)
                    new_w = n.reinforce(target_id, delta)
                    await self.thalamus.publish(
                        Event(
                            type="synapse.strengthen",
                            payload={"from": n.id, "to": target_id, "weight": new_w, "delta": delta},
                        )
                    )
        # region-level activation = mean of top-3 neurons
        top = sorted((n.activation for n in self.neurons.values()), reverse=True)[:3]
        new_level = sum(top) / 3 if top else 0.0
        if abs(new_level - self.activation_level) > 0.05:
            self.activation_level = new_level
            await self.thalamus.publish(
                Event(type="region.activate", payload={"region": self.name, "level": new_level})
            )

    # --------------------------------------------------------------- callbacks
    async def _on_signal(self, ev: Event) -> None:
        target = ev.payload.get("to")
        if target in self.neurons:
            self.neurons[target].receive(ev.payload.get("intensity", 0.0))

    async def _track_fire(self, ev: Event) -> None:
        nid = ev.payload.get("id")
        intensity = ev.payload.get("intensity", 0.0)
        self._fired_recently.append((nid, intensity, ev.t))
        # trim
        cutoff = ev.t - 1.0
        self._fired_recently = [r for r in self._fired_recently if r[2] >= cutoff]

    def _recent_intensity(self, neuron_id: str, window: float = 0.4) -> float:
        import time

        cutoff = time.time() - window
        for nid, intensity, t in reversed(self._fired_recently):
            if nid == neuron_id and t >= cutoff:
                return intensity
        return 0.0

    # -------------------------------------------------------- region lifecycle
    async def on_user_turn(self, text: str) -> None:
        """Called by Brain at the start of each turn. Override if needed."""
