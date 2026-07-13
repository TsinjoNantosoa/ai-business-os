"""Backup / restore service for SQLite (and Postgres dump helper)."""
from __future__ import annotations

import json
import re
import shutil
import sqlite3
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from app.core.config import settings

MANIFEST_NAME = "manifest.json"
DB_ENTRY = "database/aibos.db"
STORAGE_PREFIX = "storage/"
SAFE_ID = re.compile(r"^backup_\d{8}_\d{6}_[a-f0-9]{8}$")


@dataclass(frozen=True)
class BackupInfo:
    id: str
    path: str
    created_at: str
    size_bytes: int
    engine: str
    includes_storage: bool


def backup_root() -> Path:
    raw = getattr(settings, "backup_dir", None) or "./backups"
    root = Path(raw)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[2] / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def storage_root() -> Path:
    path = Path(settings.storage_local_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    return path


def _sqlite_file_from_url(database_url: str) -> Path:
    # sqlite:///./aibos.db  or  sqlite:////abs/path  or sqlite:///C:/...
    assert database_url.startswith("sqlite")
    raw = database_url.split("sqlite:///", 1)[-1]
    raw = unquote(raw)
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    return path.resolve()


def _new_backup_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = datetime.now(timezone.utc).strftime("%f")[:8]
    return f"backup_{stamp}_{suffix}"


def _copy_sqlite(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        raise FileNotFoundError(f"Base SQLite introuvable: {src}")
    # Online-safe copy via SQLite backup API
    with sqlite3.connect(src.as_posix()) as source, sqlite3.connect(dest.as_posix()) as target:
        source.backup(target)


def _pg_dump_to(dest: Path) -> None:
    import os

    dest.parent.mkdir(parents=True, exist_ok=True)
    url = settings.database_url.replace("postgresql+psycopg2://", "postgresql://", 1)
    parsed = urlparse(url)
    env = {**os.environ, "PGPASSWORD": unquote(parsed.password or "")}
    cmd = [
        "pg_dump",
        "-h",
        parsed.hostname or "localhost",
        "-p",
        str(parsed.port or 5432),
        "-U",
        unquote(parsed.username or "aibos"),
        "-d",
        (parsed.path or "/aibos").lstrip("/") or "aibos",
        "-F",
        "c",
        "-f",
        dest.as_posix(),
    ]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed: {result.stderr.strip() or result.stdout.strip()}")


def create_backup(*, include_storage: bool = True) -> BackupInfo:
    backup_id = _new_backup_id()
    out_zip = backup_root() / f"{backup_id}.zip"
    work = backup_root() / f".tmp_{backup_id}"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    engine = "sqlite" if settings.is_sqlite else "postgres"
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        if settings.is_sqlite:
            db_copy = work / "aibos.db"
            _copy_sqlite(_sqlite_file_from_url(settings.database_url), db_copy)
            db_rel = DB_ENTRY
        else:
            dump = work / "aibos.dump"
            _pg_dump_to(dump)
            db_rel = "database/aibos.dump"

        manifest = {
            "id": backup_id,
            "created_at": created_at,
            "engine": engine,
            "database_url_scheme": settings.database_url.split(":", 1)[0],
            "environment": settings.environment,
            "includes_storage": include_storage,
            "app_version": "0.1.0",
            "rpo_note": "Point-in-time copy at backup creation (RPO target daily ≤ 24h)",
            "rto_note": "Restore via CLI/API then restart API (RTO target ≤ 8h corruption)",
        }
        (work / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(work / MANIFEST_NAME, MANIFEST_NAME)
            if settings.is_sqlite:
                zf.write(work / "aibos.db", db_rel)
            else:
                zf.write(work / "aibos.dump", db_rel)
            if include_storage:
                root = storage_root()
                if root.exists():
                    for path in root.rglob("*"):
                        if path.is_file():
                            arc = STORAGE_PREFIX + path.relative_to(root).as_posix()
                            zf.write(path, arc)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    return BackupInfo(
        id=backup_id,
        path=out_zip.as_posix(),
        created_at=created_at,
        size_bytes=out_zip.stat().st_size,
        engine=engine,
        includes_storage=include_storage,
    )


def list_backups() -> list[BackupInfo]:
    items: list[BackupInfo] = []
    for path in sorted(backup_root().glob("backup_*.zip"), reverse=True):
        stem = path.stem
        created = ""
        engine = "unknown"
        includes_storage = False
        try:
            with zipfile.ZipFile(path, "r") as zf:
                if MANIFEST_NAME in zf.namelist():
                    data = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
                    created = str(data.get("created_at") or "")
                    engine = str(data.get("engine") or "unknown")
                    includes_storage = bool(data.get("includes_storage"))
                    stem = str(data.get("id") or stem)
        except (OSError, zipfile.BadZipFile, json.JSONDecodeError):
            pass
        items.append(
            BackupInfo(
                id=stem,
                path=path.as_posix(),
                created_at=created or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                size_bytes=path.stat().st_size,
                engine=engine,
                includes_storage=includes_storage,
            )
        )
    return items


def resolve_backup_path(backup_id: str) -> Path:
    if not SAFE_ID.match(backup_id) and not backup_id.startswith("backup_"):
        raise ValueError("Identifiant de backup invalide")
    path = backup_root() / f"{backup_id}.zip"
    if not path.exists():
        # Allow exact stem mismatches by scanning
        for item in backup_root().glob("backup_*.zip"):
            if item.stem == backup_id:
                return item
        raise FileNotFoundError(f"Backup introuvable: {backup_id}")
    return path


def restore_backup(backup_id: str, *, restore_storage: bool = True) -> dict:
    """Restore DB (+ optional storage). Stops short of restarting the process."""
    zip_path = resolve_backup_path(backup_id)
    work = backup_root() / f".restore_{backup_id}"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(work)
            names = zf.namelist()

        manifest_path = work / MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        engine = manifest.get("engine") or ("sqlite" if (work / "database" / "aibos.db").exists() else "postgres")

        if engine == "sqlite" or (work / "database" / "aibos.db").exists():
            src_db = work / "database" / "aibos.db"
            if not src_db.exists():
                raise FileNotFoundError("aibos.db manquant dans l'archive")
            dest = _sqlite_file_from_url(settings.database_url)
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_suffix(".restore.tmp")
            if tmp.exists():
                tmp.unlink()
            shutil.copy2(src_db, tmp)
            # Windows: os.replace onto an existing locked/open file can fail — remove then move.
            if dest.exists():
                try:
                    dest.unlink()
                except PermissionError:
                    # Fallback overwrite copy if unlink blocked
                    shutil.copy2(tmp, dest)
                    tmp.unlink(missing_ok=True)
                else:
                    tmp.replace(dest)
            else:
                tmp.replace(dest)
        else:
            dump = work / "database" / "aibos.dump"
            if not dump.exists():
                raise FileNotFoundError("aibos.dump manquant dans l'archive")
            import os

            url = settings.database_url.replace("postgresql+psycopg2://", "postgresql://", 1)
            parsed = urlparse(url)
            env = {**os.environ, "PGPASSWORD": unquote(parsed.password or "")}
            cmd = [
                "pg_restore",
                "--clean",
                "--if-exists",
                "-h",
                parsed.hostname or "localhost",
                "-p",
                str(parsed.port or 5432),
                "-U",
                unquote(parsed.username or "aibos"),
                "-d",
                (parsed.path or "/aibos").lstrip("/") or "aibos",
                dump.as_posix(),
            ]
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                raise RuntimeError(f"pg_restore failed: {result.stderr.strip() or result.stdout.strip()}")

        storage_restored = 0
        if restore_storage:
            storage_dir = work / "storage"
            if storage_dir.exists():
                target = storage_root()
                target.mkdir(parents=True, exist_ok=True)
                for path in storage_dir.rglob("*"):
                    if path.is_file():
                        rel = path.relative_to(storage_dir)
                        dest_file = target / rel
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(path, dest_file)
                        storage_restored += 1

        return {
            "status": "restored",
            "backupId": backup_id,
            "engine": engine,
            "storageFiles": storage_restored,
            "entries": len(names),
            "note": "Redémarrez l'API pour recharger les connexions SQLAlchemy.",
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)
