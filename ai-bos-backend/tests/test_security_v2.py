from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.workflow_actions import execute_call_api, validate_outbound_url

client = TestClient(app)


def _headers() -> dict[str, str]:
    login = client.post("/api/v1/auth/login", json={"email": "ceo@demo.aibos.io", "password": "demo1234"})
    return {"Authorization": f"Bearer {login.json()['token']}"}


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/admin",
        "http://127.0.0.1/latest/meta-data",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.1/internal",
        "http://192.168.1.10/internal",
        "ftp://example.com/file",
    ],
)
def test_workflow_http_blocks_ssrf(url: str) -> None:
    with pytest.raises(ValueError):
        validate_outbound_url(url)


def test_api_key_cannot_request_admin_or_wildcard_scope() -> None:
    for scope in ("*", "settings.org", "ai.approval.decide", "admin.audit"):
        response = client.post(
            "/api/v1/platform/api-keys",
            headers=_headers(),
            json={"name": "forbidden", "scopes": [scope]},
        )
        assert response.status_code == 422


def test_tenant_header_cannot_override_token_tenant() -> None:
    response = client.get(
        "/api/v1/crm/contacts",
        headers={**_headers(), "X-Tenant-Id": "org-2"},
    )
    assert response.status_code == 403


def test_workflow_http_retries_5xx_but_not_4xx(monkeypatch) -> None:
    monkeypatch.setattr("socket.getaddrinfo", lambda *args: [(None, None, None, None, ("93.184.216.34", 443))])
    statuses = [503, 503, 200]

    class Response:
        def __init__(self, status_code: int) -> None:
            self.status_code = status_code
            self.text = "ok"

    class Client:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def request(self, *args, **kwargs):
            return Response(statuses.pop(0))

    monkeypatch.setattr("app.services.workflow_actions.httpx.Client", Client)
    result = execute_call_api(None, org_id="org-1", context={"url": "https://example.com/hook"}, workflow_name="retry")
    assert result.ok is True
    assert result.attempts == 3

    statuses[:] = [400, 200]
    failed = execute_call_api(None, org_id="org-1", context={"url": "https://example.com/hook"}, workflow_name="no-retry")
    assert failed.ok is False
    assert failed.attempts == 1
    assert statuses == [200]
