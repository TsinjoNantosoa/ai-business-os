"""Fallback smoke load test without k6 (httpx).

Usage (API running on :8000):
  python tests/perf/smoke_httpx.py
"""
from __future__ import annotations

import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

BASE = os.getenv("API_URL", "http://127.0.0.1:8000")
EMAIL = os.getenv("EMAIL", "ceo@demo.aibos.io")
PASSWORD = os.getenv("PASSWORD", "demo1234")
WORKERS = int(os.getenv("VUS", "8"))
ROUNDS = int(os.getenv("ROUNDS", "5"))


def login(client: httpx.Client) -> str:
    res = client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    res.raise_for_status()
    body = res.json()
    return body.get("token") or body["accessToken"]


def one_round(token: str) -> dict[str, float]:
    headers = {"Authorization": f"Bearer {token}", "X-Correlation-ID": f"py-{time.time_ns()}"}
    timings: dict[str, float] = {}
    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        for name, path in (
            ("health", "/health"),
            ("contacts", "/api/v1/crm/contacts"),
            ("kpis", "/api/v1/analytics/kpis"),
        ):
            t0 = time.perf_counter()
            res = client.get(path, headers=None if name == "health" else headers)
            timings[name] = (time.perf_counter() - t0) * 1000
            if res.status_code != 200:
                raise RuntimeError(f"{name} -> {res.status_code} {res.text[:200]}")
        t0 = time.perf_counter()
        res = client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
        timings["login"] = (time.perf_counter() - t0) * 1000
        if res.status_code != 200:
            raise RuntimeError(f"login -> {res.status_code}")
    return timings


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        health = client.get("/health")
        health.raise_for_status()
        token = login(client)

    samples: dict[str, list[float]] = {"health": [], "contacts": [], "kpis": [], "login": []}
    errors = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(one_round, token) for _ in range(WORKERS * ROUNDS)]
        for fut in as_completed(futures):
            try:
                timings = fut.result()
                for k, v in timings.items():
                    samples[k].append(v)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                print(f"error: {exc}")

    total = WORKERS * ROUNDS
    print(f"API={BASE} workers={WORKERS} rounds={ROUNDS} ok={total - errors}/{total}")
    for name, vals in samples.items():
        if not vals:
            continue
        p95 = sorted(vals)[max(0, int(len(vals) * 0.95) - 1)]
        print(
            f"  {name:8s} n={len(vals):3d} mean={statistics.mean(vals):7.1f}ms "
            f"p95={p95:7.1f}ms max={max(vals):7.1f}ms"
        )
    if errors:
        raise SystemExit(1)
    print("smoke_httpx OK")


if __name__ == "__main__":
    main()
