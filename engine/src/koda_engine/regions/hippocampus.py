from __future__ import annotations

import time
import uuid

from koda_engine.events import Event
from koda_engine.neurons import Neuron, Synapse
from koda_engine.regions.base import Region


class Hippocampus(Region):
    """Episodic encoding + pattern completion.

    On each user turn we snapshot the currently-active neurons across the brain
    and bind them into an "episode" — a small constellation. Future activations
    that overlap with an episode partially complete the pattern (re-activate
    the rest of its neurons), simulating memory recall.
    """

    name = "hippocampus"
    anatomy = (0.0, -0.2, 0.0)
    color = "#7a5af5"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.episodes: dict[str, dict] = {}
        self.thalamus.subscribe("neuron.fire", self._on_any_fire)
        self._coactive: dict[str, float] = {}  # neuron_id -> last seen intensity

    async def _on_any_fire(self, ev: Event) -> None:
        nid = ev.payload.get("id")
        if not nid:
            return
        self._coactive[nid] = ev.t
        # pattern completion: if a hippocampus neuron fires that participates
        # in episodes, partially re-activate the rest of those episodes
        if ev.payload.get("region") == self.name:
            await self._complete_pattern(nid)

    async def encode_episode(self, label: str = "") -> str:
        """Snapshot recently coactive neurons as a new episode."""
        now = time.time()
        members = [nid for nid, t in self._coactive.items() if now - t < 1.5]
        if len(members) < 2:
            return ""
        ep_id = f"ep_{uuid.uuid4().hex[:8]}"
        # create an index neuron in the hippocampus that points to the members
        anchor = Neuron(region=self.name, concept=f"episode:{label}" if label else "episode")
        anchor.synapses = [Synapse(target=mid, weight=0.5) for mid in members]
        await self.add_neuron(anchor)
        self.episodes[ep_id] = {"id": ep_id, "label": label, "anchor": anchor.id, "members": members, "t": now}
        await self.thalamus.publish(
            Event(type="memory.encode", payload={"episode_id": ep_id, "anchor": anchor.id, "neurons": members, "label": label})
        )
        return ep_id

    async def _complete_pattern(self, anchor_id: str) -> None:
        for ep in self.episodes.values():
            if ep["anchor"] != anchor_id:
                continue
            # Trigger a soft re-activation of episode members via the bus
            for mid in ep["members"]:
                await self.thalamus.publish(
                    Event(
                        type="synapse.signal",
                        payload={"from": anchor_id, "to": mid, "weight": 0.4, "intensity": 0.3},
                    )
                )
