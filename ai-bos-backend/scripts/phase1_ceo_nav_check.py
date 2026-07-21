"""Validate Phase 1 CEO navigation visibility against live API."""
from __future__ import annotations

import json
import urllib.request

BASE = "http://127.0.0.1:8000"

NAV = [
    ("Marketing", "marketing.campaign.read"),
    ("Payments", "finance.payment.read"),
    ("Projects", "project.read"),
    ("Calendar", "calendar.read"),
    ("Meetings", "meeting.read"),
    ("Inventory", "inventory.read"),
    ("Procurement", "inventory.read"),
    ("Employees", "hr.employee.read"),
    ("Recruitment", "hr.recruitment.read"),
    ("Payroll", "hr.employee.read"),
    ("Leaves", "hr.leave.read"),
    ("Contracts", "contract.read"),
    ("Knowledge", "knowledge.read"),
    ("Forecasts", "ml.forecast.read"),
    ("Profile", "settings.profile"),
    ("Notifications", "settings.profile"),
]


def login(email: str) -> dict:
    req = urllib.request.Request(
        BASE + "/api/v1/auth/login",
        data=json.dumps({"email": email, "password": "demo1234"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())["user"]


def can(user: dict, perm: str) -> bool:
    if user.get("role") in {"owner", "admin"}:
        return True
    return perm in (user.get("permissions") or [])


def main() -> None:
    ceo = login("ceo@demo.aibos.io")
    staff = login("staff@demo.aibos.io")
    print(f"CEO role={ceo['role']} jwt_perms={len(ceo.get('permissions') or [])}")
    hidden = []
    for name, perm in NAV:
        ok = can(ceo, perm)
        print(f"  CEO {name:14} {'OK' if ok else 'HIDDEN'}")
        if not ok:
            hidden.append(name)
    print(f"STAFF knowledge={can(staff, 'knowledge.read')} payments={can(staff, 'finance.payment.read')} admin={can(staff, 'admin.audit')}")
    if hidden:
        raise SystemExit(f"PHASE1 FAIL hidden={hidden}")
    print("PHASE1 OK — CEO sees all required nav permissions")


if __name__ == "__main__":
    main()
