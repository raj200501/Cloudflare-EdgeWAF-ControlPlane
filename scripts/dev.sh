#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  if [[ -n "${EDGE_PID:-}" ]]; then kill "$EDGE_PID"; fi
  if [[ -n "${ORIGIN_PID:-}" ]]; then kill "$ORIGIN_PID"; fi
  if [[ -n "${DASH_PID:-}" ]]; then kill "$DASH_PID"; fi
}
trap cleanup EXIT

PYTHONPATH=. python -m uvicorn apps.origin.main:app --host 0.0.0.0 --port 8081 &
ORIGIN_PID=$!
PYTHONPATH=. python -m uvicorn apps.edge.main:app --host 0.0.0.0 --port 8080 &
EDGE_PID=$!

pushd apps/dashboard >/dev/null
npm install
npm run dev -- --host 0.0.0.0 --port 5173 &
DASH_PID=$!
popd >/dev/null

wait
