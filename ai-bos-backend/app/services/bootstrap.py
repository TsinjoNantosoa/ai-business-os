from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.data import seed
from app.data.seed_crm import BILLING_PLANS, CRM_ACTIVITIES, CRM_CONTACTS, CRM_LEADS
from app.data.seed_documents import DOCUMENTS
from app.data.seed_finance import FINANCE_INVOICES, WORKFLOWS
from app.data.seed_tasks import TASKS
from app.data.seed_tickets import SUPPORT_TICKETS
from app.models.activity import Activity
from app.models.audit_log import AuditLog
from app.models.billing import BillingInvoice, BillingPlan, Subscription
from app.models.contact import Contact
from app.models.document import Document
from app.models.finance_invoice import FinanceInvoice
from app.models.api_key import ApiKey
from app.models.feature_flag import FeatureFlag
from app.models.invitation import Invitation
from app.models.lead import Lead
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.task import Task
from app.models.ticket import Ticket, TicketMessage
from app.models.user import User
from app.models.workflow import Workflow
from app.presentation.serializers import parse_iso_datetime
from app.repositories.activity_repository import ActivityRepository
from app.repositories.api_key_repository import DEFAULT_SCOPES, ApiKeyRepository, hash_api_key
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.billing_repository import BillingRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.feature_flag_repository import FeatureFlagRepository
from app.repositories.invitation_repository import InvitationRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.lead_repository import LeadRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.services.feature_flag_service import FEATURE_CATALOG
from app.services.role_permissions import OWNER_PERMISSIONS, permissions_for_role


def bootstrap_demo_data(session: Session) -> None:
    _bootstrap_organizations_and_users(session)
    _bootstrap_billing(session)
    _bootstrap_contacts(session)
    _bootstrap_leads_and_activities(session)
    _bootstrap_finance_invoices(session)
    _bootstrap_workflows(session)
    _bootstrap_webhooks(session)
    _bootstrap_tasks(session)
    _bootstrap_ops(session)
    _bootstrap_catalog(session)
    _bootstrap_tickets(session)
    _bootstrap_documents(session)
    _bootstrap_audit_logs(session)
    _bootstrap_invitations(session)
    _bootstrap_feature_flags(session)
    _bootstrap_notifications(session)
    _bootstrap_api_keys(session)
    session.commit()


def _bootstrap_catalog(session: Session) -> None:
    """Seed remaining modules (HR, procurement, analytics, …) into DB for org-1."""
    from app.data.seed_ops import DEMO_BI_REPORTS, DEMO_EMPLOYEES, DEMO_FINANCE_OVERVIEW
    from app.models.catalog import (
        AiAgent,
        Candidate,
        Contract,
        Employee,
        FinanceTransaction,
        InventoryItem,
        JobOpening,
        KnowledgeArticle,
        PurchaseOrder,
        Supplier,
    )
    from app.repositories.catalog_repository import CatalogRepository

    repo = CatalogRepository(session)
    org_id = "org-1"

    if repo.count_all(Employee) == 0:
        for i, emp in enumerate(DEMO_EMPLOYEES):
            manager_id = None
            if i > 0:
                manager_id = DEMO_EMPLOYEES[max(0, (i - 1) // 3)]["id"] if i > 2 else DEMO_EMPLOYEES[0]["id"]
            session.add(
                Employee(
                    id=emp["id"],
                    org_id=org_id,
                    first_name=emp["firstName"],
                    last_name=emp["lastName"],
                    email=emp["email"],
                    phone=emp.get("phone"),
                    position=emp["position"],
                    department=emp["department"],
                    start_date=emp["startDate"],
                    status=emp["status"],
                    avatar_color=emp.get("avatarColor"),
                    salary=emp.get("salary"),
                    location=emp.get("location"),
                    manager_id=manager_id,
                )
            )

    if repo.count_all(JobOpening) == 0:
        for job in seed.JOB_OPENINGS:
            session.add(
                JobOpening(
                    id=job["id"],
                    org_id=org_id,
                    title=job["title"],
                    department=job["department"],
                    status=job["status"],
                    applicants=job["applicants"],
                    posted_date=str(job["postedDate"])[:10] if job.get("postedDate") else "",
                    location=job["location"],
                    type=job["type"],
                )
            )

    if repo.count_all(Candidate) == 0:
        for cand in seed.CANDIDATES:
            session.add(
                Candidate(
                    id=cand["id"],
                    org_id=org_id,
                    name=cand["name"],
                    email=cand["email"],
                    job_id=cand.get("jobId"),
                    job_title=cand.get("jobTitle"),
                    stage=cand["stage"],
                    score=cand["score"],
                    avatar_color=cand.get("avatarColor"),
                    applied_at=str(cand["appliedAt"])[:32],
                )
            )

    if repo.count_all(Supplier) == 0:
        for s in seed.SUPPLIERS:
            session.add(
                Supplier(
                    id=s["id"],
                    org_id=org_id,
                    name=s["name"],
                    email=s["email"],
                    phone=s.get("phone"),
                    rating=s["rating"],
                    country=s["country"],
                    status=s["status"],
                )
            )

    if repo.count_all(PurchaseOrder) == 0:
        for po in seed.PURCHASE_ORDERS:
            session.add(
                PurchaseOrder(
                    id=po["id"],
                    org_id=org_id,
                    po_number=po["poNumber"],
                    supplier_id=po.get("supplierId"),
                    supplier_name=po["supplierName"],
                    status=po["status"],
                    total_amount=po["totalAmount"],
                    currency=po["currency"],
                    created_at_iso=str(po["createdAt"])[:32],
                    expected_at=str(po["expectedAt"])[:32],
                    owner_name=po["ownerName"],
                    item_count=po["itemCount"],
                )
            )

    if repo.count_all(Contract) == 0:
        for c in seed.CONTRACTS:
            session.add(
                Contract(
                    id=c["id"],
                    org_id=org_id,
                    title=c["title"],
                    type=c["type"],
                    counterparty=c["counterparty"],
                    value=c["value"],
                    currency=c["currency"],
                    start_date=str(c["startDate"])[:32],
                    end_date=str(c["endDate"])[:32] if c.get("endDate") else None,
                    status=c["status"],
                    owner=c["owner"],
                )
            )

    if repo.count_all(InventoryItem) == 0:
        for item in seed.INVENTORY_ITEMS:
            session.add(
                InventoryItem(
                    id=item["id"],
                    org_id=org_id,
                    sku=item["sku"],
                    name=item["name"],
                    category=item["category"],
                    quantity=item["quantity"],
                    reorder_level=item["reorderLevel"],
                    warehouse=item["warehouse"],
                    unit_price=item["unitPrice"],
                    status=item["status"],
                )
            )

    if repo.count_all(FinanceTransaction) == 0:
        for tx in DEMO_FINANCE_OVERVIEW["recentTransactions"]:
            session.add(
                FinanceTransaction(
                    id=tx["id"],
                    org_id=org_id,
                    description=tx["description"],
                    amount=tx["amount"],
                    type=tx["type"],
                    category=tx["category"],
                    date=tx["date"],
                    account=tx["account"],
                )
            )

    if repo.count_all(KnowledgeArticle) == 0:
        for art in seed.KNOWLEDGE_ARTICLES:
            session.add(
                KnowledgeArticle(
                    id=art["id"],
                    org_id=org_id,
                    title=art["title"],
                    category=art["category"],
                    excerpt=art["excerpt"],
                    content=art["content"],
                    author=art["author"],
                    updated_at_iso=str(art["updatedAt"])[:32],
                    views=art["views"],
                    helpful=art["helpful"],
                )
            )

    if repo.count_all(AiAgent) == 0:
        for agent in seed.AI_AGENTS:
            session.add(
                AiAgent(
                    id=agent["id"],
                    org_id=org_id,
                    slug=agent["slug"],
                    name=agent["name"],
                    description=agent["description"],
                    status=agent["status"],
                    category=agent["category"],
                    icon=agent["icon"],
                    tools_count=agent["toolsCount"],
                    last_used=str(agent["lastUsed"])[:32] if agent.get("lastUsed") else None,
                    conversations=agent["conversations"],
                )
            )

    if repo.get_dataset(org_id, "finance_overview") is None:
        repo.upsert_dataset(org_id, "finance_overview", DEMO_FINANCE_OVERVIEW)
    if repo.get_dataset(org_id, "analytics_kpis") is None:
        repo.upsert_dataset(org_id, "analytics_kpis", seed.ANALYTICS_KPIS)
    if repo.get_dataset(org_id, "bi_reports") is None:
        repo.upsert_dataset(org_id, "bi_reports", {"items": DEMO_BI_REPORTS})
    for horizon in ("7d", "30d", "90d"):
        key = f"forecast_{horizon}"
        if repo.get_dataset(org_id, key) is None:
            repo.upsert_dataset(org_id, key, seed.forecast_data(horizon))


def _bootstrap_organizations_and_users(session: Session) -> None:
    org_repo = OrganizationRepository(session)
    user_repo = UserRepository(session)

    if org_repo.count() == 0:
        for org_data in seed.ORGANIZATIONS:
            session.add(
                Organization(
                    id=org_data["id"],
                    name=org_data["name"],
                    plan=org_data["plan"],
                    currency=org_data["currency"],
                    timezone=org_data["timezone"],
                    locale=org_data["locale"],
                    address=org_data.get("address"),
                )
            )

    if user_repo.count() == 0:
        demo_users = [
        {
            "id": "u-owner-1",
            "email": "ceo@demo.aibos.io",
            "first_name": "Jean",
            "last_name": "Bernard",
            "role": "owner",
            "permissions": list(OWNER_PERMISSIONS),
            "org_id": "org-1",
        },
        {
            "id": "u-staff-1",
            "email": "staff@demo.aibos.io",
            "first_name": "Lucas",
            "last_name": "Thomas",
            "role": "staff",
            "permissions": permissions_for_role("staff"),
            "org_id": "org-1",
        },
        {
            "id": "u-sales-1",
            "email": "sales@demo.aibos.io",
            "first_name": "Marie",
            "last_name": "Dupont",
            "role": "admin",
            "permissions": permissions_for_role("admin"),
            "org_id": "org-1",
        },
        {
            "id": "u-finance-1",
            "email": "finance@demo.aibos.io",
            "first_name": "Paul",
            "last_name": "Martin",
            "role": "admin",
            "permissions": permissions_for_role("admin"),
            "org_id": "org-1",
        },
        {
            "id": "u-hr-1",
            "email": "hr@demo.aibos.io",
            "first_name": "Sophie",
            "last_name": "Leroy",
            "role": "admin",
            "permissions": permissions_for_role("admin"),
            "org_id": "org-1",
        },
        {
            "id": "u-owner-2",
            "email": "ceo@eu.aibos.io",
            "first_name": "Anna",
            "last_name": "Schmidt",
            "role": "owner",
            "permissions": list(OWNER_PERMISSIONS),
            "org_id": "org-2",
        },
        ]

        for user_data in demo_users:
            session.add(
                User(
                    id=user_data["id"],
                    email=user_data["email"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    role=user_data["role"],
                    permissions=user_data["permissions"],
                    org_id=user_data["org_id"],
                    password_hash=hash_password("demo1234"),
                    active=True,
                )
            )
        session.flush()

    _ensure_org2_user(session)
    _ensure_login_demo_users(session)
    _sync_demo_user_permissions(session)


def _ensure_personal_ceo_account(session: Session) -> None:
    """Deprecated — personal accounts must never be hardcoded in the codebase.

    Kept as a no-op so older call sites / branches do not break if reintroduced.
    """
    return


def _ensure_org2_user(session: Session) -> None:
    user_repo = UserRepository(session)
    if user_repo.get_by_email("ceo@eu.aibos.io"):
        return
    session.add(
        User(
            id="u-owner-2",
            email="ceo@eu.aibos.io",
            first_name="Anna",
            last_name="Schmidt",
            role="owner",
            permissions=list(OWNER_PERMISSIONS),
            org_id="org-2",
            password_hash=hash_password("demo1234"),
            active=True,
        )
    )
    session.flush()


def _ensure_login_demo_users(session: Session) -> None:
    """Ensure LoginPage demo accounts exist even on an already-seeded DB."""
    user_repo = UserRepository(session)
    extras = [
        {
            "id": "u-sales-1",
            "email": "sales@demo.aibos.io",
            "first_name": "Marie",
            "last_name": "Dupont",
            "role": "admin",
            "permissions": permissions_for_role("admin"),
        },
        {
            "id": "u-finance-1",
            "email": "finance@demo.aibos.io",
            "first_name": "Paul",
            "last_name": "Martin",
            "role": "admin",
            "permissions": permissions_for_role("admin"),
        },
        {
            "id": "u-hr-1",
            "email": "hr@demo.aibos.io",
            "first_name": "Sophie",
            "last_name": "Leroy",
            "role": "admin",
            "permissions": permissions_for_role("admin"),
        },
    ]
    for user_data in extras:
        if user_repo.get_by_email(user_data["email"]):
            continue
        session.add(
            User(
                id=user_data["id"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"],
                permissions=user_data["permissions"],
                org_id="org-1",
                password_hash=hash_password("demo1234"),
                active=True,
            )
        )
    session.flush()


def _sync_demo_user_permissions(session: Session) -> None:
    """Met à jour les permissions démo si la base existait déjà."""
    user_repo = UserRepository(session)
    expected: dict[str, list[str]] = {
        "ceo@demo.aibos.io": list(OWNER_PERMISSIONS),
        "staff@demo.aibos.io": permissions_for_role("staff"),
        "sales@demo.aibos.io": permissions_for_role("admin"),
        "finance@demo.aibos.io": permissions_for_role("admin"),
        "hr@demo.aibos.io": permissions_for_role("admin"),
        "ceo@eu.aibos.io": list(OWNER_PERMISSIONS),
    }
    for email, permissions in expected.items():
        user = user_repo.get_by_email(email)
        if user and list(user.permissions or []) != permissions:
            user.permissions = permissions


def _bootstrap_billing(session: Session) -> None:
    billing_repo = BillingRepository(session)
    if billing_repo.plans_count() > 0:
        return

    for plan_data in BILLING_PLANS:
        session.add(BillingPlan(**plan_data))

    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=30)
    subscription = Subscription(
        id="sub-org-1",
        org_id="org-1",
        plan_id="plan-enterprise",
        status="active",
        current_period_start=now,
        current_period_end=period_end,
        seats_used=25,
        ai_tokens_used=850_000,
        storage_gb_used=45,
        stripe_customer_id="cus_demo_org1",
        stripe_subscription_id="sub_demo_org1",
    )
    session.add(subscription)

    for i, month_label in enumerate(["012", "011", "010", "009"]):
        period_start = now - timedelta(days=30 * (i + 1))
        period_invoice_end = period_start + timedelta(days=30)
        session.add(
            BillingInvoice(
                id=f"bill-inv-{i + 1}",
                org_id="org-1",
                subscription_id="sub-org-1",
                invoice_number=f"INV-2024-{month_label}",
                amount=1200,
                currency="EUR",
                status="paid",
                period_start=period_start,
                period_end=period_invoice_end,
                stripe_invoice_id=f"in_demo_{month_label}",
                pdf_url=f"https://billing.demo.aibos.io/invoices/INV-2024-{month_label}.pdf",
                created_at=period_invoice_end,
            )
        )


def _bootstrap_contacts(session: Session) -> None:
    contact_repo = ContactRepository(session)
    if contact_repo.count_all() == 0:
        for contact_data in CRM_CONTACTS:
            session.add(
                Contact(
                    id=contact_data["id"],
                    org_id=contact_data["org_id"],
                    first_name=contact_data["first_name"],
                    last_name=contact_data["last_name"],
                    email=contact_data["email"],
                    phone=contact_data["phone"],
                    company=contact_data["company"],
                    position=contact_data["position"],
                    status=contact_data["status"],
                    owner_id=contact_data["owner_id"],
                    owner_name=contact_data["owner_name"],
                    tags=contact_data["tags"],
                    avatar_color=contact_data["avatar_color"],
                    last_activity_at=parse_iso_datetime(contact_data["last_activity_at"]),
                    created_at=parse_iso_datetime(contact_data["created_at"]),
                )
            )
        session.flush()

    # Dedicated contact for tenant isolation tests (org-2).
    if not contact_repo.get_by_id("org-2", "contact-org2-1"):
        now = datetime.now(timezone.utc)
        session.add(
            Contact(
                id="contact-org2-1",
                org_id="org-2",
                first_name="Klaus",
                last_name="Weber",
                email="klaus@eu-partner.de",
                phone="+49 30 123456",
                company="EU Partner GmbH",
                position="CEO",
                status="active",
                owner_id="u-owner-2",
                owner_name="Anna Schmidt",
                tags=["eu", "partner"],
                avatar_color="bg-emerald-100",
                last_activity_at=now,
                created_at=now,
            )
        )


def _bootstrap_leads_and_activities(session: Session) -> None:
    lead_repo = LeadRepository(session)
    activity_repo = ActivityRepository(session)

    if lead_repo.count_all() == 0:
        for lead_data in CRM_LEADS:
            session.add(
                Lead(
                    id=lead_data["id"],
                    org_id=lead_data["org_id"],
                    title=lead_data["title"],
                    company=lead_data["company"],
                    contact_name=lead_data["contact_name"],
                    value=lead_data["value"],
                    currency=lead_data["currency"],
                    stage=lead_data["stage"],
                    probability=lead_data["probability"],
                    owner_id=lead_data["owner_id"],
                    owner_name=lead_data["owner_name"],
                    owner_avatar_color=lead_data["owner_avatar_color"],
                    expected_close_date=parse_iso_datetime(lead_data["expected_close_date"]),
                    stage_changed_at=parse_iso_datetime(lead_data["stage_changed_at"]),
                    created_at=parse_iso_datetime(lead_data["created_at"]),
                )
            )

    if activity_repo.count_all() == 0:
        for activity_data in CRM_ACTIVITIES:
            session.add(
                Activity(
                    id=activity_data["id"],
                    org_id=activity_data["org_id"],
                    type=activity_data["type"],
                    description=activity_data["description"],
                    contact_id=activity_data["contact_id"],
                    user_id=activity_data["user_id"],
                    user_name=activity_data["user_name"],
                    created_at=parse_iso_datetime(activity_data["created_at"]),
                )
            )


def _bootstrap_finance_invoices(session: Session) -> None:
    invoice_repo = InvoiceRepository(session)
    if invoice_repo.count_all() > 0:
        return

    for invoice_data in FINANCE_INVOICES:
        session.add(
            FinanceInvoice(
                id=invoice_data["id"],
                org_id=invoice_data["org_id"],
                invoice_number=invoice_data["invoice_number"],
                client_id=invoice_data["client_id"],
                client_name=invoice_data["client_name"],
                amount=invoice_data["amount"],
                tax_amount=invoice_data["tax_amount"],
                total_amount=invoice_data["total_amount"],
                currency=invoice_data["currency"],
                status=invoice_data["status"],
                issue_date=parse_iso_datetime(invoice_data["issue_date"]),
                due_date=parse_iso_datetime(invoice_data["due_date"]),
                paid_date=parse_iso_datetime(invoice_data["paid_date"]) if invoice_data.get("paid_date") else None,
                line_items=invoice_data["line_items"],
            )
        )


def _bootstrap_workflows(session: Session) -> None:
    workflow_repo = WorkflowRepository(session)
    if workflow_repo.count_all() > 0:
        return

    for workflow_data in WORKFLOWS:
        session.add(
            Workflow(
                id=workflow_data["id"],
                org_id=workflow_data["org_id"],
                name=workflow_data["name"],
                description=workflow_data["description"],
                status=workflow_data["status"],
                trigger=workflow_data["trigger"],
                actions=workflow_data["actions"],
                last_run=parse_iso_datetime(workflow_data["last_run"]) if workflow_data.get("last_run") else None,
                run_count=workflow_data["run_count"],
                success_rate=workflow_data["success_rate"],
            )
        )


def _bootstrap_webhooks(session: Session) -> None:
    """Default inbound webhook for org-1 (Lot F / S33)."""
    from app.services.event_bus import WebhookEndpointRepository

    repo = WebhookEndpointRepository(session)
    if repo.count_by_org("org-1") > 0:
        return
    repo.create(
        org_id="org-1",
        name="Inbound démo",
        description="Webhook entrant démo — Lot F / S33",
        event_types=["webhook.inbound", "crm.lead.created"],
    )


def _bootstrap_tasks(session: Session) -> None:
    task_repo = TaskRepository(session)
    if task_repo.count_all() > 0:
        return

    for task_data in TASKS:
        session.add(
            Task(
                id=task_data["id"],
                org_id=task_data["org_id"],
                title=task_data["title"],
                description=task_data["description"],
                status=task_data["status"],
                priority=task_data["priority"],
                assignee_id=task_data["assignee_id"],
                assignee_name=task_data["assignee_name"],
                assignee_avatar_color=task_data["assignee_avatar_color"],
                project_id=task_data["project_id"],
                project_name=task_data["project_name"],
                due_date=parse_iso_datetime(task_data["due_date"]),
                tags=task_data["tags"],
                created_at=parse_iso_datetime(task_data["created_at"]),
            )
        )


def _bootstrap_ops(session: Session) -> None:
    """Seed Lot B demo data (orders, campaigns, projects, events, meetings) into org-1."""
    from datetime import datetime, timezone as _tz

    from app.data.seed_ops import (
        DEMO_CALENDAR_EVENTS,
        DEMO_CAMPAIGNS,
        DEMO_MEETINGS,
        DEMO_PROJECTS,
        DEMO_SALES_ORDERS,
    )
    from app.models.ops import CalendarEvent, Campaign, Meeting, Project, SalesOrder
    from app.repositories.ops_repository import SalesOrderRepository

    if SalesOrderRepository(session).count_all() > 0:
        return

    now = datetime.now(_tz.utc)
    org_id = "org-1"

    for order in DEMO_SALES_ORDERS:
        session.add(
            SalesOrder(
                id=order["id"],
                org_id=org_id,
                order_number=order["orderNumber"],
                customer_id=order["customerId"],
                customer_name=order["customerName"],
                status=order["status"],
                amount=order["amount"],
                currency=order["currency"],
                date=order["date"],
                sales_rep_id=order["salesRepId"],
                sales_rep_name=order["salesRepName"],
                line_items=order["lineItems"],
                created_at=now,
                updated_at=now,
            )
        )

    for campaign in DEMO_CAMPAIGNS:
        session.add(
            Campaign(
                id=campaign["id"],
                org_id=org_id,
                name=campaign["name"],
                type=campaign["type"],
                status=campaign["status"],
                reach=campaign["reach"],
                open_rate=campaign["openRate"],
                click_rate=campaign["clickRate"],
                conversions=campaign["conversions"],
                budget=campaign["budget"],
                spent=campaign["spent"],
                start_date=str(campaign["startDate"])[:10],
                end_date=str(campaign["endDate"])[:10] if campaign.get("endDate") else None,
                created_at=now,
                updated_at=now,
            )
        )

    for project in DEMO_PROJECTS:
        session.add(
            Project(
                id=project["id"],
                org_id=org_id,
                name=project["name"],
                description=project["description"],
                status=project["status"],
                progress=project["progress"],
                start_date=str(project["startDate"])[:10],
                end_date=str(project["endDate"])[:10] if project.get("endDate") else None,
                budget=project["budget"],
                spent=project["spent"],
                team_members=project["teamMembers"],
                task_count=project["taskCount"],
                completed_tasks=project["completedTasks"],
                color=project["color"],
                created_at=now,
                updated_at=now,
            )
        )

    for event in DEMO_CALENDAR_EVENTS:
        session.add(
            CalendarEvent(
                id=event["id"],
                org_id=org_id,
                title=event["title"],
                type=event["type"],
                start_date=event["startDate"],
                end_date=event.get("endDate"),
                color=event["color"],
                location=event.get("location"),
                attendees=event.get("attendees") or [],
                description=event.get("description"),
                created_at=now,
                updated_at=now,
            )
        )

    for meeting in DEMO_MEETINGS:
        session.add(
            Meeting(
                id=meeting["id"],
                org_id=org_id,
                title=meeting["title"],
                date=str(meeting["date"])[:10],
                duration=meeting["duration"],
                status=meeting["status"],
                location=meeting.get("location"),
                attendees=meeting.get("attendees") or [],
                agenda=meeting.get("agenda") or [],
                summary=meeting.get("summary"),
                action_items=meeting.get("actionItems") or [],
                created_at=now,
                updated_at=now,
            )
        )


def _bootstrap_tickets(session: Session) -> None:
    ticket_repo = TicketRepository(session)
    if ticket_repo.count_all() > 0:
        return

    for ticket_data in SUPPORT_TICKETS:
        session.add(
            Ticket(
                id=ticket_data["id"],
                org_id=ticket_data["org_id"],
                ticket_number=ticket_data["ticket_number"],
                subject=ticket_data["subject"],
                customer_name=ticket_data["customer_name"],
                customer_email=ticket_data["customer_email"],
                priority=ticket_data["priority"],
                status=ticket_data["status"],
                agent_id=ticket_data.get("agent_id"),
                agent_name=ticket_data.get("agent_name"),
                category=ticket_data["category"],
                sla_deadline=parse_iso_datetime(ticket_data["sla_deadline"]),
                created_at=parse_iso_datetime(ticket_data["created_at"]),
                updated_at=parse_iso_datetime(ticket_data["updated_at"]),
            )
        )
        for message_data in ticket_data["messages"]:
            session.add(
                TicketMessage(
                    id=message_data["id"],
                    org_id=message_data["org_id"],
                    ticket_id=message_data["ticket_id"],
                    author=message_data["author"],
                    content=message_data["content"],
                    is_internal=message_data["is_internal"],
                    created_at=parse_iso_datetime(message_data["created_at"]),
                )
            )


def _bootstrap_documents(session: Session) -> None:
    document_repo = DocumentRepository(session)
    if document_repo.count_all() > 0:
        return

    for doc_data in DOCUMENTS:
        session.add(
            Document(
                id=doc_data["id"],
                org_id=doc_data["org_id"],
                name=doc_data["name"],
                type=doc_data["type"],
                size=doc_data["size"],
                parent_id=doc_data.get("parent_id"),
                storage_key=doc_data.get("storage_key"),
                mime_type=doc_data.get("mime_type"),
                starred=doc_data.get("starred", False),
                modified_by=doc_data["modified_by"],
                modified_at=parse_iso_datetime(doc_data["modified_at"]),
            )
        )


def _bootstrap_audit_logs(session: Session) -> None:
    audit_repo = AuditLogRepository(session)
    if audit_repo.count_all() > 0:
        return

    for log_data in seed.AUDIT_LOGS:
        session.add(
            AuditLog(
                id=log_data["id"],
                org_id="org-1",
                timestamp=parse_iso_datetime(log_data["timestamp"]),
                user_id=log_data["userId"],
                user_name=log_data["userName"],
                action=log_data["action"],
                resource=log_data["resource"],
                resource_id=log_data.get("resourceId"),
                ip=log_data["ip"],
                details=log_data.get("details"),
            )
        )


def _bootstrap_invitations(session: Session) -> None:
    inv_repo = InvitationRepository(session)
    if inv_repo.count_all() > 0:
        return

    now = datetime.now(timezone.utc)
    session.add(
        Invitation(
            id="inv-demo-1",
            org_id="org-1",
            email="nouveau@acme.com",
            role="staff",
            token="demo-invite-token-nouveau",
            status="pending",
            invited_by="u-owner-1",
            invited_by_name="Jean Bernard",
            message="Bienvenue dans l'équipe Acme",
            created_at=now,
            expires_at=now + timedelta(days=7),
        )
    )


def _bootstrap_feature_flags(session: Session) -> None:
    flag_repo = FeatureFlagRepository(session)
    if flag_repo.count_flags() > 0:
        return
    for item in FEATURE_CATALOG:
        session.add(
            FeatureFlag(
                key=item["key"],
                name=item["name"],
                description=item["description"],
                env=item["env"],
                default_enabled=item["default_enabled"],
            )
        )


def _bootstrap_notifications(session: Session) -> None:
    notif_repo = NotificationRepository(session)
    if notif_repo.count_all() > 0:
        return
    for item in seed.NOTIFICATIONS:
        session.add(
            Notification(
                id=item["id"],
                org_id="org-1",
                user_id=None,
                type=item["type"],
                title=item["title"],
                message=item["message"],
                read=item["read"],
                link=item.get("link"),
                created_at=parse_iso_datetime(item["createdAt"]),
            )
        )


def _bootstrap_api_keys(session: Session) -> None:
    repo = ApiKeyRepository(session)
    if repo.count_all() > 0:
        return
    # Known demo secret for integration tests (never returned by list API).
    raw = "aibos_sk_demo_integration_key_do_not_share"
    session.add(
        ApiKey(
            id="apk-demo-1",
            org_id="org-1",
            name="Demo Integration",
            key_prefix=raw[:16],
            key_hash=hash_api_key(raw),
            scopes=list(DEFAULT_SCOPES),
            created_by="u-owner-1",
            created_by_name="Jean Bernard",
            active=True,
            created_at=datetime.now(timezone.utc),
        )
    )
