// ============================================================
// AI BOS — API Types (matching future backend API)
// ============================================================

// --- Auth ---
export type Role =
  | 'owner'
  | 'admin'
  | 'sales_manager'
  | 'finance_manager'
  | 'hr_manager'
  | 'project_manager'
  | 'staff'
  | 'viewer';

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  avatarUrl?: string;
  role: Role;
  permissions: string[];
  orgId: string;
  jobTitle?: string;
  department?: string;
  phone?: string;
  twoFactorEnabled?: boolean;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
}

export interface OAuthProvider {
  id: string;
  enabled: boolean;
  mode: 'mock' | 'live' | string;
}

export interface OAuthStartResponse {
  provider: string;
  mode: string;
  state: string;
  authorizationUrl: string;
}

export interface GdprExport {
  exportVersion: string;
  subject: { userId: string; orgId: string };
  organization: Organization | null;
  user: TeamMember | null;
  contacts: Contact[];
  leads: Lead[];
  activitiesCount: number;
  invoicesCount: number;
  tasks: Task[];
  ticketsCount: number;
  documentsCount: number;
  notifications: AppNotification[];
  auditLogsCount: number;
  note?: string;
}

export interface Organization {
  id: string;
  name: string;
  logoUrl?: string;
  plan: 'starter' | 'pro' | 'enterprise';
  currency: string;
  timezone: string;
  locale: string;
  address?: string | null;
}

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  status: string;
  firstName?: string;
  lastName?: string;
}

export interface Invitation {
  id: string;
  orgId: string;
  email: string;
  role: string;
  status: 'pending' | 'accepted' | 'revoked' | string;
  invitedBy: string;
  invitedByName: string;
  message?: string | null;
  createdAt: string;
  expiresAt: string;
  acceptedAt?: string | null;
  token?: string;
  organizationName?: string;
}

export interface FeatureFlag {
  key: string;
  name: string;
  description: string;
  env: string;
  enabled: boolean;
  source?: 'override' | 'plan' | 'default' | string;
  plan?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  keyPrefix: string;
  maskedKey: string;
  scopes: string[];
  active: boolean;
  createdBy: string;
  createdByName: string;
  createdAt: string;
  lastUsedAt?: string | null;
  revokedAt?: string | null;
  secret?: string;
}

// --- CRM ---
export type ContactStatus = 'active' | 'inactive' | 'lead' | 'archived';

export interface Contact {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  company: string;
  position?: string;
  status: ContactStatus;
  ownerId: string;
  ownerName?: string;
  tags: string[];
  lastActivityAt: string;
  createdAt: string;
  avatarColor?: string;
}

export type LeadStage = 'new' | 'qualified' | 'proposal' | 'negotiation' | 'won' | 'lost';

export interface Lead {
  id: string;
  title: string;
  company: string;
  contactName: string;
  value: number;
  currency: string;
  stage: LeadStage;
  probability: number;
  ownerId: string;
  ownerName: string;
  ownerAvatarColor: string;
  expectedCloseDate: string;
  daysInStage: number;
  createdAt: string;
}

export interface Activity {
  id: string;
  type: 'call' | 'email' | 'meeting' | 'note' | 'task';
  description: string;
  contactId?: string;
  userId: string;
  userName: string;
  createdAt: string;
}

// --- Sales ---
export type OrderStatus = 'draft' | 'sent' | 'accepted' | 'fulfilled' | 'invoiced' | 'cancelled';

export interface OrderLineItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
}

export interface Order {
  id: string;
  orderNumber: string;
  customerId: string;
  customerName: string;
  status: OrderStatus;
  amount: number;
  currency: string;
  date: string;
  salesRepId: string;
  salesRepName: string;
  lineItems: OrderLineItem[];
}

// --- Finance ---
export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';

export interface InvoiceLineItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  taxRate: number;
  total: number;
}

export interface Invoice {
  id: string;
  invoiceNumber: string;
  clientId: string;
  clientName: string;
  amount: number;
  taxAmount: number;
  totalAmount: number;
  currency: string;
  status: InvoiceStatus;
  issueDate: string;
  dueDate: string;
  paidDate?: string;
  lineItems: InvoiceLineItem[];
}

export interface FinanceOverview {
  cashBalance: number;
  arOutstanding: number;
  apOutstanding: number;
  burnRate: number;
  monthlyRevenue: { month: string; revenue: number; expenses: number }[];
  agingReceivables: { bucket: string; amount: number }[];
  recentTransactions: Transaction[];
}

export interface Transaction {
  id: string;
  description: string;
  amount: number;
  type: 'income' | 'expense';
  category: string;
  date: string;
  account: string;
}

// --- Projects & Tasks ---
export type ProjectStatus = 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled';
export type TaskStatus = 'todo' | 'in_progress' | 'review' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Project {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  progress: number;
  startDate: string;
  endDate: string;
  budget: number;
  spent: number;
  teamMembers: { id: string; name: string; avatarColor: string; role: string }[];
  taskCount: number;
  completedTasks: number;
  color: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assigneeId: string;
  assigneeName: string;
  assigneeAvatarColor: string;
  projectId?: string;
  projectName?: string;
  dueDate: string;
  tags: string[];
  createdAt: string;
}

// --- Calendar & Meetings ---
export interface CalendarEvent {
  id: string;
  title: string;
  type: 'meeting' | 'deadline' | 'reminder' | 'call' | 'task';
  startDate: string;
  endDate: string;
  color: string;
  location?: string;
  attendees?: string[];
  description?: string;
}

export interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: number;
  attendees: { id: string; name: string; avatarColor: string }[];
  agenda: string[];
  summary?: string;
  actionItems: { id: string; text: string; done: boolean; assignee: string }[];
  status: 'upcoming' | 'completed' | 'cancelled';
  location?: string;
}

// --- Documents ---
export interface DocumentItem {
  id: string;
  name: string;
  type: 'pdf' | 'docx' | 'xlsx' | 'image' | 'folder';
  size: number;
  parentId?: string;
  modifiedAt: string;
  modifiedBy: string;
  starred?: boolean;
  hasFile?: boolean;
}

// --- HR ---
export interface Employee {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  position: string;
  department: string;
  managerId?: string;
  managerName?: string;
  startDate: string;
  status: 'active' | 'on_leave' | 'terminated';
  avatarColor: string;
  salary?: number;
  location?: string;
}

export interface JobOpening {
  id: string;
  title: string;
  department: string;
  status: 'open' | 'paused' | 'closed';
  applicants: number;
  postedDate: string;
  location: string;
  type: 'full_time' | 'part_time' | 'contract' | 'internship';
}

export interface Candidate {
  id: string;
  name: string;
  email: string;
  jobId: string;
  jobTitle: string;
  stage: 'applied' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected';
  score: number;
  avatarColor: string;
  appliedAt: string;
}

// --- Marketing ---
export type CampaignStatus = 'draft' | 'scheduled' | 'active' | 'completed' | 'paused';

export interface Campaign {
  id: string;
  name: string;
  type: 'email' | 'social' | 'sms' | 'webinar' | 'ads' | 'content';
  status: CampaignStatus;
  reach: number;
  openRate: number;
  clickRate: number;
  conversions: number;
  budget: number;
  spent: number;
  startDate: string;
  endDate?: string;
}

// --- Support ---
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';
export type TicketStatus = 'open' | 'pending' | 'resolved' | 'closed';

export interface Ticket {
  id: string;
  ticketNumber: string;
  subject: string;
  customerName: string;
  customerEmail: string;
  priority: TicketPriority;
  status: TicketStatus;
  agentId?: string;
  agentName?: string;
  createdAt: string;
  updatedAt: string;
  slaDeadline: string;
  category: string;
  messages: { id: string; author: string; content: string; createdAt: string; isInternal: boolean }[];
}

// --- Contracts ---
export interface Contract {
  id: string;
  title: string;
  type: 'service' | 'nda' | 'employment' | 'vendor' | 'lease';
  counterparty: string;
  value: number;
  currency: string;
  startDate: string;
  endDate: string;
  status: 'active' | 'expiring' | 'expired' | 'draft';
  owner: string;
}

// --- Knowledge Base ---
export interface KnowledgeArticle {
  id: string;
  title: string;
  category: string;
  excerpt: string;
  content: string;
  author: string;
  updatedAt: string;
  views: number;
  helpful: number;
}

export interface KnowledgeSearchHit {
  documentId: string;
  documentTitle: string;
  chunkId: string;
  relevanceScore: number;
  excerpt: string;
  sourceUri?: string | null;
}

export interface KnowledgeSearchResponse {
  query: string;
  items: KnowledgeSearchHit[];
}

export interface KnowledgeStats {
  chunkCount: number;
  documentCount: number;
}

// --- Analytics & BI ---
export interface AnalyticsData {
  kpis: { label: string; value: number; change: number; unit: string }[];
  revenue: { month: string; revenue: number; target: number }[];
  users: { month: string; active: number; new: number }[];
  conversion: { stage: string; value: number; rate: number }[];
  churn: { month: string; rate: number }[];
}

export interface BIReport {
  id: string;
  name: string;
  description: string;
  category: string;
  chartType: 'bar' | 'line' | 'pie' | 'area';
  lastRun: string;
  schedule?: string;
}

// --- ML Forecasts ---
export interface ForecastData {
  horizon: '7d' | '30d' | '90d';
  data: { date: string; actual?: number; forecast: number; lower: number; upper: number }[];
  model: {
    name: string;
    version: string;
    mae: number;
    lastTrained: string;
    confidence: number;
  };
  recommendations: string[];
}

// --- Workflows ---
export type WorkflowStatus = 'active' | 'inactive' | 'draft';

export interface WorkflowGraphNode {
  id: string;
  type: 'trigger' | 'action' | string;
  position: { x: number; y: number };
  data: { label: string; kind?: string };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface WorkflowDefinition {
  nodes: WorkflowGraphNode[];
  edges: WorkflowEdge[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: WorkflowStatus;
  trigger: string;
  actions: string[];
  definition?: WorkflowDefinition;
  lastRun?: string;
  runCount: number;
  successRate: number;
}

export type WorkflowExecutionStatus = 'running' | 'success' | 'error';

export interface WorkflowExecution {
  id: string;
  workflowId: string;
  workflowName?: string;
  status: WorkflowExecutionStatus;
  startedAt: string;
  finishedAt?: string;
  durationMs?: number;
  resultMessage?: string;
  errorMessage?: string;
}

export interface WorkflowRunResult {
  execution: WorkflowExecution;
  workflow: Workflow;
}

export interface WorkflowUpsertPayload {
  name: string;
  description?: string;
  status?: WorkflowStatus;
  definition?: WorkflowDefinition;
}

// --- AI Agents ---
export type AgentStatus = 'active' | 'idle' | 'error';

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: AgentStatus;
  category: string;
  icon: string;
  toolsCount: number;
  lastUsed?: string;
  conversations: number;
}

// --- Inventory ---
export interface InventoryItem {
  id: string;
  sku: string;
  name: string;
  category: string;
  quantity: number;
  reorderLevel: number;
  warehouse: string;
  unitPrice: number;
  status: 'in_stock' | 'low_stock' | 'out_of_stock';
}

// --- Notifications ---
export interface AppNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
  link?: string;
}

// --- Audit Logs ---
export interface AuditLog {
  id: string;
  timestamp: string;
  userId: string;
  userName: string;
  action: string;
  resource: string;
  resourceId?: string;
  ip: string;
  details?: string;
}

// --- Copilot ---
export interface CopilotMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  agentId?: string;
}

export interface CopilotConversation {
  id: string;
  title: string;
  messages: CopilotMessage[];
  createdAt: string;
  updatedAt: string;
}

// --- Procurement ---
export type PurchaseOrderStatus =
  | 'draft'
  | 'submitted'
  | 'approved'
  | 'received'
  | 'cancelled'

export type SupplierStatus = 'active' | 'paused' | 'blacklisted'

export interface Supplier {
  id: string
  name: string
  email: string
  phone?: string
  rating: number // 0..5
  country: string
  status: SupplierStatus
}

export interface PurchaseOrder {
  id: string
  poNumber: string
  supplierId?: string
  supplierName: string
  status: PurchaseOrderStatus
  totalAmount: number
  currency: string
  createdAt: string
  expectedAt: string
  ownerName: string
  itemCount: number
}

// --- Billing ---
export interface BillingPlan {
  id: string
  code: 'starter' | 'pro' | 'enterprise' | string
  name: string
  priceMonthly: number
  currency: string
  seatsLimit: number
  aiTokensLimit: number
  storageGbLimit: number
}

export interface BillingUsageMeter {
  used: number
  limit: number
}

export interface BillingSubscription {
  id: string
  orgId: string
  status: string
  plan: BillingPlan
  currentPeriodStart: string
  currentPeriodEnd: string
  renewalDate: string
  usage: {
    seats: BillingUsageMeter
    aiTokens: BillingUsageMeter
    storageGb: BillingUsageMeter
  }
}

export interface BillingInvoice {
  id: string
  invoiceNumber: string
  amount: number
  currency: string
  status: string
  periodStart: string
  periodEnd: string
  createdAt: string
  pdfUrl?: string
}

export interface BillingOverview {
  subscription: BillingSubscription
  invoices: BillingInvoice[]
}

export interface CheckoutSession {
  sessionId: string
  checkoutUrl: string
}
