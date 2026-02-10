from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class TokenBucketConfig:
    rate_per_sec: float
    burst: int
    ttl_seconds: int = 60


class InMemoryTokenBucket:
    def __init__(self, config: TokenBucketConfig, time_fn: Callable[[], float] | None = None):
        self.config = config
        self.time_fn = time_fn or time.time
        self._state: Dict[str, dict[str, float]] = {}

    def allow(self, key: str) -> bool:
        now = self.time_fn()
        state = self._state.get(key)
        if not state:
            state = {"tokens": float(self.config.burst), "last": now}
            self._state[key] = state
        elapsed = now - state["last"]
        state["last"] = now
        state["tokens"] = min(
            float(self.config.burst),
            state["tokens"] + elapsed * self.config.rate_per_sec,
        )
        if state["tokens"] >= 1:
            state["tokens"] -= 1
            return True
        return False

    def purge_expired(self) -> None:
        now = self.time_fn()
        expired = [
            key
            for key, state in self._state.items()
            if now - state["last"] > self.config.ttl_seconds
        ]
        for key in expired:
            self._state.pop(key, None)
