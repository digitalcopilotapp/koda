from __future__ import annotations

import asyncio
from typing import Any

from koda_engine.memory import Memory
from koda_engine.motor import Motor
from koda_engine.regions import Amygdala, Broca, Hippocampus, PrefrontalCortex, Region
from koda_engine.thalamus import Thalamus
from koda_engine.workspace import Workspace


class Brain:
    """Top-level orchestrator. Holds regions, runs the tick loop."""

    def __init__(self, motor: Motor | None = None, db_path: str | None = None) -> None:
        self.motor = motor or Motor()
        self.thalamus = Thalamus()
        self.memory = Memory(self.thalamus, path=db_path) if db_path else Memory(self.thalamus)
        self.workspace = Workspace(self.thalamus)
        self.hippocampus = Hippocampus(self.motor, self.thalamus, self.workspace)
        self.amygdala = Amygdala(self.motor, self.thalamus, self.workspace)
        self.prefrontal = PrefrontalCortex(self.motor, self.thalamus, self.workspace)
        self.broca = Broca(self.motor, self.thalamus, self.workspace)
        self.regions: list[Region] = [self.hippocampus, self.amygdala, self.prefrontal, self.broca]
        # let Broca see siblings without importing them
        self.broca._siblings = self.regions  # type: ignore[attr-defined]
        self._tick_task: asyncio.Task | None = None
        self._running = False

    async def boot(self) -> None:
        await self.amygdala.boot()
        await self.prefrontal.boot()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        await self.memory.start()
        await self.boot()
        self._tick_task = asyncio.create_task(self._tick_loop())

    async def stop(self) -> None:
        self._running = False
        if self._tick_task:
            self._tick_task.cancel()
            try:
                await self._tick_task
            except asyncio.CancelledError:
                pass
        await self.memory.stop()

    async def _tick_loop(self) -> None:
        while self._running:
            await asyncio.gather(*(r.step() for r in self.regions), return_exceptions=True)
            await asyncio.sleep(0.05)

    async def turn(self, text: str) -> dict[str, Any]:
        """Process a user turn end-to-end and return the spoken response."""
        self.workspace.user_turn = text
        self.memory.current_user_turn = text
        # 1. parallel sensory/affective uptake
        await asyncio.gather(
            self.amygdala.on_user_turn(text),
            self.prefrontal.on_user_turn(text),
        )
        # propagate context for thought decoration
        self.memory.current_emotion = self.amygdala.last_emotion or ""
        self.memory.current_drive = self.prefrontal.winning_drive() or ""
        # 2. let neurons settle / fire across a few ticks
        for _ in range(8):
            await asyncio.gather(*(r.step() for r in self.regions), return_exceptions=True)
            await asyncio.sleep(0.05)
        # 3. encode the constellation as an episode
        episode_id = await self.hippocampus.encode_episode(label=text[:32])
        self.memory.current_episode = episode_id or ""
        # 4. let Broca speak from the workspace
        utterance = await self.broca.speak()
        # 5. record the turn
        await self.memory.record_turn(
            text=text,
            episode_id=episode_id or "",
            utterance=utterance or "",
            emotion=self.memory.current_emotion,
            drive=self.memory.current_drive,
        )
        # 6. clear workspace for next turn
        self.workspace.clear()
        return {
            "utterance": utterance or "",
            "episode_id": episode_id,
            "drive": self.prefrontal.winning_drive(),
            "emotion": self.amygdala.last_emotion,
        }
