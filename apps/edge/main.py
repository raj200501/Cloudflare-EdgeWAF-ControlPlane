from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import (
    Body,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.edge.control_plane import (
    BotPolicy,
    ControlPlane,
    GeoPolicyModel,
    RateLimitPolicy,
    WafRule,
    paginate,
)
from apps.edge.store import EventRecord, make_state_backend
from packages.limiter import InMemoryTokenBucket, TokenBucketConfig
from packages.rules_engine import RuleEngine

app = FastAPI(title="IronShield Edge & Control Plane", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ORIGIN_URL = "http://localhost:8081"
RULES_PATH = Path("packages/rules_engine/rules/default.json")
GEO_PATH = Path("apps/edge/geo.json")

state = make_state_backend()
control = ControlPlane()
rule_engine = RuleEngine.from_json(RULES_PATH)
_events_ws_clients: set[WebSocket] = set()
_under_attack = False


def load_geo() -> dict[str, str]:
    return json.loads(GEO_PATH.read_text())


geo_map = load_geo()
geo_denylist: set[str] = set()


class LimiterManager:
    def __init__(self) -> None:
        self.normal = InMemoryTokenBucket(TokenBucketConfig(rate_per_sec=6, burst=12))
        self.attack = InMemoryTokenBucket(TokenBucketConfig(rate_per_sec=2, burst=4))

    def allow(self, ip: str, under_attack: bool) -> bool:
        bucket = self.attack if under_attack else self.normal
        bucket.purge_expired()
        return bucket.allow(ip)


limiter = LimiterManager()


async def publish_event(event: EventRecord) -> None:
    state.append_event(event)
    stale: list[WebSocket] = []
    for client in _events_ws_clients:
        try:
            await client.send_json(event.__dict__)
        except WebSocketDisconnect:
            stale.append(client)
    for item in stale:
        _events_ws_clients.discard(item)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/events")
def list_events(limit: int = Query(default=500, ge=1, le=2000)) -> dict[str, Any]:
    return {"items": state.recent_events(limit=limit)}


@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    _events_ws_clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        _events_ws_clients.discard(ws)


@app.post("/api/config/under_attack")
def under_attack(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    global _under_attack
    _under_attack = bool(payload.get("enabled", False))
    return {"under_attack": _under_attack}


@app.post("/api/config/geo_denylist")
def set_geo(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    global geo_denylist
    geo_denylist = set(payload.get("denylist", []))
    return {"denylist": sorted(geo_denylist)}


@app.get("/api/policies/waf")
def list_waf(page: int = 1, page_size: int = 20):
    return paginate([i.model_dump() for i in control.waf_rules.values()], page, page_size)


@app.post("/api/policies/waf")
def create_waf(policy: WafRule):
    control.waf_rules[policy.id] = policy
    return policy


@app.put("/api/policies/waf/{policy_id}")
def update_waf(policy_id: str, policy: WafRule):
    control.waf_rules[policy_id] = policy.model_copy(update={"id": policy_id})
    return control.waf_rules[policy_id]


@app.delete("/api/policies/waf/{policy_id}")
def delete_waf(policy_id: str):
    control.waf_rules.pop(policy_id, None)
    return Response(status_code=204)


@app.get("/api/policies/rate")
def list_rate(page: int = 1, page_size: int = 20):
    return paginate([i.model_dump() for i in control.rate_policies.values()], page, page_size)


@app.post("/api/policies/rate")
def create_rate(policy: RateLimitPolicy):
    control.rate_policies[policy.id] = policy
    return policy


@app.put("/api/policies/rate/{policy_id}")
def update_rate(policy_id: str, policy: RateLimitPolicy):
    control.rate_policies[policy_id] = policy.model_copy(update={"id": policy_id})
    return control.rate_policies[policy_id]


@app.delete("/api/policies/rate/{policy_id}")
def delete_rate(policy_id: str):
    control.rate_policies.pop(policy_id, None)
    return Response(status_code=204)


@app.get("/api/policies/geo")
def list_geo(page: int = 1, page_size: int = 20):
    return paginate([i.model_dump() for i in control.geo_policies.values()], page, page_size)


@app.post("/api/policies/geo")
def create_geo(policy: GeoPolicyModel):
    control.geo_policies[policy.id] = policy
    return policy


@app.put("/api/policies/geo/{policy_id}")
def update_geo(policy_id: str, policy: GeoPolicyModel):
    control.geo_policies[policy_id] = policy.model_copy(update={"id": policy_id})
    return control.geo_policies[policy_id]


@app.delete("/api/policies/geo/{policy_id}")
def delete_geo(policy_id: str):
    control.geo_policies.pop(policy_id, None)
    return Response(status_code=204)


@app.get("/api/policies/bot")
def list_bot(page: int = 1, page_size: int = 20):
    return paginate([i.model_dump() for i in control.bot_policies.values()], page, page_size)


@app.post("/api/policies/bot")
def create_bot(policy: BotPolicy):
    control.bot_policies[policy.id] = policy
    return policy


@app.put("/api/policies/bot/{policy_id}")
def update_bot(policy_id: str, policy: BotPolicy):
    control.bot_policies[policy_id] = policy.model_copy(update={"id": policy_id})
    return control.bot_policies[policy_id]


@app.delete("/api/policies/bot/{policy_id}")
def delete_bot(policy_id: str):
    control.bot_policies.pop(policy_id, None)
    return Response(status_code=204)


@app.post("/api/deployments/compile")
def compile_snapshot():
    snap = control.compile_snapshot()
    state.put_json(f"snapshot:{snap.id}", snap.model_dump())
    return snap


@app.post("/api/deployments/activate/{snapshot_id}")
def activate_snapshot(snapshot_id: str):
    try:
        snap = control.activate(snapshot_id)
    except KeyError as exc:
        raise HTTPException(404, "snapshot_not_found") from exc
    state.put_json("active_snapshot", snap.model_dump())
    return snap


@app.get("/api/deployments/active")
def active_snapshot():
    snap = control.active()
    if not snap:
        return JSONResponse({"detail": "none"}, status_code=404)
    return snap


def resolve_country(ip: str) -> str:
    return geo_map.get(ip.split(".")[0], "Unknown")


def geo_allowed(country: str) -> bool:
    if country in geo_denylist:
        return False
    for policy in control.geo_policies.values():
        if policy.allow and country not in policy.allow:
            return False
        if country in policy.deny:
            return False
    return True


def bot_allowed(headers: dict[str, str]) -> tuple[bool, str]:
    ua = headers.get("user-agent", "")
    for policy in control.bot_policies.values():
        for blocked in policy.blocked_user_agents:
            if blocked.lower() in ua.lower():
                if policy.challenge_mode:
                    return False, "bot_challenge"
                return False, "bot_blocked"
    return True, "ok"


@app.api_route("/origin/{path:path}", methods=["GET", "POST"])
async def origin(path: str, request: Request):
    await httpx.AsyncClient().aclose()
    start = time.perf_counter()
    body = await request.body()
    await httpx.AsyncClient().aclose()
    latency = (time.perf_counter() - start) * 1000
    return {"path": path, "size": len(body), "latency_ms": round(latency, 2), "ok": True}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def edge_proxy(path: str, request: Request):
    started = time.perf_counter()
    client_ip = request.headers.get(
        "x-forwarded-for", request.client.host if request.client else "127.0.0.1"
    )
    body = await request.body()
    headers = dict(request.headers)

    geo_start = time.perf_counter()
    country = resolve_country(client_ip)
    geo_ok = geo_allowed(country)
    geo_ms = (time.perf_counter() - geo_start) * 1000

    waf_start = time.perf_counter()
    eval_payload = {
        "path": f"/{path}",
        "query": request.url.query,
        "body": body.decode("utf-8", errors="ignore"),
        "headers": headers,
        "method": request.method,
    }
    rule_match = rule_engine.evaluate(eval_payload)
    waf_ms = (time.perf_counter() - waf_start) * 1000

    rl_start = time.perf_counter()
    rate_ok = limiter.allow(client_ip, _under_attack)
    rl_ms = (time.perf_counter() - rl_start) * 1000

    bot_start = time.perf_counter()
    bot_ok, bot_reason = bot_allowed(headers)
    bot_ms = (time.perf_counter() - bot_start) * 1000

    decision = "allow"
    reason = "ok"
    threat_type: str | None = None
    status_code = 200

    if not geo_ok:
        decision, reason, threat_type, status_code = "block", "geo", "geo-block", 451
    elif rule_match.action == "block":
        decision, reason, threat_type, status_code = (
            "block",
            rule_match.reason,
            rule_match.threat_type,
            403,
        )
    elif not rate_ok:
        decision, reason, threat_type, status_code = "block", "rate", "rate-limit", 429
    elif not bot_ok:
        decision, reason, threat_type, status_code = "block", bot_reason, "bot", 403

    origin_ms = 0.0
    content: Any = {"detail": "blocked"}
    media_type = "application/json"

    if decision == "allow":
        proxy_start = time.perf_counter()
        upstream = f"{ORIGIN_URL}/{path}"
        try:
            async with httpx.AsyncClient() as client:
                upstream_response = await client.request(
                    request.method,
                    upstream,
                    params=request.query_params,
                    headers=headers,
                    content=body,
                    timeout=5,
                )
            origin_ms = (time.perf_counter() - proxy_start) * 1000
            status_code = upstream_response.status_code
            content = upstream_response.content
            media_type = upstream_response.headers.get("content-type", "application/json")
        except httpx.HTTPError:
            origin_ms = (time.perf_counter() - proxy_start) * 1000
            status_code = 200
            content = {"ok": True, "path": f"/{path}", "fallback": True}
            media_type = "application/json"

    total_ms = (time.perf_counter() - started) * 1000
    event = EventRecord(
        id=f"evt_{int(time.time() * 1000000)}",
        ts=time.time(),
        decision=decision,
        reason=reason,
        ip=client_ip,
        country=country,
        path=f"/{path}",
        method=request.method,
        status_code=status_code,
        latency_ms=round(total_ms, 2),
        timings={
            "geo": round(geo_ms, 2),
            "waf": round(waf_ms, 2),
            "rate_limit": round(rl_ms, 2),
            "bot": round(bot_ms, 2),
            "origin": round(origin_ms, 2),
            "total": round(total_ms, 2),
        },
        threat_type=threat_type,
    )
    await publish_event(event)

    response_payload = content if isinstance(content, bytes) else json.dumps(content)
    response = Response(
        content=response_payload,
        status_code=status_code,
        media_type=media_type,
    )
    response.headers["Server-Timing"] = (
        f"geo;dur={geo_ms:.2f},waf;dur={waf_ms:.2f},"
        f"rl;dur={rl_ms:.2f},bot;dur={bot_ms:.2f},origin;dur={origin_ms:.2f}"
    )
    response.headers["X-IronShield-Decision"] = decision
    response.headers["X-IronShield-Reason"] = reason
    response.headers["X-IronShield-Country"] = country
    return response
