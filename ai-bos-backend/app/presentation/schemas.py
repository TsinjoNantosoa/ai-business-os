from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class ContactCreateBody(BaseModel):
    firstName: str = Field(min_length=1, max_length=128)
    lastName: str = Field(min_length=1, max_length=128)
    email: EmailStr
    company: str = Field(min_length=1, max_length=255)
    phone: str | None = None
    position: str | None = None
    status: str = "active"
    tags: list[str] = Field(default_factory=list)


class ContactUpdateBody(BaseModel):
    firstName: str | None = None
    lastName: str | None = None
    email: EmailStr | None = None
    company: str | None = None
    phone: str | None = None
    position: str | None = None
    status: str | None = None
    tags: list[str] | None = None


class CheckoutBody(BaseModel):
    planCode: str = Field(min_length=1, max_length=32)


class LeadCreateBody(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    contactName: str = Field(min_length=1, max_length=255)
    value: int = Field(ge=0)
    currency: str = "EUR"
    stage: str = "new"
    expectedCloseDate: str


class LeadStageUpdateBody(BaseModel):
    stage: str = Field(min_length=1, max_length=32)


class InvoiceLineItemBody(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    quantity: int = Field(ge=1)
    unitPrice: int = Field(ge=0)
    taxRate: int = Field(ge=0, le=100, default=20)


class InvoiceCreateBody(BaseModel):
    clientId: str = Field(min_length=1, max_length=64)
    clientName: str = Field(min_length=1, max_length=255)
    currency: str = "EUR"
    issueDate: str | None = None
    dueDate: str | None = None
    lineItems: list[InvoiceLineItemBody] = Field(min_length=1)


class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    agentId: str | None = None
    context: str | None = None
    conversationId: str | None = None


class TaskStatusUpdateBody(BaseModel):
    status: str = Field(min_length=1, max_length=32)


class TaskAssignBody(BaseModel):
    assigneeId: str = Field(min_length=1, max_length=64)
    assigneeName: str | None = None
    assigneeAvatarColor: str | None = None


class TicketMessageCreateBody(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    isInternal: bool = False
    author: str | None = None


class TicketStatusUpdateBody(BaseModel):
    status: str = Field(min_length=1, max_length=32)


class OrganizationUpdateBody(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    currency: str | None = Field(default=None, min_length=1, max_length=8)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    locale: str | None = Field(default=None, min_length=1, max_length=8)
    address: str | None = Field(default=None, max_length=512)


class InvitationCreateBody(BaseModel):
    email: EmailStr
    role: str = Field(default="staff", min_length=1, max_length=64)
    message: str | None = Field(default=None, max_length=1000)


class InvitationAcceptBody(BaseModel):
    token: str = Field(min_length=10, max_length=128)
    firstName: str = Field(min_length=1, max_length=128)
    lastName: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=6, max_length=128)
