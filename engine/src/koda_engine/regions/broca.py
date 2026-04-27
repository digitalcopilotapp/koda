from __future__ import annotations

from koda_engine.events import Event
from koda_engine.regions.base import Region


class Broca(Region):
    """Language production. Reads from the global workspace; if there is
    something to say, asks the motor to articulate it."""

    name = "broca"
    anatomy = (-0.4, 0.25, 0.1)
    color = "#f5a524"

    async def speak(self) -> str | None:
        if not self.workspace or not self.workspace.has_content():
            return None
        items = self.workspace.snapshot()
        # Simple system prompt; richer interpolation can come later.
        from koda_engine.regions.prefrontal import PrefrontalCortex  # local import avoids cycle

        pfc = next((r for r in self._sibling_regions() if isinstance(r, PrefrontalCortex)), None)
        emotion = ""
        drive = ""
        if pfc:
            drive = pfc.winning_drive() or ""
        for r in self._sibling_regions():
            if r.name == "amygdala":
                emotion = getattr(r, "last_emotion", "")
        system = (
            "You are the language production area of a brain-inspired system. "
            "Speak in 1-3 short Portuguese sentences, in first person, as a curious mind reflecting. "
            "Do not be a chatbot; be a thinking voice."
        )
        user_parts = [f"User just said: {self.workspace.user_turn or '...'}"]
        if items:
            user_parts.append("Active conscious content: " + " | ".join(items))
        if emotion:
            user_parts.append(f"Felt tone: {emotion}")
        if drive:
            user_parts.append(f"Dominant drive: {drive}")
        text = await self.motor.generate(system, "\n".join(user_parts), deep=True, max_tokens=240)
        await self.thalamus.publish(Event(type="broca.utterance", payload={"text": text}))
        return text

    def _sibling_regions(self) -> list[Region]:
        # set by Brain on registration
        return getattr(self, "_siblings", [])
