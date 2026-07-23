"""Catalog: workflow trigger labels ↔ domain event types (Lot F / S33)."""

from __future__ import annotations

# Free-text trigger labels used in the designer / seed → canonical event types
TRIGGER_LABEL_TO_EVENT: dict[str, str] = {
    "Lead créé": "crm.lead.created",
    "Contact créé": "crm.contact.created",
    "Facture créée": "finance.invoice.created",
    "Facture en retard": "finance.invoice.overdue",
    "Commande créée": "sales.order.created",
    "Employé créé": "hr.employee.created",
    "Employé ajouté": "hr.employee.created",
    "Ticket urgent": "support.ticket.urgent",
    "Ticket resolved": "support.ticket.resolved",
    "Lead won": "crm.lead.won",
    "Meeting demain": "calendar.meeting.reminder",
    "Stock bas": "inventory.stock.low",
    "Webhook entrant": "webhook.inbound",
    "Planification hebdo": "schedule.weekly",
}

EVENT_CATALOG: list[dict[str, str]] = [
    {"eventType": "crm.lead.created", "label": "Lead créé", "description": "Nouveau lead CRM"},
    {"eventType": "crm.contact.created", "label": "Contact créé", "description": "Nouveau contact"},
    {"eventType": "crm.lead.won", "label": "Lead won", "description": "Lead gagné"},
    {"eventType": "finance.invoice.created", "label": "Facture créée", "description": "Facture créée"},
    {"eventType": "finance.invoice.overdue", "label": "Facture en retard", "description": "Facture overdue"},
    {"eventType": "sales.order.created", "label": "Commande créée", "description": "Commande sales"},
    {"eventType": "hr.employee.created", "label": "Employé créé", "description": "Nouvel employé"},
    {"eventType": "support.ticket.urgent", "label": "Ticket urgent", "description": "Ticket prioritaire"},
    {"eventType": "webhook.inbound", "label": "Webhook entrant", "description": "HTTP inbound"},
    {"eventType": "inventory.stock.low", "label": "Stock bas", "description": "Seuil stock"},
]


def labels_for_event(event_type: str) -> set[str]:
    labels = {item["label"] for item in EVENT_CATALOG if item["eventType"] == event_type}
    for label, mapped in TRIGGER_LABEL_TO_EVENT.items():
        if mapped == event_type:
            labels.add(label)
    labels.add(event_type)
    return labels


def event_type_for_trigger_label(label: str) -> str | None:
    if not label or label == "Manuel":
        return None
    if "." in label and " " not in label:
        return label
    return TRIGGER_LABEL_TO_EVENT.get(label)
