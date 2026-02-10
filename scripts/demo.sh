#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  [[ -n "${EDGE_PID:-}" ]] && kill "$EDGE_PID" || true
  [[ -n "${ORIGIN_PID:-}" ]] && kill "$ORIGIN_PID" || true
  [[ -n "${DASH_PID:-}" ]] && kill "$DASH_PID" || true
  [[ -n "${ATTACKER_PID:-}" ]] && kill "$ATTACKER_PID" || true
}
trap cleanup EXIT

PYTHONPATH=. python -m uvicorn apps.origin.main:app --host 0.0.0.0 --port 8081 &
ORIGIN_PID=$!
PYTHONPATH=. python -m uvicorn apps.edge.main:app --host 0.0.0.0 --port 8000 &
EDGE_PID=$!

pushd apps/dashboard >/dev/null
npm run dev -- --host 0.0.0.0 --port 5173 &
DASH_PID=$!
popd >/dev/null

echo "Demo running"
echo "- Dashboard: http://localhost:5173"
echo "- Edge API:   http://localhost:8000"

sleep 4
python -m apps.attacker.run --target http://localhost:8000 --duration 3600 --seed 123 --workers 6 &
ATTACKER_PID=$!

wait
