#!/usr/bin/env bash
set -euo pipefail

echo "==> installing engine (python)"
cd "$(dirname "$0")/.."
pip install --user -e ./engine

echo "==> installing visualizer (node)"
cd visualizer
npm install
cd ..

echo "==> installing claude CLI"
npm install -g @anthropic-ai/claude-code || echo "(optional) claude CLI install failed; you can still use ANTHROPIC_API_KEY"

echo
echo "==> done."
echo
echo "Next steps:"
echo "  1) authenticate (pick one):"
echo "     - subscription:    claude login"
echo "     - api key:         export ANTHROPIC_API_KEY=sk-..."
echo "  2) start both servers:  ./dev.sh"
echo "  3) open the forwarded 'visualizer' port (5173) in the Ports tab"
