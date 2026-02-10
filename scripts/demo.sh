#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=. python -m uvicorn apps.origin.main:app --host 0.0.0.0 --port 8081 &
ORIGIN_PID=$!
PYTHONPATH=. python -m uvicorn apps.edge.main:app --host 0.0.0.0 --port 8080 &
EDGE_PID=$!

pushd apps/dashboard >/dev/null
npm install
npm run dev -- --host 0.0.0.0 --port 5173 &
DASH_PID=$!
popd >/dev/null

cleanup() {
  kill "$EDGE_PID" "$ORIGIN_PID" "$DASH_PID"
}
trap cleanup EXIT

sleep 3
python -m apps.attacker.run --target http://localhost:8080 --profile mixed &
ATTACKER_PID=$!

while true; do
  sleep 5
  python -m apps.attacker.run --target http://localhost:8080 --profile attack
  sleep 5
  python -m apps.attacker.run --target http://localhost:8080 --profile normal
  if ! kill -0 "$EDGE_PID" 2>/dev/null; then
    break
  fi
done

wait "$ATTACKER_PID"
