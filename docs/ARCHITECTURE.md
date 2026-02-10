# IronShield Architecture

## Components
- **Edge (apps/edge)**: FastAPI reverse proxy with WAF, rate limiting, geo policy, and event streaming.
- **Origin (apps/origin)**: Deterministic upstream service.
- **Dashboard (apps/dashboard)**: React UI with live attack map and control panels.
- **Attacker (apps/attacker)**: Deterministic traffic generator.
- **Rules Engine (packages/rules_engine)**: JSON ruleset parsing and matching.
- **Limiter (packages/limiter)**: Token bucket rate limiter.

## Event Flow
1. Request arrives at the Edge.
2. WAF rules evaluate the request for threats.
3. Rate limiter checks per-IP capacity.
4. Geo policy checks the resolved country.
5. Decision and latency headers are appended.
6. Event is stored in memory and streamed via WebSocket/SSE.
7. Dashboard subscribes to events for the live map and tables.
