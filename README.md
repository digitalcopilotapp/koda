# koda

Cognitive architecture inspired by the brain. The LLM is a stateless generative substrate; cognition emerges from a population of agent-neurons grouped into brain regions, communicating through a thalamic event bus.

## Layout

- `engine/` — Python cognitive engine (motor, neurons, regions, thalamus, workspace, FastAPI + WebSocket).
- `visualizer/` — React + react-three-fiber 3D graph that streams brain activity in real time.

## Quickstart

```bash
# engine
cd engine
pip install -e .

# pick ONE auth path:
KODA_BACKEND=claude_code python -m koda_engine     # uses your Claude Code subscription (recommended)
ANTHROPIC_API_KEY=sk-... python -m koda_engine     # uses Anthropic API
python -m koda_engine                              # offline (pseudo-match, dev only)

# visualizer (new shell)
cd visualizer
npm install
npm run dev
```

Open http://localhost:5173 and POST a turn to `http://localhost:8000/turn`:

```bash
curl -X POST http://localhost:8000/turn -H 'content-type: application/json' \
  -d '{"text":"hoje vi uma exposicao do rothko e fiquei estranho"}'
```

### Backends

`KODA_BACKEND` selects the LLM substrate:

- `claude_code` — routes through your local `claude` CLI / subscription via `claude-agent-sdk`. Requires the CLI to be installed and logged in.
- `api` — direct Anthropic API. Requires `ANTHROPIC_API_KEY`.
- `offline` — deterministic keyword pseudo-match. No network. Useful for dev.

If unset, the engine auto-selects: `api` if `ANTHROPIC_API_KEY` is present, else `claude_code` if the SDK is installed, else `offline`.

### Access from mobile / another device

Both servers bind to `0.0.0.0`. Find your machine's LAN IP and open
`http://<your-ip>:5173` from your phone (same Wi-Fi). The Vite dev server proxies `/turn`, `/state`, `/memory`, and `/ws` to the engine on `:8000`.

For access outside the LAN, run a tunnel:

```bash
# cloudflared (no signup)
cloudflared tunnel --url http://localhost:5173

# or ngrok
ngrok http 5173
```

## Architecture

See `docs/` (forthcoming) and inline module docstrings. Key concepts:

- **Motor** — primitives `match`, `generate`, `abstract`, `evaluate`, `embed` over Anthropic API with caching.
- **Neuron** — small stateful agent: `activation`, `threshold`, `synapses`, Hebbian plasticity.
- **Region** — population of neurons with characteristic dynamics (Hippocampus, Amygdala, PFC, Broca).
- **Thalamus** — async pub/sub bus; every signal flows through it.
- **Workspace** — small buffer; only the strongest patterns become "conscious" and reach Broca.
