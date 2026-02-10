from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, Optional

import httpx
from fastapi import Body, FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse

from packages.limiter import InMemoryTokenBucket, TokenBucketConfig
from packages.rules_engine import RuleEngine

app = FastAPI(title="IronShield Edge")

ORIGIN_URL = "http://localhost:8081"
RULES_PATH = Path("packages/rules_engine/rules/default.json")
GEO_PATH = Path("apps/edge/geo.json")

rule_engine = RuleEngine.from_json(RULES_PATH)

EVENT_TTL_SECONDS = 120
EVENTS_MAX = 500
_events: Deque[dict[str, Any]] = deque(maxlen=EVENTS_MAX)
_ws_clients: set[WebSocket] = set()
_under_attack = False


class EventStore:
    def __init__(self) -> None:
        self._events = _events

    def add(self, event: dict[str, Any]) -> None:
        self._events.appendleft(event)

    def recent(self) -> list[dict[str, Any]]:
        cutoff = time.time() - EVENT_TTL_SECONDS
        return [event for event in list(self._events) if event["ts"] >= cutoff]


store = EventStore()


class GeoPolicy:
    def __init__(self, mapping: dict[str, str]):
        self.mapping = mapping
        self.denylist: set[str] = set()

    @classmethod
    def from_json(cls, path: Path) -> "GeoPolicy":
        data = json.loads(path.read_text())
        return cls(data)

    def resolve_country(self, ip: str) -> str:
        first_octet = ip.split(".")[0]
        return self.mapping.get(first_octet, "Unknown")

    def allow(self, country: str) -> bool:
        return country not in self.denylist


geo_policy = GeoPolicy.from_json(GEO_PATH)


class LimiterManager:
    def __init__(self) -> None:
        self.normal = InMemoryTokenBucket(TokenBucketConfig(rate_per_sec=5, burst=10))
        self.attack = InMemoryTokenBucket(TokenBucketConfig(rate_per_sec=2, burst=4))

    def allow(self, ip: str, under_attack: bool) -> bool:
        bucket = self.attack if under_attack else self.normal
        bucket.purge_expired()
        return bucket.allow(ip)


limiter = LimiterManager()


async def publish_event(event: dict[str, Any]) -> None:
    store.add(event)
    living = set()
    for ws in _ws_clients:
        try:
            await ws.send_json(event)
            living.add(ws)
        except WebSocketDisconnect:
            continue
    _ws_clients.clear()
    _ws_clients.update(living)


@app.get("/api/events/recent")
async def recent_events() -> dict[str, Any]:
    return {"events": store.recent()}


@app.get("/api/events/stream")
async def stream_events():
    async def event_generator():
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        async def watcher():
            while True:
                await asyncio.sleep(0.5)
                if _events:
                    await queue.put(_events[0])

        task = asyncio.create_task(watcher())
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            task.cancel()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    _ws_clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        _ws_clients.discard(ws)


@app.post("/api/config/under_attack")
async def toggle_under_attack(payload: dict = Body(...)) -> dict[str, Any]:
    global _under_attack
    _under_attack = bool(payload.get("enabled"))
    return {"under_attack": _under_attack}


@app.post("/api/config/geo_denylist")
async def update_geo_denylist(payload: dict = Body(...)) -> dict[str, Any]:
    denylist = payload.get("denylist", [])
    geo_policy.denylist = set(denylist)
    return {"denylist": sorted(geo_policy.denylist)}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request):
    started = time.perf_counter()
    client_ip = request.headers.get("x-forwarded-for", request.client.host)
    body = await request.body()
    query_string = request.url.query
    headers = dict(request.headers)
    country = geo_policy.resolve_country(client_ip)

    waf_start = time.perf_counter()
    waf_match = rule_engine.evaluate(
        {
            "path": f"/{path}",
            "query": query_string,
            "body": body.decode("utf-8", errors="ignore"),
            "headers": headers,
            "method": request.method,
        }
    )
    waf_duration = (time.perf_counter() - waf_start) * 1000

    rl_start = time.perf_counter()
    rate_allowed = limiter.allow(client_ip, _under_attack)
    rl_duration = (time.perf_counter() - rl_start) * 1000

    geo_start = time.perf_counter()
    geo_allowed = geo_policy.allow(country)
    geo_duration = (time.perf_counter() - geo_start) * 1000

    decision = "allow"
    reason = "ok"
    threat_type = None
    status_code = 200

    strict_triggered = _under_attack and any(
        token in query_string.lower() for token in ["select", "drop", "<script", "onerror="]
    )

    if waf_match.action == "block" or strict_triggered:
        decision = "block"
        reason = waf_match.reason if waf_match.action == "block" else "strict"
        threat_type = waf_match.threat_type if waf_match.action == "block" else "under-attack"
        status_code = 403
    elif not rate_allowed:
        decision = "block"
        reason = "rate"
        threat_type = "rate-limit"
        status_code = 429
    elif not geo_allowed:
        decision = "block"
        reason = "geo"
        threat_type = "geo-block"
        status_code = 451

    proxy_start = time.perf_counter()
    response_content = {"detail": "blocked"}
    response_headers: Dict[str, str] = {}
    media_type: Optional[str] = None
    if decision == "allow":
        async with httpx.AsyncClient() as client:
            upstream = f"{ORIGIN_URL}/{path}"
            upstream_response = await client.request(
                request.method,
                upstream,
                params=request.query_params,
                headers=headers,
                content=body,
                timeout=10.0,
            )
            response_content = upstream_response.content
            response_headers = dict(upstream_response.headers)
            media_type = upstream_response.headers.get("content-type")
            status_code = upstream_response.status_code
    proxy_duration = (time.perf_counter() - proxy_start) * 1000

    total_latency = (time.perf_counter() - started) * 1000
    event = {
        "ts": time.time(),
        "ip": client_ip,
        "country": country,
        "method": request.method,
        "path": f"/{path}",
        "status": status_code,
        "decision": decision,
        "reason": reason,
        "threat_type": threat_type,
        "latency_ms": round(total_latency, 2),
    }
    await publish_event(event)

    headers_out = {
        "x-ironshield-decision": decision,
        "x-ironshield-reason": reason,
        "server-timing": (
            f"waf;dur={waf_duration:.2f}, "
            f"ratelimit;dur={rl_duration:.2f}, "
            f"geo;dur={geo_duration:.2f}, "
            f"proxy;dur={proxy_duration:.2f}"
        ),
    }
    headers_out.update(response_headers)
    if decision == "allow":
        return Response(
            content=response_content,
            status_code=status_code,
            headers=headers_out,
            media_type=media_type,
        )
    return JSONResponse(content=response_content, status_code=status_code, headers=headers_out)
