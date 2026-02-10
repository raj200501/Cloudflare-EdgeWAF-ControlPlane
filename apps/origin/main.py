from __future__ import annotations

import random
import time

from fastapi import FastAPI, Request

app = FastAPI(title="Origin Simulator")


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def origin(path: str, request: Request):
    start = time.perf_counter()
    body = await request.body()
    random.seed(path)
    jitter = random.random() * 0.02
    time.sleep(jitter)
    latency_ms = (time.perf_counter() - start) * 1000
    return {
        "ok": True,
        "path": f"/{path}",
        "method": request.method,
        "payload_size": len(body),
        "latency_ms": round(latency_ms, 2),
    }
