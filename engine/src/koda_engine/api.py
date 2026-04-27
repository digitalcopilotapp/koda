from __future__ import annotations

import asyncio
import contextlib
import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from koda_engine.brain import Brain

log = logging.getLogger(__name__)


class TurnIn(BaseModel):
    text: str


def create_app() -> FastAPI:
    app = FastAPI(title="koda-engine")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    brain = Brain()
    app.state.brain = brain

    @app.on_event("startup")
    async def _startup() -> None:
        await brain.start()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await brain.stop()

    @app.post("/turn")
    async def turn(body: TurnIn) -> dict:
        return await brain.turn(body.text)

    @app.get("/state")
    async def state() -> dict:
        return {
            "regions": [
                {
                    "name": r.name,
                    "color": r.color,
                    "anatomy": list(r.anatomy),
                    "activation": r.activation_level,
                    "neurons": [
                        {
                            "id": n.id,
                            "concept": n.concept,
                            "activation": n.activation,
                            "synapses": [{"to": s.target, "w": s.weight} for s in n.synapses],
                        }
                        for n in r.neurons.values()
                    ],
                }
                for r in brain.regions
            ]
        }

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        q = brain.thalamus.fanout()
        # send a snapshot first so visualizer can render existing neurons
        snapshot = await state()
        await websocket.send_text(json.dumps({"type": "snapshot", "payload": snapshot}))
        try:
            while True:
                ev = await q.get()
                await websocket.send_text(json.dumps(ev.to_wire()))
        except WebSocketDisconnect:
            pass
        except Exception as e:  # pragma: no cover - defensive
            log.warning("ws error: %s", e)
        finally:
            brain.thalamus.drop_fanout(q)
            with contextlib.suppress(Exception):
                await websocket.close()

    return app


app = create_app()
