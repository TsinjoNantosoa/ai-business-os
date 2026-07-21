"""Reset SQLite demo DB and reseed rich demo data.

Usage (from ai-bos-backend/):
  python scripts/reseed_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.migrations import run_migrations  # noqa: E402
from app.services.bootstrap import bootstrap_demo_data  # noqa: E402
from app.services.rag_ingest import ensure_rag_index  # noqa: E402


def _sqlite_path() -> Path | None:
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        return None
    raw = url.replace("sqlite:///", "", 1)
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    return path


def main() -> None:
    db_path = _sqlite_path()
    if db_path is None:
        print(f"DATABASE_URL non-SQLite ({settings.database_url}) — skip file delete, bootstrap only.")
    else:
        for suffix in ("", "-wal", "-shm"):
            p = Path(str(db_path) + suffix) if suffix else db_path
            if p.exists():
                p.unlink()
                print(f"Deleted {p}")

    run_migrations()
    with SessionLocal() as session:
        bootstrap_demo_data(session)
        ensure_rag_index(session)

        from app.repositories.contact_repository import ContactRepository
        from app.repositories.lead_repository import LeadRepository
        from app.repositories.invoice_repository import InvoiceRepository
        from app.repositories.task_repository import TaskRepository
        from app.repositories.ticket_repository import TicketRepository
        from app.repositories.activity_repository import ActivityRepository
        from app.repositories.workflow_repository import WorkflowRepository
        from app.repositories.document_repository import DocumentRepository
        from app.repositories.audit_log_repository import AuditLogRepository
        from app.repositories.notification_repository import NotificationRepository

        print("Reseed OK:")
        print(f"  contacts={ContactRepository(session).count_all()}")
        print(f"  leads={LeadRepository(session).count_all()}")
        print(f"  activities={ActivityRepository(session).count_all()}")
        print(f"  invoices={InvoiceRepository(session).count_all()}")
        print(f"  tasks={TaskRepository(session).count_all()}")
        print(f"  tickets={TicketRepository(session).count_all()}")
        print(f"  workflows={WorkflowRepository(session).count_all()}")
        print(f"  documents={DocumentRepository(session).count_all()}")
        print(f"  audit_logs={AuditLogRepository(session).count_all()}")
        print(f"  notifications={NotificationRepository(session).count_all()}")


if __name__ == "__main__":
    main()
