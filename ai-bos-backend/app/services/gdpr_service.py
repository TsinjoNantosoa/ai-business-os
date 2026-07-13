from __future__ import annotations

from sqlalchemy.orm import Session

from app.presentation.serializers import (
    contact_to_dict,
    lead_to_dict,
    notification_to_dict,
    organization_to_dict,
    task_to_dict,
    team_member_to_dict,
)
from app.repositories.activity_repository import ActivityRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.lead_repository import LeadRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.user_repository import UserRepository


def build_gdpr_export(db: Session, *, org_id: str, user_id: str) -> dict:
    org = OrganizationRepository(db).get_by_id(org_id)
    user = UserRepository(db).get_by_id(user_id)
    contacts = ContactRepository(db).list_by_org(org_id)
    leads = LeadRepository(db).list_by_org(org_id)
    activities = ActivityRepository(db).list_by_org(org_id)
    invoices = InvoiceRepository(db).list_by_org(org_id)
    tasks = TaskRepository(db).list_by_org(org_id)
    tickets = TicketRepository(db).list_by_org(org_id)
    documents = DocumentRepository(db).list_by_org(org_id)
    notifications = NotificationRepository(db).list_for_user(org_id, user_id=user_id)
    audit = AuditLogRepository(db).list_by_org(org_id, limit=200)

    return {
        "exportVersion": "1.0",
        "subject": {"userId": user_id, "orgId": org_id},
        "organization": organization_to_dict(org) if org else None,
        "user": team_member_to_dict(user) if user else None,
        "contacts": [contact_to_dict(c) for c in contacts],
        "leads": [lead_to_dict(lead) for lead in leads],
        "activitiesCount": len(activities),
        "invoicesCount": len(invoices),
        "tasks": [task_to_dict(t) for t in tasks],
        "ticketsCount": len(tickets),
        "documentsCount": len(documents),
        "notifications": [notification_to_dict(n) for n in notifications],
        "auditLogsCount": len(audit),
        "note": "Export GDPR portabilité — données accessibles pour le tenant de l'utilisateur.",
    }
