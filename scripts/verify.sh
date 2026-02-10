#!/usr/bin/env bash
set -euo pipefail

python -m ruff check .
python -m ruff format --check .
pytest -q

pushd apps/dashboard >/dev/null
npm ci
npm run lint
npm run typecheck
npm test
npm run build
popd >/dev/null
