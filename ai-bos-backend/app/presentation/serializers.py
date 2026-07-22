from __future__ import annotations

from datetime import datetime, timezone

from app.models.activity import Activity
from app.models.api_key import ApiKey
from app.models.audit_log import AuditLog
from app.models.billing import BillingInvoice, BillingPlan, Subscription
from app.models.contact import Contact
from app.models.document import Document
from app.models.finance_invoice import FinanceInvoice
from app.models.invitation import Invitation
from app.models.lead import Lead
from app.models.notification import Notification
from app.models.ops import CalendarEvent, Campaign, Meeting, Project, SalesOrder
from app.models.organization import Organization
from app.models.task import Task
from app.models.ticket import Ticket, TicketMessage
from app.models.user import User
from app.models.workflow import Workflow, WorkflowExecution


def contact_to_dict(contact: Contact) -> dict:
    return {
        "id": contact.id,
        "firstName": contact.first_name,
        "lastName": contact.last_name,
        "email": contact.email,
        "phone": contact.phone,
        "company": contact.company,
        "position": contact.position,
        "status": contact.status,
        "ownerId": contact.owner_id,
        "ownerName": contact.owner_name,
        "tags": contact.tags or [],
        "lastActivityAt": contact.last_activity_at.isoformat(),
        "createdAt": contact.created_at.isoformat(),
        "avatarColor": contact.avatar_color,
    }


def lead_to_dict(lead: Lead) -> dict:
    now = datetime.now(timezone.utc)
    stage_changed = lead.stage_changed_at
    if stage_changed.tzinfo is None:
        stage_changed = stage_changed.replace(tzinfo=timezone.utc)
    days_in_stage = max(1, (now - stage_changed).days + 1)
    return {
        "id": lead.id,
        "title": lead.title,
        "company": lead.company,
        "contactName": lead.contact_name,
        "value": lead.value,
        "currency": lead.currency,
        "stage": lead.stage,
        "probability": lead.probability,
        "ownerId": lead.owner_id,
        "ownerName": lead.owner_name,
        "ownerAvatarColor": lead.owner_avatar_color,
        "expectedCloseDate": lead.expected_close_date.isoformat(),
        "daysInStage": days_in_stage,
        "createdAt": lead.created_at.isoformat(),
    }


def activity_to_dict(activity: Activity) -> dict:
    return {
        "id": activity.id,
        "type": activity.type,
        "description": activity.description,
        "contactId": activity.contact_id,
        "userId": activity.user_id,
        "userName": activity.user_name,
        "createdAt": activity.created_at.isoformat(),
    }


def task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "assigneeId": task.assignee_id,
        "assigneeName": task.assignee_name,
        "assigneeAvatarColor": task.assignee_avatar_color,
        "projectId": task.project_id,
        "projectName": task.project_name,
        "dueDate": task.due_date.date().isoformat(),
        "tags": task.tags or [],
        "createdAt": task.created_at.isoformat(),
    }


def document_to_dict(document: Document) -> dict:
    return {
        "id": document.id,
        "name": document.name,
        "type": document.type,
        "size": document.size,
        "parentId": document.parent_id,
        "modifiedAt": document.modified_at.isoformat(),
        "modifiedBy": document.modified_by,
        "starred": document.starred,
        "hasFile": bool(document.storage_key),
    }


def audit_log_to_dict(entry: AuditLog) -> dict:
    return {
        "id": entry.id,
        "timestamp": entry.timestamp.isoformat(),
        "userId": entry.user_id,
        "userName": entry.user_name,
        "action": entry.action,
        "resource": entry.resource,
        "resourceId": entry.resource_id,
        "ip": entry.ip,
        "details": entry.details,
    }


def ticket_message_to_dict(message: TicketMessage) -> dict:
    return {
        "id": message.id,
        "author": message.author,
        "content": message.content,
        "createdAt": message.created_at.isoformat(),
        "isInternal": message.is_internal,
    }


def ticket_to_dict(ticket: Ticket) -> dict:
    return {
        "id": ticket.id,
        "ticketNumber": ticket.ticket_number,
        "subject": ticket.subject,
        "customerName": ticket.customer_name,
        "customerEmail": ticket.customer_email,
        "priority": ticket.priority,
        "status": ticket.status,
        "agentId": ticket.agent_id,
        "agentName": ticket.agent_name,
        "createdAt": ticket.created_at.isoformat(),
        "updatedAt": ticket.updated_at.isoformat(),
        "slaDeadline": ticket.sla_deadline.isoformat(),
        "category": ticket.category,
        "messages": [ticket_message_to_dict(message) for message in (ticket.messages or [])],
    }


def plan_to_dict(plan: BillingPlan) -> dict:
    return {
        "id": plan.id,
        "code": plan.code,
        "name": plan.name,
        "priceMonthly": plan.price_monthly,
        "currency": plan.currency,
        "seatsLimit": plan.seats_limit,
        "aiTokensLimit": plan.ai_tokens_limit,
        "storageGbLimit": plan.storage_gb_limit,
    }


def subscription_to_dict(subscription: Subscription) -> dict:
    plan = subscription.plan
    return {
        "id": subscription.id,
        "orgId": subscription.org_id,
        "status": subscription.status,
        "plan": plan_to_dict(plan) if plan else None,
        "currentPeriodStart": subscription.current_period_start.isoformat(),
        "currentPeriodEnd": subscription.current_period_end.isoformat(),
        "renewalDate": subscription.current_period_end.isoformat(),
        "usage": {
            "seats": {"used": subscription.seats_used, "limit": plan.seats_limit if plan else 0},
            "aiTokens": {"used": subscription.ai_tokens_used, "limit": plan.ai_tokens_limit if plan else 0},
            "storageGb": {"used": subscription.storage_gb_used, "limit": plan.storage_gb_limit if plan else 0},
        },
        "stripeCustomerId": subscription.stripe_customer_id,
        "stripeSubscriptionId": subscription.stripe_subscription_id,
    }


def billing_invoice_to_dict(invoice: BillingInvoice) -> dict:
    return {
        "id": invoice.id,
        "invoiceNumber": invoice.invoice_number,
        "amount": invoice.amount,
        "currency": invoice.currency,
        "status": invoice.status,
        "periodStart": invoice.period_start.isoformat(),
        "periodEnd": invoice.period_end.isoformat(),
        "createdAt": invoice.created_at.isoformat(),
        "pdfUrl": invoice.pdf_url,
    }


def finance_invoice_to_dict(invoice: FinanceInvoice) -> dict:
    return {
        "id": invoice.id,
        "invoiceNumber": invoice.invoice_number,
        "clientId": invoice.client_id,
        "clientName": invoice.client_name,
        "amount": invoice.amount,
        "taxAmount": invoice.tax_amount,
        "totalAmount": invoice.total_amount,
        "currency": invoice.currency,
        "status": invoice.status,
        "issueDate": invoice.issue_date.date().isoformat(),
        "dueDate": invoice.due_date.date().isoformat(),
        "paidDate": invoice.paid_date.date().isoformat() if invoice.paid_date else None,
        "lineItems": invoice.line_items or [],
    }


def workflow_to_dict(workflow: Workflow) -> dict:
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "trigger": workflow.trigger,
        "actions": workflow.actions or [],
        "lastRun": workflow.last_run.isoformat() if workflow.last_run else None,
        "runCount": workflow.run_count,
        "successRate": workflow.success_rate,
    }


def workflow_execution_to_dict(execution: WorkflowExecution, workflow_name: str | None = None) -> dict:
    return {
        "id": execution.id,
        "workflowId": execution.workflow_id,
        "workflowName": workflow_name,
        "status": execution.status,
        "startedAt": execution.started_at.isoformat(),
        "finishedAt": execution.finished_at.isoformat() if execution.finished_at else None,
        "durationMs": execution.duration_ms,
        "resultMessage": execution.result_message,
        "errorMessage": execution.error_message,
    }


def organization_to_dict(org: Organization) -> dict:
    return {
        "id": org.id,
        "name": org.name,
        "plan": org.plan,
        "currency": org.currency,
        "timezone": org.timezone,
        "locale": org.locale,
        "address": org.address,
    }


def team_member_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "name": f"{user.first_name} {user.last_name}".strip(),
        "email": user.email,
        "role": user.role,
        "status": "active" if user.active else "inactive",
        "firstName": user.first_name,
        "lastName": user.last_name,
    }


def invitation_to_dict(invitation: Invitation, *, include_token: bool = False) -> dict:
    data = {
        "id": invitation.id,
        "orgId": invitation.org_id,
        "email": invitation.email,
        "role": invitation.role,
        "status": invitation.status,
        "invitedBy": invitation.invited_by,
        "invitedByName": invitation.invited_by_name,
        "message": invitation.message,
        "createdAt": invitation.created_at.isoformat(),
        "expiresAt": invitation.expires_at.isoformat(),
        "acceptedAt": invitation.accepted_at.isoformat() if invitation.accepted_at else None,
    }
    if include_token:
        data["token"] = invitation.token
    return data


def notification_to_dict(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "read": notification.read,
        "createdAt": notification.created_at.isoformat(),
        "link": notification.link,
        "userId": notification.user_id,
    }


def api_key_to_dict(api_key: ApiKey) -> dict:
    from app.repositories.api_key_repository import mask_api_key

    return {
        "id": api_key.id,
        "name": api_key.name,
        "keyPrefix": api_key.key_prefix,
        "maskedKey": mask_api_key(api_key.key_prefix),
        "scopes": api_key.scopes or [],
        "active": api_key.active,
        "createdBy": api_key.created_by,
        "createdByName": api_key.created_by_name,
        "createdAt": api_key.created_at.isoformat(),
        "lastUsedAt": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        "revokedAt": api_key.revoked_at.isoformat() if api_key.revoked_at else None,
    }


def sales_order_to_dict(order: SalesOrder) -> dict:
    return {
        "id": order.id,
        "orderNumber": order.order_number,
        "customerId": order.customer_id,
        "customerName": order.customer_name,
        "status": order.status,
        "amount": order.amount,
        "currency": order.currency,
        "date": order.date,
        "salesRepId": order.sales_rep_id,
        "salesRepName": order.sales_rep_name,
        "lineItems": order.line_items or [],
    }


def campaign_to_dict(campaign: Campaign) -> dict:
    return {
        "id": campaign.id,
        "name": campaign.name,
        "type": campaign.type,
        "status": campaign.status,
        "reach": campaign.reach,
        "openRate": campaign.open_rate,
        "clickRate": campaign.click_rate,
        "conversions": campaign.conversions,
        "budget": campaign.budget,
        "spent": campaign.spent,
        "startDate": campaign.start_date,
        "endDate": campaign.end_date,
    }


def project_to_dict(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "progress": project.progress,
        "startDate": project.start_date,
        "endDate": project.end_date,
        "budget": project.budget,
        "spent": project.spent,
        "teamMembers": project.team_members or [],
        "taskCount": project.task_count,
        "completedTasks": project.completed_tasks,
        "color": project.color,
    }


def calendar_event_to_dict(event: CalendarEvent) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "type": event.type,
        "startDate": event.start_date,
        "endDate": event.end_date,
        "color": event.color,
        "location": event.location,
        "attendees": event.attendees or [],
        "description": event.description,
    }


def meeting_to_dict(meeting: Meeting) -> dict:
    return {
        "id": meeting.id,
        "title": meeting.title,
        "date": meeting.date,
        "duration": meeting.duration,
        "status": meeting.status,
        "location": meeting.location,
        "attendees": meeting.attendees or [],
        "agenda": meeting.agenda or [],
        "summary": meeting.summary,
        "actionItems": meeting.action_items or [],
    }


def parse_iso_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
