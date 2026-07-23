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


class ApprovalDecisionBody(BaseModel):
    decision: str = Field(min_length=1, max_length=16)  # approve | reject


class TaskCreateBody(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: str = Field(default="medium", min_length=1, max_length=16)
    status: str = Field(default="todo", min_length=1, max_length=32)
    dueDate: str
    assigneeId: str | None = None
    assigneeName: str | None = None
    projectId: str | None = None
    projectName: str | None = None
    tags: list[str] = Field(default_factory=list)


class TaskStatusUpdateBody(BaseModel):
    status: str = Field(min_length=1, max_length=32)


class TaskAssignBody(BaseModel):
    assigneeId: str = Field(min_length=1, max_length=64)
    assigneeName: str | None = None
    assigneeAvatarColor: str | None = None


class TicketCreateBody(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    customerName: str = Field(min_length=1, max_length=255)
    customerEmail: EmailStr
    priority: str = Field(default="medium", min_length=1, max_length=16)
    category: str = Field(default="Support", min_length=1, max_length=64)
    message: str | None = Field(default=None, max_length=8000)


class TicketMessageCreateBody(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    isInternal: bool = False
    author: str | None = None


class TicketStatusUpdateBody(BaseModel):
    status: str = Field(min_length=1, max_length=32)


class ProfileUpdateBody(BaseModel):
    firstName: str | None = Field(default=None, min_length=1, max_length=128)
    lastName: str | None = Field(default=None, min_length=1, max_length=128)


class PasswordChangeBody(BaseModel):
    currentPassword: str = Field(min_length=4, max_length=128)
    newPassword: str = Field(min_length=6, max_length=128)


class ForgotPasswordBody(BaseModel):
    email: EmailStr


class VerifyResetCodeBody(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=16)


class ResetPasswordBody(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=16)
    newPassword: str = Field(min_length=6, max_length=128)


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


class OrderLineItemBody(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    quantity: int = Field(ge=1)
    unitPrice: float = Field(ge=0)


class OrderCreateBody(BaseModel):
    customerName: str = Field(min_length=1, max_length=255)
    customerId: str | None = None
    status: str = "draft"
    currency: str = "EUR"
    date: str | None = None
    lineItems: list[OrderLineItemBody] = Field(min_length=1)


class OrderUpdateBody(BaseModel):
    customerName: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = None
    lineItems: list[OrderLineItemBody] | None = None


class CampaignCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: str = "email"
    status: str = "draft"
    budget: float = Field(ge=0, default=0)
    startDate: str | None = None
    endDate: str | None = None


class CampaignUpdateBody(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: str | None = None
    status: str | None = None
    budget: float | None = Field(default=None, ge=0)
    spent: float | None = Field(default=None, ge=0)
    startDate: str | None = None
    endDate: str | None = None


class ProjectCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    status: str = "planning"
    startDate: str | None = None
    endDate: str | None = None
    budget: float = Field(ge=0, default=0)
    color: str = Field(default="#4f46e5", max_length=16)


class ProjectUpdateBody(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    startDate: str | None = None
    endDate: str | None = None
    budget: float | None = Field(default=None, ge=0)
    spent: float | None = Field(default=None, ge=0)
    color: str | None = Field(default=None, max_length=16)


class CalendarEventCreateBody(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    type: str = "meeting"
    startDate: str
    endDate: str | None = None
    color: str = Field(default="#4f46e5", max_length=16)
    location: str | None = Field(default=None, max_length=255)
    attendees: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=2000)


class CalendarEventUpdateBody(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    type: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    color: str | None = Field(default=None, max_length=16)
    location: str | None = Field(default=None, max_length=255)
    attendees: list[str] | None = None
    description: str | None = Field(default=None, max_length=2000)


class MeetingCreateBody(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    date: str
    duration: int = Field(ge=5, le=600, default=30)
    location: str | None = Field(default=None, max_length=255)
    agenda: list[str] = Field(default_factory=list)


class MeetingUpdateBody(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    date: str | None = None
    duration: int | None = Field(default=None, ge=5, le=600)
    status: str | None = None
    location: str | None = Field(default=None, max_length=255)
    agenda: list[str] | None = None
    summary: str | None = Field(default=None, max_length=4000)


class WorkflowDefinitionBody(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)


class WorkflowCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=512)
    status: str = Field(default="draft", min_length=1, max_length=32)
    definition: WorkflowDefinitionBody | None = None


class WorkflowUpdateBody(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=512)
    status: str | None = Field(default=None, min_length=1, max_length=32)
    definition: WorkflowDefinitionBody | None = None


# --- Catalog CRUD (HR / Inventory / Procurement / Accounting) ---


class EmployeeCreateBody(BaseModel):
    firstName: str = Field(min_length=1, max_length=128)
    lastName: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    position: str = Field(min_length=1, max_length=128)
    department: str = Field(min_length=1, max_length=128)
    startDate: str | None = None
    status: str = "active"
    salary: float | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=128)
    managerId: str | None = None
    avatarColor: str | None = Field(default=None, max_length=64)


class EmployeeUpdateBody(BaseModel):
    firstName: str | None = Field(default=None, min_length=1, max_length=128)
    lastName: str | None = Field(default=None, min_length=1, max_length=128)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    position: str | None = Field(default=None, min_length=1, max_length=128)
    department: str | None = Field(default=None, min_length=1, max_length=128)
    startDate: str | None = None
    status: str | None = None
    salary: float | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=128)
    managerId: str | None = None
    avatarColor: str | None = Field(default=None, max_length=64)


class JobCreateBody(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    department: str = Field(min_length=1, max_length=128)
    status: str = "open"
    location: str = Field(min_length=1, max_length=128)
    type: str = "full_time"
    postedDate: str | None = None


class JobUpdateBody(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = Field(default=None, min_length=1, max_length=128)
    status: str | None = None
    location: str | None = Field(default=None, min_length=1, max_length=128)
    type: str | None = None
    applicants: int | None = Field(default=None, ge=0)


class CandidateCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    jobId: str | None = None
    jobTitle: str | None = Field(default=None, max_length=255)
    stage: str = "applied"
    score: int = Field(default=0, ge=0, le=100)
    avatarColor: str | None = Field(default=None, max_length=64)
    appliedAt: str | None = None


class CandidateUpdateBody(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    jobId: str | None = None
    jobTitle: str | None = Field(default=None, max_length=255)
    stage: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    avatarColor: str | None = Field(default=None, max_length=64)


class InventoryItemCreateBody(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=128)
    quantity: int = Field(default=0, ge=0)
    reorderLevel: int = Field(default=0, ge=0)
    warehouse: str = Field(min_length=1, max_length=128)
    unitPrice: float = Field(default=0, ge=0)
    status: str | None = None


class InventoryItemUpdateBody(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, min_length=1, max_length=128)
    quantity: int | None = Field(default=None, ge=0)
    reorderLevel: int | None = Field(default=None, ge=0)
    warehouse: str | None = Field(default=None, min_length=1, max_length=128)
    unitPrice: float | None = Field(default=None, ge=0)
    status: str | None = None


class SupplierCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    rating: float = Field(default=4.0, ge=0, le=5)
    country: str = Field(default="", max_length=64)
    status: str = "active"


class SupplierUpdateBody(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    rating: float | None = Field(default=None, ge=0, le=5)
    country: str | None = Field(default=None, max_length=64)
    status: str | None = None


class PurchaseOrderCreateBody(BaseModel):
    supplierId: str | None = None
    supplierName: str = Field(min_length=1, max_length=255)
    status: str = "draft"
    totalAmount: float = Field(default=0, ge=0)
    currency: str = "EUR"
    expectedAt: str | None = None
    itemCount: int = Field(default=1, ge=0)


class PurchaseOrderUpdateBody(BaseModel):
    supplierId: str | None = None
    supplierName: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = None
    totalAmount: float | None = Field(default=None, ge=0)
    currency: str | None = None
    expectedAt: str | None = None
    itemCount: int | None = Field(default=None, ge=0)


class TransactionCreateBody(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    amount: float = Field(gt=0)
    type: str = "expense"
    category: str = Field(min_length=1, max_length=128)
    date: str | None = None
    account: str = Field(min_length=1, max_length=128)


class TransactionUpdateBody(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount: float | None = Field(default=None, gt=0)
    type: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=128)
    date: str | None = None
    account: str | None = Field(default=None, min_length=1, max_length=128)
