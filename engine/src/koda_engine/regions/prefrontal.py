from __future__ import annotations

from koda_engine.events import Event
from koda_engine.neurons import Neuron
from koda_engine.regions.base import Region

DRIVES = {
    "curiosity": "questions unanswered, gaps in understanding, novel topics",
    "aesthetic": "beauty, form, art, rhythm, composition, sublime",
    "coherence": "contradictions, alignments, narrative threads",
    "care": "the user's wellbeing, mood shifts, what is unsaid",
}


class PrefrontalCortex(Region):
    """Executive control: holds working memory, runs drives, decides what
    competes for the global workspace."""

    name = "prefrontal"
    anatomy = (0.0, 0.4, 0.25)
    color = "#3da9fc"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.working_memory: list[str] = []

    async def boot(self) -> None:
        for drive in DRIVES:
            await self.add_neuron(Neuron(region=self.name, concept=f"drive:{drive}", threshold=0.5))

    async def on_user_turn(self, text: str) -> None:
        self.working_memory.append(text)
        if len(self.working_memory) > 8:
            self.working_memory = self.working_memory[-8:]
        for n in self.neurons.values():
            drive_name = n.concept.split(":", 1)[-1]
            pattern = DRIVES.get(drive_name, drive_name)
            score = await self.motor.match(text, pattern)
            n.receive(score, source_text=text)

    def winning_drive(self) -> str | None:
        if not self.neurons:
            return None
        top = max(self.neurons.values(), key=lambda n: n.activation)
        if top.activation < 0.3:
            return None
        return top.concept.split(":", 1)[-1]
