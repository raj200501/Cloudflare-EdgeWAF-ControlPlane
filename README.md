# IronShield Edge Security Control Plane

Cloudflare-style local control plane simulator with a FastAPI edge pipeline, signed policy snapshots, deterministic attacker traffic, and a React dashboard.

## Verified quickstart

```bash
make bootstrap
make demo
```

URLs:
- Dashboard: http://localhost:5173
- Edge API: http://localhost:8000
- Origin simulator: http://localhost:8081

## Verified checks

```bash
make verify
cd apps/dashboard && npm test
pytest -q
make loc
```

## Monorepo layout

- `apps/edge`: edge + control plane APIs + websockets
- `apps/origin`: deterministic origin simulator
- `apps/attacker`: deterministic local attacker CLI
- `apps/dashboard`: React + Vite + TypeScript dashboard (legacy dashboard preserved under `apps/dashboard/legacy`)
- `packages/rules_engine`: WAF rule matching engine
- `packages/limiter`: token-bucket rate limiting primitives
- `docs/`: architecture and demo notes

## API summary

### Policies
- `GET/POST /api/policies/waf`
- `GET/POST /api/policies/rate`
- `GET/POST /api/policies/geo`
- `GET/POST /api/policies/bot`
- `PUT/DELETE /api/policies/*/{id}`

### Deployments
- `POST /api/deployments/compile`
- `POST /api/deployments/activate/{snapshot_id}`
- `GET /api/deployments/active`

### Events
- `GET /api/events?limit=500`
- `WS /ws/events`

## Dashboard pages

1. Overview
2. Live Attack Map
3. Events Explorer
4. WAF Rulesets
5. Rate Limiting
6. Geo Policy
7. Bot Management
8. Deployments
9. Analytics
10. Runbooks

## Demo behavior

`make demo` starts origin, edge, dashboard, then launches attacker traffic with a deterministic seed so charts/tables update immediately and reproducibly.
