from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['token']}"}


def test_list_feature_flags_for_enterprise() -> None:
    res = client.get("/api/v1/platform/feature-flags", headers=headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 8
    by_key = {f["key"]: f for f in body}
    assert by_key["ai.copilot"]["enabled"] is True
    assert by_key["ml.forecasts"]["enabled"] is True
    assert by_key["analytics.advanced"]["enabled"] is True
    assert by_key["ai.copilot"]["plan"] == "enterprise"


def test_admin_flags_requires_permission() -> None:
    res = client.get("/api/v1/admin/feature-flags", headers=headers("staff@demo.aibos.io"))
    assert res.status_code == 403


def test_override_and_reset_feature_flag() -> None:
    h = headers()
    disable = client.patch(
        "/api/v1/admin/feature-flags/realtime.sync",
        headers=h,
        json={"enabled": False},
    )
    assert disable.status_code == 200
    assert disable.json()["enabled"] is False
    assert disable.json()["source"] == "override"

    enable = client.patch(
        "/api/v1/admin/feature-flags/realtime.sync",
        headers=h,
        json={"enabled": True},
    )
    assert enable.status_code == 200
    assert enable.json()["enabled"] is True

    reset = client.patch(
        "/api/v1/admin/feature-flags/realtime.sync",
        headers=h,
        json={"enabled": False, "reset": True},
    )
    assert reset.status_code == 200
    assert reset.json()["source"] in {"plan", "default"}


def test_ml_forecast_respects_feature_flag() -> None:
    h = headers()
    # Disable ml.forecasts via override
    client.patch("/api/v1/admin/feature-flags/ml.forecasts", headers=h, json={"enabled": False})
    blocked = client.get("/api/v1/ml/forecast?horizon=7d", headers=h)
    assert blocked.status_code == 403

    # Re-enable
    client.patch("/api/v1/admin/feature-flags/ml.forecasts", headers=h, json={"enabled": True})
    ok = client.get("/api/v1/ml/forecast?horizon=7d", headers=h)
    assert ok.status_code == 200

    # Reset for other tests
    client.patch(
        "/api/v1/admin/feature-flags/ml.forecasts",
        headers=h,
        json={"enabled": True, "reset": True},
    )


def test_pro_org_has_different_plan_flags() -> None:
    # org-2 plan is pro
    res = client.get("/api/v1/platform/feature-flags", headers=headers("ceo@eu.aibos.io"))
    assert res.status_code == 200
    by_key = {f["key"]: f for f in res.json()}
    assert by_key["ai.copilot"]["plan"] == "pro"
    assert by_key["module.sales"]["enabled"] is True
    assert by_key["realtime.sync"]["enabled"] is False
    assert by_key["ai.custom_agents"]["enabled"] is False
