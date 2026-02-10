# Threat Model

## In Scope
- SQL injection and XSS payload detection.
- Bot and abusive user-agent blocking.
- Rate limiting per IP.
- Geo-based allow/deny decisions.

## Out of Scope
- Advanced persistent threats.
- TLS termination and certificate management.
- Real geolocation APIs.

## Assumptions
- The edge runs locally with trusted operators.
- Attack traffic is simulated with deterministic payloads.
