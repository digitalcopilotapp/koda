"""LLM substrate. Three interchangeable backends:

1. **api**         — Anthropic API via `anthropic` SDK (requires ANTHROPIC_API_KEY).
2. **claude_code** — Claude Code OAuth (your subscription) via `claude-agent-sdk`.
                     Requires the `claude` CLI installed and logged in.
3. **offline**     — pseudo deterministic match/generate. Zero deps, for dev.

Selection precedence:
- Explicit: `KODA_BACKEND=api|claude_code|offline`
- Auto: ANTHROPIC_API_KEY set → api; else claude-agent-sdk importable → claude_code;
  else → offline.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from dataclasses import dataclass

log = logging.getLogger(__name__)

FAST_MODEL = os.environ.get("KODA_FAST_MODEL", "claude-haiku-4-5-20251001")
DEEP_MODEL = os.environ.get("KODA_DEEP_MODEL", "claude-sonnet-4-6")


@dataclass
class MotorConfig:
    fast_model: str = FAST_MODEL
    deep_model: str = DEEP_MODEL
    backend: str = ""  # "api" | "claude_code" | "offline" (auto if empty)


class Motor:
    """LLM substrate. No agent state — pure primitives."""

    def __init__(self, cfg: MotorConfig | None = None) -> None:
        self.cfg = cfg or MotorConfig()
        if not self.cfg.backend:
            self.cfg.backend = os.environ.get("KODA_BACKEND", "").lower() or _auto_backend()
        self._impl = _build_backend(self.cfg.backend)
        self._embed_cache: dict[str, list[float]] = {}
        log.info("motor backend=%s fast=%s deep=%s", self.cfg.backend, self.cfg.fast_model, self.cfg.deep_model)

    @property
    def backend(self) -> str:
        return self.cfg.backend

    async def match(self, text: str, pattern: str) -> float:
        if self.cfg.backend == "offline":
            return _offline_match(text, pattern)
        prompt = (
            f"Pattern: {pattern}\nText: {text}\n\n"
            "On a 0.00-1.00 scale, how strongly does the text evoke the pattern? "
            "Reply with only the number."
        )
        out = await self._impl.generate(model=self.cfg.fast_model, system=None, user=prompt, max_tokens=8)
        try:
            return max(0.0, min(1.0, float(out.strip().split()[0])))
        except (ValueError, IndexError):
            return 0.0

    async def generate(self, system: str, user: str, *, deep: bool = False, max_tokens: int = 512) -> str:
        model = self.cfg.deep_model if deep else self.cfg.fast_model
        return await self._impl.generate(model=model, system=system, user=user, max_tokens=max_tokens)

    async def abstract(self, items: list[str]) -> str:
        if not items:
            return ""
        joined = "\n- ".join(items)
        return await self.generate(
            "You distil clusters of episodes into one concise concept (<=12 words).",
            f"Items:\n- {joined}\n\nConcept:",
            max_tokens=40,
        )

    async def embed(self, text: str) -> list[float]:
        """Deterministic pseudo-embedding. Swap for Voyage/OpenAI later."""
        if text in self._embed_cache:
            return self._embed_cache[text]
        h = hashlib.blake2b(text.encode(), digest_size=64).digest()
        vec = [(b - 128) / 128 for b in h]
        self._embed_cache[text] = vec
        return vec


# ---------------------------------------------------------------------- backends


class _Backend:
    async def generate(self, *, model: str, system: str | None, user: str, max_tokens: int) -> str:
        raise NotImplementedError


class _OfflineBackend(_Backend):
    async def generate(self, *, model: str, system: str | None, user: str, max_tokens: int) -> str:  # noqa: ARG002
        return _offline_generate(system or "", user)


class _ApiBackend(_Backend):
    def __init__(self) -> None:
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic()

    async def generate(self, *, model: str, system: str | None, user: str, max_tokens: int) -> str:
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": user}],
        }
        if system:
            kwargs["system"] = system
        msg = await self.client.messages.create(**kwargs)
        return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")


class _ClaudeCodeBackend(_Backend):
    """Routes through the user's Claude Code subscription.

    Uses `claude-agent-sdk.query()` which spawns the local `claude` CLI
    and inherits its OAuth session — no API key required.
    """

    def __init__(self) -> None:
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ResultMessage,
            TextBlock,
            query,
        )

        self._query = query
        self._options_cls = ClaudeAgentOptions
        self._AssistantMessage = AssistantMessage
        self._ResultMessage = ResultMessage
        self._TextBlock = TextBlock

    async def generate(self, *, model: str, system: str | None, user: str, max_tokens: int) -> str:  # noqa: ARG002
        opts = self._options_cls(
            model=model,
            system_prompt=system or "",
            max_turns=1,
            permission_mode="bypassPermissions",
        )
        parts: list[str] = []
        result_text: str | None = None
        async for msg in self._query(prompt=user, options=opts):
            if isinstance(msg, self._ResultMessage):
                result_text = msg.result
                break
            if isinstance(msg, self._AssistantMessage):
                for block in msg.content:
                    if isinstance(block, self._TextBlock):
                        parts.append(block.text)
        return result_text if result_text is not None else "".join(parts)


def _auto_backend() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "api"
    try:
        import claude_agent_sdk  # noqa: F401

        return "claude_code"
    except ImportError:
        return "offline"


def _build_backend(name: str) -> _Backend:
    if name == "api":
        try:
            return _ApiBackend()
        except Exception as e:
            log.warning("api backend init failed (%s) — falling back to offline", e)
            return _OfflineBackend()
    if name == "claude_code":
        try:
            return _ClaudeCodeBackend()
        except Exception as e:
            log.warning("claude_code backend init failed (%s) — falling back to offline", e)
            return _OfflineBackend()
    return _OfflineBackend()


# ------------------------------------------------------------------- offline ops


def _offline_match(text: str, pattern: str) -> float:
    def tokens(s: str) -> set[str]:
        return {w for w in re.split(r"[^a-zÀ-ſ]+", s.lower()) if len(w) > 2}

    t, p = tokens(text), tokens(pattern)
    if not p:
        return 0.0
    overlap = len(t & p)
    return min(1.0, 0.4 * overlap + 0.05)


def _offline_generate(system: str, user: str) -> str:  # noqa: ARG001
    return f"[offline] {user[:120]}"
