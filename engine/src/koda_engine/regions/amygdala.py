from __future__ import annotations

from koda_engine.events import Event
from koda_engine.neurons import Neuron
from koda_engine.regions.base import Region

EMOTIONS = {
    "fear": "fear, threat, anxiety, danger",
    "joy": "joy, delight, pleasure, warmth",
    "sadness": "sadness, loss, grief, melancholy, saudade",
    "awe": "awe, wonder, sublime, beauty, art",
    "anger": "anger, frustration, irritation",
    "tenderness": "tenderness, care, affection, intimacy",
}


class Amygdala(Region):
    """Fast-and-dirty affective tagger. Modulates brain-wide plasticity."""

    name = "amygdala"
    anatomy = (-0.2, -0.15, 0.05)
    color = "#e85b6e"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.modulation: float = 1.0  # multiplier for plasticity
        self.last_emotion: str = ""

    async def boot(self) -> None:
        for emotion in EMOTIONS:
            await self.add_neuron(Neuron(region=self.name, concept=emotion, threshold=0.45))

    async def on_user_turn(self, text: str) -> None:
        # parallel scoring of all emotion-neurons
        for n in list(self.neurons.values()):
            pattern = EMOTIONS.get(n.concept, n.concept)
            score = await self.motor.match(text, pattern)
            n.receive(score, source_text=text)
        # set modulation: stronger emotion → more plasticity
        peak = max((n.activation for n in self.neurons.values()), default=0.0)
        self.modulation = 1.0 + peak * 1.5
        if peak > 0.4:
            top = max(self.neurons.values(), key=lambda n: n.activation)
            self.last_emotion = top.concept
