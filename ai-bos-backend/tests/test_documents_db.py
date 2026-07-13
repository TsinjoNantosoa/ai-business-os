from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "demo1234"},
    )
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_documents_list_from_db() -> None:
    res = client.get("/api/v1/documents", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 10
    assert any(doc["type"] == "folder" for doc in body)
    assert body[0]["type"] == "folder"


def test_document_upload_and_download() -> None:
    headers = auth_headers()
    content = b"%PDF-1.4 test document content for AI BOS"
    files = {"file": ("rapport_test.pdf", BytesIO(content), "application/pdf")}
    data = {"parentId": "doc-3"}

    upload = client.post("/api/v1/documents/upload", headers=headers, files=files, data=data)
    assert upload.status_code == 201, upload.text
    document = upload.json()
    assert document["name"] == "rapport_test.pdf"
    assert document["type"] == "pdf"
    assert document["parentId"] == "doc-3"
    assert document["hasFile"] is True
    assert document["size"] == len(content)

    download = client.get(f"/api/v1/documents/{document['id']}/download", headers=headers)
    assert download.status_code == 200
    assert download.content == content


def test_document_upload_rejects_bad_type() -> None:
    headers = auth_headers()
    files = {"file": ("malware.exe", BytesIO(b"MZ"), "application/octet-stream")}
    res = client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert res.status_code == 400
