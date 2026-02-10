from __future__ import annotations

import argparse
import random
import threading
import time

import httpx


def build_profiles() -> list[dict[str, str]]:
    return [
        {"method": "GET", "path": "/home"},
        {"method": "GET", "path": "/assets/logo.svg"},
        {"method": "POST", "path": "/login", "data": "username=alice&password=hunter2"},
        {"method": "GET", "path": "/search?q=' OR 1=1 --"},
        {"method": "GET", "path": "/comment?text=<script>alert(1)</script>"},
        {"method": "GET", "path": "/api/data"},
    ]


def fire(target: str, duration: int, seed: int, workers: int = 4):
    stop_at = time.time() + duration
    octets = [1, 2, 8, 21, 44, 88, 101, 121]
    ip_pool = [f"{octet}.10.0.{host}" for octet in octets for host in range(1, 30)]

    def worker(offset: int):
        rnd = random.Random(seed + offset)
        with httpx.Client(timeout=2.0) as client:
            while time.time() < stop_at:
                req = rnd.choice(build_profiles())
                ip = rnd.choice(ip_pool)
                headers = {
                    "x-forwarded-for": ip,
                    "user-agent": rnd.choice(
                        [
                            "Mozilla/5.0",
                            "python-requests/2.31",
                            "curl/8.0",
                            "sqlmap/1.8",
                            "EvilBot/4.2",
                        ]
                    ),
                }
                method = req["method"]
                url = f"{target}{req['path']}"
                try:
                    client.request(method, url, data=req.get("data", ""), headers=headers)
                except Exception:
                    pass
                time.sleep(rnd.uniform(0.005, 0.08))

    threads = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic local attacker simulator")
    parser.add_argument("--target", default="http://localhost:8000")
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    fire(args.target, args.duration, args.seed, args.workers)
