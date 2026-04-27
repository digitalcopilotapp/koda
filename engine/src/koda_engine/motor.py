from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from anthropic import AsyncAnthropic

FAST_MODEL = os.environ.get("KODA_FAST_MODEL", "claude-haiku-4-5-20251001")
DEEP_MODEL = os.environ.get("KODA_DEEP_MODEL", "claude-sonnet-4-6")


@dataclass
class MotorConfig:
    fast_model: str = FAST_MODEL
    deep_model: str = DEEP_MODEL
    offline: bool = False


class Motor:
    """LLM substrate. No agent state — pure primitives."""

    def __init__(self, cfg: MotorConfig | None = None) -> None:
        self.cfg = cfg or MotorConfig()
        self.cfg.offline = self.cfg.offline or not os.environ.get("ANTHROPIC_API_KEY")
        self._client: AsyncAnthropic | None = None if self.cfg.offline else AsyncAnthropic()
        self._embed_cache: dict[str, list[float]] = {}

    async def match(self, text: str, pattern: str) -> float:
        """Score in [0,1] for whether `text` evokes `pattern`."""
        if self.cfg.offline:
            return _offline_match(text, pattern)
        prompt = (
            f"Pattern: {pattern}\nText: {text}\n\n"
            "On a 0.00-1.00 scale, how strongly does the text evoke the pattern? "
            "Reply with only the number."
        )
        out = await self._gen(self.cfg.fast_model, prompt, max_tokens=8)
        try:
            return max(0.0, min(1.0, float(out.strip().split()[0])))
        except (ValueError, IndexError):
            return 0.0

    async def generate(self, system: str, user: str, *, deep: bool = False, max_tokens: int = 512) -> str:
        if self.cfg.offline:
            return _offline_generate(system, user)
        model = self.cfg.deep_model if deep else self.cfg.fast_model
        return await self._gen(model, user, system=system, max_tokens=max_tokens)

    async def abstract(self, items: list[str]) -> str:
        if not items:
            return ""
        if self.cfg.offline:
            return f"({len(items)} items)"
        joined = "\n- ".join(items)
        return await self.generate(
            "You distil clusters of episodes into one concise concept (<=12 words).",
            f"Items:\n- {joined}\n\nConcept:",
            max_tokens=40,
        )

    async def embed(self, text: str) -> list[float]:
        """Cheap deterministic pseudo-embedding (offline-safe).

        We do NOT call a real embedding API here — keeps the engine runnable
        with zero dependencies for the MVP. Swap for Voyage/OpenAI later.
        """
        h = hashlib.blake2b(text.encode(), digest_size=64).digest()
        if text in self._embed_cache:
            return self._embed_cache[text]
        vec = [(b - 128) / 128 for b in h]
        self._embed_cache[text] = vec
        return vec

    async def _gen(self, model: str, prompt: str, *, system: str | None = None, max_tokens: int = 256) -> str:
        assert self._client is not None
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        msg = await self._client.messages.create(**kwargs)
        parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
        return "".join(parts)


def _offline_match(text: str, pattern: str) -> float:
    import re

    tokens = lambda s: {w for w in re.split(r"[^a-zÀ-ſ]+", s.lower()) if len(w) > 2}
    t, p = tokens(text), tokens(pattern)
    if not p:
        return 0.0
    overlap = len(t & p)
    return min(1.0, 0.4 * overlap + 0.05)


def _offline_generate(system: str, user: str) -> str:
    return f"[offline] {user[:120]}"
