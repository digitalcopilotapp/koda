"""Persistence layer.

Every event, thought, observation, episode, neuron creation, synapse update
and utterance is recorded as a row. The Memory module subscribes to the
thalamus and writes asynchronously through a bounded queue so the tick loop
is never blocked by disk I/O.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Any

import aiosqlite

from koda_engine.events import Event
from koda_engine.thalamus import Thalamus

log = logging.getLogger(__name__)

DEFAULT_PATH = os.environ.get("KODA_DB_PATH", "koda_brain.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  t REAL NOT NULL,
  payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_type_t ON events(type, t);
CREATE INDEX IF NOT EXISTS events_t ON events(t);

CREATE TABLE IF NOT EXISTS thoughts (
  id TEXT PRIMARY KEY,
  t REAL NOT NULL,
  content TEXT NOT NULL,
  intensity REAL,
  source_neuron TEXT,
  region TEXT,
  drive TEXT,
  emotion TEXT,
  episode_id TEXT,
  user_turn TEXT
);
CREATE INDEX IF NOT EXISTS thoughts_t ON thoughts(t);

CREATE TABLE IF NOT EXISTS observations (
  id TEXT PRIMARY KEY,
  t REAL NOT NULL,
  kind TEXT,
  content TEXT,
  source TEXT,
  intensity REAL,
  related TEXT
);
CREATE INDEX IF NOT EXISTS observations_t ON observations(t);
CREATE INDEX IF NOT EXISTS observations_kind ON observations(kind, t);

CREATE TABLE IF NOT EXISTS neurons (
  id TEXT PRIMARY KEY,
  region TEXT,
  concept TEXT,
  created_at REAL,
  fire_count INTEGER DEFAULT 0,
  last_fired_at REAL
);
CREATE INDEX IF NOT EXISTS neurons_region ON neurons(region);

CREATE TABLE IF NOT EXISTS synapses (
  src TEXT NOT NULL,
  dst TEXT NOT NULL,
  weight REAL,
  signal_count INTEGER DEFAULT 0,
  updated_at REAL,
  PRIMARY KEY (src, dst)
);

CREATE TABLE IF NOT EXISTS episodes (
  id TEXT PRIMARY KEY,
  t REAL,
  label TEXT,
  anchor TEXT,
  members TEXT,
  emotion TEXT,
  drive TEXT
);
CREATE INDEX IF NOT EXISTS episodes_t ON episodes(t);

CREATE TABLE IF NOT EXISTS utterances (
  id TEXT PRIMARY KEY,
  t REAL,
  text TEXT,
  episode_id TEXT
);
CREATE INDEX IF NOT EXISTS utterances_t ON utterances(t);

CREATE TABLE IF NOT EXISTS turns (
  id TEXT PRIMARY KEY,
  t REAL,
  text TEXT,
  episode_id TEXT,
  utterance TEXT,
  emotion TEXT,
  drive TEXT
);
CREATE INDEX IF NOT EXISTS turns_t ON turns(t);
"""


class Memory:
    """Async persistence over sqlite. Subscribes to the thalamus once started."""

    def __init__(self, thalamus: Thalamus, path: str = DEFAULT_PATH) -> None:
        self.path = path
        self.thalamus = thalamus
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=10000)
        self._task: asyncio.Task | None = None
        self._db: aiosqlite.Connection | None = None
        # context that decorates every thought.surface event
        self.current_user_turn: str = ""
        self.current_episode: str = ""
        self.current_emotion: str = ""
        self.current_drive: str = ""

    # ------------------------------------------------------------------ lifecycle
    async def start(self) -> None:
        self._db = await aiosqlite.connect(self.path)
        await self._db.executescript(SCHEMA)
        await self._db.commit()
        self.thalamus.subscribe("*", self._enqueue)
        self._task = asyncio.create_task(self._writer_loop())
        log.info("memory ready at %s", self.path)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._db:
            await self._db.close()
            self._db = None

    # ------------------------------------------------------------------- ingress
    async def _enqueue(self, event: Event) -> None:
        if self._queue.full():
            return  # drop on saturation; better to lose telemetry than to stall the brain
        self._queue.put_nowait(event)

    async def _writer_loop(self) -> None:
        assert self._db is not None
        while True:
            ev = await self._queue.get()
            try:
                await self._persist(ev)
                # batch a few more if queued (keeps WAL happy)
                drained = 0
                while not self._queue.empty() and drained < 64:
                    nxt = self._queue.get_nowait()
                    await self._persist(nxt)
                    drained += 1
                await self._db.commit()
            except asyncio.CancelledError:  # noqa: PERF203
                raise
            except Exception as e:
                log.warning("memory write failed: %s", e)

    # --------------------------------------------------------------- persistence
    async def _persist(self, ev: Event) -> None:
        assert self._db is not None
        # 1. raw event log — every signal is preserved
        await self._db.execute(
            "INSERT OR REPLACE INTO events (id, type, t, payload) VALUES (?, ?, ?, ?)",
            (ev.id, ev.type, ev.t, json.dumps(ev.payload)),
        )

        p = ev.payload
        match ev.type:
            case "neuron.create":
                await self._db.execute(
                    "INSERT OR REPLACE INTO neurons (id, region, concept, created_at, fire_count, last_fired_at) "
                    "VALUES (?, ?, ?, ?, COALESCE((SELECT fire_count FROM neurons WHERE id = ?), 0), 0)",
                    (p.get("id"), p.get("region"), p.get("concept"), ev.t, p.get("id")),
                )

            case "neuron.fire":
                await self._db.execute(
                    "UPDATE neurons SET fire_count = COALESCE(fire_count,0) + 1, last_fired_at = ? WHERE id = ?",
                    (ev.t, p.get("id")),
                )

            case "synapse.signal" | "synapse.strengthen":
                weight = p.get("weight", 0.2)
                await self._db.execute(
                    """
                    INSERT INTO synapses (src, dst, weight, signal_count, updated_at)
                    VALUES (?, ?, ?, 1, ?)
                    ON CONFLICT(src, dst) DO UPDATE SET
                      weight = excluded.weight,
                      signal_count = synapses.signal_count + 1,
                      updated_at = excluded.updated_at
                    """,
                    (p.get("from"), p.get("to"), weight, ev.t),
                )

            case "memory.encode":
                await self._db.execute(
                    "INSERT OR REPLACE INTO episodes (id, t, label, anchor, members, emotion, drive) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        p.get("episode_id"),
                        ev.t,
                        p.get("label", ""),
                        p.get("anchor"),
                        json.dumps(p.get("neurons", [])),
                        self.current_emotion,
                        self.current_drive,
                    ),
                )
                self.current_episode = p.get("episode_id", "") or self.current_episode

            case "thought.surface":
                await self._db.execute(
                    "INSERT OR REPLACE INTO thoughts "
                    "(id, t, content, intensity, source_neuron, region, drive, emotion, episode_id, user_turn) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        ev.id,
                        ev.t,
                        p.get("content", ""),
                        p.get("intensity", 0.0),
                        p.get("source", ""),
                        p.get("region", ""),
                        self.current_drive,
                        self.current_emotion,
                        self.current_episode,
                        self.current_user_turn,
                    ),
                )

            case "observation.note":
                await self._db.execute(
                    "INSERT OR REPLACE INTO observations (id, t, kind, content, source, intensity, related) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        ev.id,
                        ev.t,
                        p.get("kind", "meta"),
                        p.get("content", ""),
                        p.get("source", ""),
                        p.get("intensity", 0.0),
                        json.dumps(p.get("related", [])),
                    ),
                )

            case "broca.utterance":
                await self._db.execute(
                    "INSERT OR REPLACE INTO utterances (id, t, text, episode_id) VALUES (?, ?, ?, ?)",
                    (ev.id, ev.t, p.get("text", ""), self.current_episode),
                )

            case _:
                pass  # already in events table

    # ---------------------------------------------------------------- public API
    async def record_turn(self, text: str, episode_id: str, utterance: str, emotion: str, drive: str) -> str:
        assert self._db is not None
        turn_id = f"turn_{uuid.uuid4().hex[:8]}"
        await self._db.execute(
            "INSERT INTO turns (id, t, text, episode_id, utterance, emotion, drive) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (turn_id, time.time(), text, episode_id, utterance, emotion, drive),
        )
        await self._db.commit()
        return turn_id

    async def query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        assert self._db is not None
        self._db.row_factory = aiosqlite.Row
        async with self._db.execute(sql, params) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
