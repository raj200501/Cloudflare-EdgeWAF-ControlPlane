from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class WafRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    field: str
    operator: str
    pattern: str
    action: str = "block"
    reason: str
    threat_type: str = "waf"
    priority: int = 100


class RateLimitPolicy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    rate_per_sec: float
    burst: int


class GeoPolicyModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    allow: list[str] = Field(default_factory=list)
    deny: list[str] = Field(default_factory=list)


class BotPolicy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    blocked_user_agents: list[str] = Field(default_factory=list)
    challenge_mode: bool = False


class Snapshot(BaseModel):
    id: str
    created_at: str
    hash: str
    bundle: dict[str, Any]
    etag: str


class ControlPlane:
    def __init__(self):
        self.waf_rules: dict[str, WafRule] = {}
        self.rate_policies: dict[str, RateLimitPolicy] = {}
        self.geo_policies: dict[str, GeoPolicyModel] = {}
        self.bot_policies: dict[str, BotPolicy] = {}
        self.snapshots: dict[str, Snapshot] = {}
        self.active_snapshot_id: str | None = None

    def _hash_bundle(self, bundle: dict[str, Any]) -> str:
        canonical = json.dumps(bundle, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def build_bundle(self) -> dict[str, Any]:
        return {
            "waf": [
                item.model_dump()
                for item in sorted(self.waf_rules.values(), key=lambda x: x.priority)
            ],
            "rate": [item.model_dump() for item in self.rate_policies.values()],
            "geo": [item.model_dump() for item in self.geo_policies.values()],
            "bot": [item.model_dump() for item in self.bot_policies.values()],
        }

    def compile_snapshot(self) -> Snapshot:
        bundle = self.build_bundle()
        digest = self._hash_bundle(bundle)
        snapshot_id = str(uuid4())
        snapshot = Snapshot(
            id=snapshot_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            hash=digest,
            bundle=bundle,
            etag=f'W/"{digest[:16]}"',
        )
        self.snapshots[snapshot_id] = snapshot
        return snapshot

    def activate(self, snapshot_id: str) -> Snapshot:
        if snapshot_id not in self.snapshots:
            raise KeyError(snapshot_id)
        self.active_snapshot_id = snapshot_id
        return self.snapshots[snapshot_id]

    def active(self) -> Snapshot | None:
        if not self.active_snapshot_id:
            return None
        return self.snapshots[self.active_snapshot_id]


def paginate(items: list[Any], page: int, page_size: int) -> dict[str, Any]:
    total = len(items)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
