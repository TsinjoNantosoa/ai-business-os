from __future__ import annotations

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
    assert body["database"] == "ok"
    assert "metrics" in body
    assert isinstance(body["metrics"], dict)


def test_http_request_increments_metrics() -> None:
    before = client.get("/health/details").json()["metrics"].get("http_requests", 0)
    response = client.get("/health")
    assert response.status_code == 200
    after = client.get("/health/details").json()["metrics"].get("http_requests", 0)
    assert after > before

