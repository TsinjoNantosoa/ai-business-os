"""Smoke audit: login as CEO and probe all frontend-backed APIs + nav permission gaps."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
CHATBOT = "2856e2980204a7db0278471c7c13b175c1cf7f7a9e6e4613759cc13c08ae9f37"


def req(method: str, path: str, token: str | None = None, data=None, extra=None, timeout: int = 45):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra:
        headers.update(extra)
    body = None if data is None else json.dumps(data).encode()
    request = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            raw = resp.read()
            ctype = resp.headers.get("content-type", "")
            payload = None
            if raw and "application/json" in ctype:
                payload = json.loads(raw.decode())
            elif raw and "text/event-stream" in ctype:
                payload = raw.decode(errors="ignore")[:800]
            elif raw:
                payload = raw.decode(errors="ignore")[:200]
            return resp.status, payload, None
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode(errors="ignore")[:300]
        except Exception:
            detail = str(exc)
        return exc.code, None, detail
    except Exception as exc:  # noqa: BLE001
        return 0, None, str(exc)


def main() -> None:
    st, body, err = req("GET", "/health")
    print(f"HEALTH {st} {body or err}")
    st, body, err = req("GET", "/health/details")
    env = body.get("environment") if isinstance(body, dict) else err
    print(f"HEALTH_DETAILS {st} env={env}")

    st, body, err = req(
        "POST",
        "/api/v1/auth/login",
        data={"email": "ceo@demo.aibos.io", "password": "demo1234"},
    )
    if st != 200 or not isinstance(body, dict):
        print("LOGIN FAIL", st, err)
        raise SystemExit(1)
    token = body["token"]
    user = body.get("user") or {}
    perms = set(user.get("permissions") or [])
    print(f"LOGIN OK role={user.get('role')} perms={len(perms)}")

    nav_perms = {
        "/app/dashboard": None,
        "/app/copilot": "ai.copilot.use",
        "/app/inbox": None,
        "/app/crm/contacts": "crm.contact.read",
        "/app/crm/pipeline": "crm.lead.read",
        "/app/sales/orders": "sales.order.read",
        "/app/marketing/campaigns": "marketing.campaign.read",
        "/app/finance": "finance.invoice.read",
        "/app/finance/invoices": "finance.invoice.read",
        "/app/finance/payments": "finance.payment.read",
        "/app/finance/accounting": "finance.invoice.read",
        "/app/finance/reports": "finance.invoice.read",
        "/app/projects": "project.read",
        "/app/tasks": "task.read",
        "/app/calendar": "calendar.read",
        "/app/meetings": "meeting.read",
        "/app/documents": "document.read",
        "/app/inventory": "inventory.read",
        "/app/procurement": "inventory.read",
        "/app/hr/employees": "hr.employee.read",
        "/app/hr/org-chart": "hr.employee.read",
        "/app/hr/recruitment": "hr.recruitment.read",
        "/app/hr/payroll": "hr.employee.read",
        "/app/support/tickets": "support.ticket.read",
        "/app/contracts": "contract.read",
        "/app/knowledge": "knowledge.read",
        "/app/analytics": "analytics.read",
        "/app/bi": "bi.read",
        "/app/forecasts": "ml.forecast.read",
        "/app/workflows": "workflow.read",
        "/app/agents": "ai.agent.use",
        "/app/settings/profile": "settings.profile",
        "/app/settings/organization": "settings.org",
        "/app/settings/team": "settings.team",
        "/app/settings/billing": "settings.billing",
        "/app/settings/integrations": "settings.org",
        "/app/settings/notifications": "settings.profile",
        "/app/settings/api-keys": "settings.org",
        "/app/admin/audit": "admin.audit",
        "/app/admin/flags": "admin.flags",
    }

    print("\n=== NAV PERMISSION GAPS (CEO) ===")
    hidden: list[tuple[str, str]] = []
    for path, need in nav_perms.items():
        if not need:
            continue
        if path == "/app/sales/orders" and ("crm.contact.read" in perms or "sales.order.read" in perms):
            continue
        if need not in perms:
            hidden.append((path, need))
            print(f"HIDDEN {path} needs {need}")
    if not hidden:
        print("(none)")

    endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/platform/organizations"),
        ("GET", "/api/v1/platform/organizations/me"),
        ("GET", "/api/v1/platform/team"),
        ("GET", "/api/v1/platform/invitations"),
        ("GET", "/api/v1/platform/notifications"),
        ("GET", "/api/v1/platform/feature-flags"),
        ("GET", "/api/v1/admin/feature-flags"),
        ("GET", "/api/v1/platform/api-keys"),
        ("GET", "/api/v1/platform/audit-logs"),
        ("GET", "/api/v1/platform/backups"),
        ("GET", "/api/v1/platform/gdpr/export"),
        ("GET", "/api/v1/crm/contacts"),
        ("GET", "/api/v1/crm/leads"),
        ("GET", "/api/v1/crm/activities"),
        ("GET", "/api/v1/sales/orders"),
        ("GET", "/api/v1/marketing/campaigns"),
        ("GET", "/api/v1/finance/overview"),
        ("GET", "/api/v1/finance/invoices"),
        ("GET", "/api/v1/finance/transactions"),
        ("GET", "/api/v1/projects"),
        ("GET", "/api/v1/tasks"),
        ("GET", "/api/v1/calendar/events"),
        ("GET", "/api/v1/meetings"),
        ("GET", "/api/v1/documents"),
        ("GET", "/api/v1/inventory/items"),
        ("GET", "/api/v1/procurement/suppliers"),
        ("GET", "/api/v1/procurement/purchase-orders"),
        ("GET", "/api/v1/hr/employees"),
        ("GET", "/api/v1/hr/jobs"),
        ("GET", "/api/v1/hr/candidates"),
        ("GET", "/api/v1/support/tickets"),
        ("GET", "/api/v1/contracts"),
        ("GET", "/api/v1/knowledge/articles"),
        ("GET", "/api/v1/knowledge/search?q=RAG"),
        ("GET", "/api/v1/knowledge/stats"),
        ("GET", "/api/v1/workflows"),
        ("GET", "/api/v1/workflows/executions"),
        ("GET", "/api/v1/ai/agents"),
        ("GET", "/api/v1/analytics/kpis"),
        ("GET", "/api/v1/bi/reports"),
        ("GET", "/api/v1/ml/forecast?horizon=30d"),
        ("GET", "/api/v1/billing/overview"),
        ("GET", "/api/v1/billing/plans"),
        ("GET", "/api/v1/auth/oauth/providers"),
    ]

    print("\n=== API ENDPOINT STATUS ===")
    ok = fail = 0
    fails: list[str] = []
    for method, path in endpoints:
        st, body, err = req(method, path, token=token)
        count = None
        if isinstance(body, list):
            count = len(body)
        elif isinstance(body, dict) and "items" in body and isinstance(body["items"], list):
            count = len(body["items"])
        elif isinstance(body, dict) and "chunkCount" in body:
            count = body["chunkCount"]
        status = "OK" if 200 <= st < 300 else "FAIL"
        if status == "OK":
            ok += 1
        else:
            fail += 1
            fails.append(f"{st} {method} {path} :: {err}")
        extra = f" n={count}" if count is not None else ""
        detail = "" if status == "OK" else f" | {(err or '')[:120]}"
        print(f"{status:4} {st:3} {method:4} {path}{extra}{detail}")

    print("\n=== COPILOT CHAT ===")
    st, body, err = req(
        "POST",
        "/api/v1/ai/chat",
        token=token,
        data={"message": "Qu'est-ce que le RAG AI BOS?", "agentId": "ceo", "context": "Copilot"},
        extra={"X-Chatbot-Token": CHATBOT},
        timeout=90,
    )
    print(f"CHAT {st} {'OK' if st == 200 else err}")
    if isinstance(body, str):
        print(f"  has_chunk={'chunk' in body} has_sources={'sources' in body}")
        print("  preview:", body[:220].replace("\n", " "))

    print("\n=== FRONTEND ===")
    st, body, err = req("GET", "http://localhost:5173/".replace(BASE, ""), timeout=10)  # unused
    # probe frontend separately
    try:
        with urllib.request.urlopen("http://localhost:5173/", timeout=10) as resp:
            print(f"FRONTEND {resp.status}")
    except Exception as exc:  # noqa: BLE001
        print(f"FRONTEND FAIL {exc}")

    print(f"\nSUMMARY api_ok={ok} api_fail={fail} nav_hidden={len(hidden)}")
    if fails:
        print("FAILS:")
        for line in fails:
            print(" -", line)


if __name__ == "__main__":
    main()
