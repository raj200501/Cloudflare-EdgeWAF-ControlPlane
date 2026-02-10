# Architecture

IronShield has two planes:

- **Control plane**: CRUD policies + compile immutable deployment snapshots with deterministic hashing.
- **Data plane (edge)**: request evaluation pipeline (`geo -> waf -> rate limit -> bot`) and reverse proxy to origin.

## Data flow

1. Dashboard or API client creates policies.
2. `/api/deployments/compile` builds canonical bundle and SHA-256 hash.
3. `/api/deployments/activate/{id}` marks active snapshot.
4. Edge handles requests, emits event per request to state backend and websocket subscribers.

## State

`apps/edge/store.py` exposes `StateBackend` with:

- `InMemoryStateBackend` (always available)
- `RedisStateBackend` (used automatically when `REDIS_URL` is configured and reachable)

## Observability

Response headers include:
- `Server-Timing`
- `X-IronShield-Decision`
- `X-IronShield-Reason`
- `X-IronShield-Country`
