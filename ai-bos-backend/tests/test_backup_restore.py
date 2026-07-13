from __future__ import annotations

import json
import sqlite3
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services import backup_service

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_backup_api_create_and_list(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path / "backups"))
    headers = auth_headers()
    create = client.post("/api/v1/platform/backups", headers=headers, json={"includeStorage": False})
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["id"].startswith("backup_")
    assert body["engine"] == "sqlite"
    assert Path(body["path"]).exists()

    listed = client.get("/api/v1/platform/backups", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == body["id"] for item in listed.json())


def test_backup_forbidden_for_staff(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path / "backups"))
    res = client.post("/api/v1/platform/backups", headers=auth_headers("staff@demo.aibos.io"))
    assert res.status_code == 403


def test_backup_restore_roundtrip(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "roundtrip.db"
    storage = tmp_path / "storage"
    storage.mkdir()
    marker = storage / "org-1" / "note.txt"
    marker.parent.mkdir(parents=True)
    marker.write_text("before-backup", encoding="utf-8")

    conn = sqlite3.connect(db_path.as_posix())
    conn.execute("CREATE TABLE demo (id TEXT PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO demo VALUES ('1', 'alpha')")
    conn.commit()
    conn.close()

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path / "backups"))
    monkeypatch.setattr(settings, "storage_local_path", str(storage))

    info = backup_service.create_backup(include_storage=True)
    assert Path(info.path).exists()
    with zipfile.ZipFile(info.path, "r") as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        assert "database/aibos.db" in names
        assert any(n.startswith("storage/") for n in names)
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["engine"] == "sqlite"

    # Corrupt live data
    conn = sqlite3.connect(db_path.as_posix())
    conn.execute("UPDATE demo SET value='corrupted'")
    conn.commit()
    conn.close()
    marker.write_text("corrupted", encoding="utf-8")

    result = backup_service.restore_backup(info.id, restore_storage=True)
    assert result["status"] == "restored"

    conn = sqlite3.connect(db_path.as_posix())
    value = conn.execute("SELECT value FROM demo WHERE id='1'").fetchone()[0]
    conn.close()
    assert value == "alpha"
    assert marker.read_text(encoding="utf-8") == "before-backup"


def test_restore_requires_confirm(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path / "backups"))
    monkeypatch.setattr(settings, "environment", "development")
    create = client.post("/api/v1/platform/backups", headers=auth_headers(), json={"includeStorage": False})
    assert create.status_code == 201
    backup_id = create.json()["id"]
    bad = client.post(
        f"/api/v1/platform/backups/{backup_id}/restore",
        headers=auth_headers(),
        json={"confirm": "nope"},
    )
    assert bad.status_code == 400
