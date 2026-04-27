# koda

Cognitive architecture inspired by the brain. The LLM is a stateless generative substrate; cognition emerges from a population of agent-neurons grouped into brain regions, communicating through a thalamic event bus.

## Layout

- `engine/` — Python cognitive engine (motor, neurons, regions, thalamus, workspace, FastAPI + WebSocket).
- `visualizer/` — React + react-three-fiber 3D graph that streams brain activity in real time.

## Quickstart

```bash
# engine
cd engine
uv sync   # or: pip install -e .
ANTHROPIC_API_KEY=sk-... python -m koda_engine

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

## Architecture

See `docs/` (forthcoming) and inline module docstrings. Key concepts:

- **Motor** — primitives `match`, `generate`, `abstract`, `evaluate`, `embed` over Anthropic API with caching.
- **Neuron** — small stateful agent: `activation`, `threshold`, `synapses`, Hebbian plasticity.
- **Region** — population of neurons with characteristic dynamics (Hippocampus, Amygdala, PFC, Broca).
- **Thalamus** — async pub/sub bus; every signal flows through it.
- **Workspace** — small buffer; only the strongest patterns become "conscious" and reach Broca.
