from __future__ import annotations

import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_correlation_id_header_set() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers


def test_health_details_includes_metrics() -> None:
    response = client.get("/health/details")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "metrics" in body
    assert isinstance(body["metrics"], dict)


def test_json_log_emitted(caplog) -> None:
    caplog.set_level(logging.INFO, logger="aibos")
    client.get("/health")

    records = [r for r in caplog.records if r.name == "aibos" and r.getMessage() == "http_request"]
    assert records, "Aucun log 'http_request' n'a été émis"

    # On attend que log_event() injecte un dictionnaire structuré dans extra_fields
    payload = None
    for r in records:
        extra_fields = getattr(r, "extra_fields", None) or {}
        if extra_fields.get("event") == "http_request":
            payload = extra_fields
            break

    assert payload is not None
    assert payload.get("correlation_id")

