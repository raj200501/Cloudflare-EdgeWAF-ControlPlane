from __future__ import annotations

import argparse
import random
import time

import httpx

GOOD_PATHS = ["/home", "/assets", "/api/products"]
SQLI_PAYLOADS = ["' OR 1=1 --", "union select * from users"]
XSS_PAYLOADS = ["<script>alert(1)</script>", "?q=javascript:alert(1)"]

GOOD_IPS = ["8.8.8.8", "1.1.1.1", "13.0.0.1"]
BAD_IPS = ["9.9.9.9", "10.0.0.5", "2.2.2.2", "3.3.3.3"]


def send_request(client: httpx.Client, url: str, ip: str, method: str = "GET", data=None):
    headers = {"x-forwarded-for": ip}
    return client.request(method, url, headers=headers, json=data, timeout=5.0)


def run_profile(target: str, profile: str):
    random.seed(42)
    with httpx.Client() as client:
        if profile in {"normal", "mixed"}:
            for _ in range(10):
                path = random.choice(GOOD_PATHS)
                send_request(client, f"{target}{path}", random.choice(GOOD_IPS))
                time.sleep(0.1)
        if profile in {"attack", "mixed"}:
            for payload in SQLI_PAYLOADS:
                send_request(
                    client,
                    f"{target}/login?user=admin&pass={payload}",
                    random.choice(BAD_IPS),
                    method="POST",
                    data={"username": "admin", "password": payload},
                )
            for payload in XSS_PAYLOADS:
                send_request(client, f"{target}/search?q={payload}", random.choice(BAD_IPS))
            for _ in range(20):
                send_request(client, f"{target}/api/products", random.choice(BAD_IPS))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--profile", default="mixed", choices=["normal", "attack", "mixed"])
    args = parser.parse_args()
    run_profile(args.target, args.profile)


if __name__ == "__main__":
    main()
