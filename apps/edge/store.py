from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass
class EventRecord:
    id: str
    ts: float
    decision: str
    reason: str
    ip: str
    country: str
    path: str
    method: str
    status_code: int
    latency_ms: float
    timings: dict[str, float]
    threat_type: str | None = None


class StateBackend(ABC):
    @abstractmethod
    def put_json(self, key: str, payload: dict[str, Any]) -> None: ...

    @abstractmethod
    def get_json(self, key: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def append_event(self, event: EventRecord) -> None: ...

    @abstractmethod
    def recent_events(self, limit: int = 500) -> list[dict[str, Any]]: ...


class InMemoryStateBackend(StateBackend):
    def __init__(self, max_events: int = 1000):
        self.kv: dict[str, dict[str, Any]] = {}
        self.events = deque(maxlen=max_events)

    def put_json(self, key: str, payload: dict[str, Any]) -> None:
        self.kv[key] = payload

    def get_json(self, key: str) -> dict[str, Any] | None:
        return self.kv.get(key)

    def append_event(self, event: EventRecord) -> None:
        self.events.appendleft(event.__dict__)

    def recent_events(self, limit: int = 500) -> list[dict[str, Any]]:
        return list(self.events)[:limit]


class RedisStateBackend(StateBackend):
    def __init__(self, redis_client: Any, prefix: str = "ironshield"):
        self.redis = redis_client
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def put_json(self, key: str, payload: dict[str, Any]) -> None:
        self.redis.set(self._key(key), json.dumps(payload))

    def get_json(self, key: str) -> dict[str, Any] | None:
        raw = self.redis.get(self._key(key))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def append_event(self, event: EventRecord) -> None:
        self.redis.lpush(self._key("events"), json.dumps(event.__dict__))
        self.redis.ltrim(self._key("events"), 0, 999)

    def recent_events(self, limit: int = 500) -> list[dict[str, Any]]:
        payloads = self.redis.lrange(self._key("events"), 0, limit - 1)
        events = []
        for item in payloads:
            if isinstance(item, bytes):
                item = item.decode("utf-8")
            events.append(json.loads(item))
        return events


def make_state_backend() -> StateBackend:
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        try:
            import redis  # type: ignore

            client = redis.from_url(redis_url, socket_connect_timeout=0.3)
            client.ping()
            return RedisStateBackend(client)
        except Exception:
            pass
    return InMemoryStateBackend()


def stable_ts() -> float:
    return time.time()
