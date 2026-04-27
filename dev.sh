#!/usr/bin/env bash
# Run engine + visualizer together. Ctrl-C stops both.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT/.logs"
mkdir -p "$LOG_DIR"

cleanup() {
  echo
  echo "==> stopping…"
  kill "${ENGINE_PID:-}" "${VIZ_PID:-}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "==> engine on :8000  (logs: $LOG_DIR/engine.log)"
( cd "$ROOT/engine" && python -m koda_engine ) > "$LOG_DIR/engine.log" 2>&1 &
ENGINE_PID=$!

echo "==> visualizer on :5173  (logs: $LOG_DIR/visualizer.log)"
( cd "$ROOT/visualizer" && npm run dev -- --host 0.0.0.0 ) > "$LOG_DIR/visualizer.log" 2>&1 &
VIZ_PID=$!

echo
echo "==> tailing logs (Ctrl-C to stop both)"
tail -F "$LOG_DIR/engine.log" "$LOG_DIR/visualizer.log"
