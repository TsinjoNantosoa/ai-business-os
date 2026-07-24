"""Seed / reseed full demo data for Neon, Render, Plesk, or local Postgres.

Idempotent: fills empty tables; does not wipe existing customer data.

Usage (from ai-bos-backend/):
  python scripts/reseed_demo.py

Env required: DATABASE_URL (and JWT_SECRET if ENVIRONMENT=production).
Optional: SEED_DEMO_DATA is not required for this script — it always seeds.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.logging_config import configure_logging  # noqa: E402
from app.core.migrations import run_migrations  # noqa: E402
from app.services.bootstrap import bootstrap_demo_data  # noqa: E402
from app.services.rag_ingest import ensure_rag_index  # noqa: E402

logger = logging.getLogger("aibos.seed")


def _sqlite_path() -> Path | None:
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        return None
    raw = url.replace("sqlite:///", "", 1)
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    return path


def _print_counts(session) -> None:
    from app.models.catalog import Candidate, Contract, Employee, InventoryItem, PurchaseOrder, Supplier
    from app.repositories.activity_repository import ActivityRepository
    from app.repositories.audit_log_repository import AuditLogRepository
    from app.repositories.contact_repository import ContactRepository
    from app.repositories.document_repository import DocumentRepository
    from app.repositories.invoice_repository import InvoiceRepository
    from app.repositories.lead_repository import LeadRepository
    from app.repositories.notification_repository import NotificationRepository
    from app.repositories.ops_repository import (
        CalendarEventRepository,
        CampaignRepository,
        MeetingRepository,
        ProjectRepository,
        SalesOrderRepository,
    )
    from app.repositories.organization_repository import OrganizationRepository
    from app.repositories.task_repository import TaskRepository
    from app.repositories.ticket_repository import TicketRepository
    from app.repositories.user_repository import UserRepository
    from app.repositories.workflow_repository import WorkflowRepository
    from app.repositories.catalog_repository import CatalogRepository

    catalog = CatalogRepository(session)
    print("Reseed OK — demo dataset:")
    print(f"  organizations={OrganizationRepository(session).count()}")
    print(f"  users={UserRepository(session).count()}")
    print(f"  contacts={ContactRepository(session).count_all()}")
    print(f"  leads={LeadRepository(session).count_all()}")
    print(f"  activities={ActivityRepository(session).count_all()}")
    print(f"  invoices={InvoiceRepository(session).count_all()}")
    print(f"  tasks={TaskRepository(session).count_all()}")
    print(f"  tickets={TicketRepository(session).count_all()}")
    print(f"  workflows={WorkflowRepository(session).count_all()}")
    print(f"  documents={DocumentRepository(session).count_all()}")
    print(f"  sales_orders={SalesOrderRepository(session).count_all()}")
    print(f"  campaigns={CampaignRepository(session).count_all()}")
    print(f"  projects={ProjectRepository(session).count_all()}")
    print(f"  calendar_events={CalendarEventRepository(session).count_all()}")
    print(f"  meetings={MeetingRepository(session).count_all()}")
    print(f"  employees={catalog.count_all(Employee)}")
    print(f"  candidates={catalog.count_all(Candidate)}")
    print(f"  suppliers={catalog.count_all(Supplier)}")
    print(f"  purchase_orders={catalog.count_all(PurchaseOrder)}")
    print(f"  inventory={catalog.count_all(InventoryItem)}")
    print(f"  contracts={catalog.count_all(Contract)}")
    print(f"  audit_logs={AuditLogRepository(session).count_all()}")
    print(f"  notifications={NotificationRepository(session).count_all()}")
    print("")
    print("Comptes de test (mot de passe: demo1234):")
    print("  ceo@demo.aibos.io       — owner (tout voir)")
    print("  sales@demo.aibos.io     — sales")
    print("  finance@demo.aibos.io   — finance")
    print("  hr@demo.aibos.io        — RH")
    print("  staff@demo.aibos.io     — staff")


def main() -> None:
    configure_logging()
    db_path = _sqlite_path()
    if db_path is None:
        print(f"Postgres/Neon — seed idempotent sur {settings.database_url.split('@')[-1]}")
    else:
        for suffix in ("", "-wal", "-shm"):
            p = Path(str(db_path) + suffix) if suffix else db_path
            if p.exists():
                p.unlink()
                print(f"Deleted {p}")

    run_migrations()
    with SessionLocal() as session:
        bootstrap_demo_data(session)
        try:
            ensure_rag_index(session)
        except Exception:
            logger.exception("rag_index_failed_during_seed")
        _print_counts(session)


if __name__ == "__main__":
    main()
