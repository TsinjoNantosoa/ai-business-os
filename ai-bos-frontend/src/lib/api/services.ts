// ============================================================
// AI BOS — API Services
// Every service: try apiFetch → catch → return mock data
// ============================================================

import { apiFetch, USE_MOCKS, API_URL } from './client';
import type * as T from './types';

// --- Auth ---
export async function login(email: string, password: string): Promise<T.AuthResponse> {
  if (USE_MOCKS) {
    const { DEMO_USERS, DEMO_PASSWORD } = await import('./mocks/auth');
    const user = DEMO_USERS[email];
    if (!user || password !== DEMO_PASSWORD) throw new Error('Invalid credentials');
    return { user, token: `mock-token-${user.id}`, refreshToken: `mock-refresh-${user.id}` };
  }
  return apiFetch<T.AuthResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function forgotPassword(email: string): Promise<{ status: string; message: string }> {
  if (USE_MOCKS) {
    return {
      status: 'ok',
      message: 'Si ce compte existe, un code de vérification a été envoyé.',
    };
  }
  return apiFetch<{ status: string; message: string }>('/api/v1/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export async function verifyResetCode(email: string, code: string): Promise<{ status: string }> {
  if (USE_MOCKS) return { status: 'ok' };
  return apiFetch<{ status: string }>('/api/v1/auth/verify-reset-code', {
    method: 'POST',
    body: JSON.stringify({ email, code }),
  });
}

export async function resetPassword(
  email: string,
  code: string,
  newPassword: string,
): Promise<{ status: string }> {
  if (USE_MOCKS) return { status: 'ok' };
  return apiFetch<{ status: string }>('/api/v1/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ email, code, newPassword }),
  });
}

export async function getOAuthProviders(): Promise<T.OAuthProvider[]> {
  if (USE_MOCKS) {
    return [
      { id: 'google', enabled: true, mode: 'mock' },
      { id: 'microsoft', enabled: true, mode: 'mock' },
    ];
  }
  const res = await apiFetch<{ items: T.OAuthProvider[] }>('/api/v1/auth/oauth/providers');
  return res.items;
}

export async function startOAuth(provider: string): Promise<T.OAuthStartResponse> {
  return apiFetch<T.OAuthStartResponse>(`/api/v1/auth/oauth/${provider}/authorize`);
}

export async function mockOAuthLogin(provider: string, state: string, email: string): Promise<T.AuthResponse> {
  return apiFetch<T.AuthResponse>(`/api/v1/auth/oauth/${provider}/mock-login`, {
    method: 'POST',
    body: JSON.stringify({ state, email }),
  });
}

export async function exchangeOAuthCode(code: string): Promise<T.AuthResponse> {
  return apiFetch<T.AuthResponse>('/api/v1/auth/oauth/exchange', {
    method: 'POST',
    body: JSON.stringify({ code }),
  });
}

export async function exportGdprData(): Promise<T.GdprExport> {
  return apiFetch<T.GdprExport>('/api/v1/platform/gdpr/export');
}

export async function requestGdprErase(): Promise<{ status: string; userId: string; active: boolean }> {
  return apiFetch('/api/v1/platform/gdpr/erase-request', { method: 'POST' });
}

export async function getMe(): Promise<T.User> {
  if (USE_MOCKS) {
    const { DEMO_USERS } = await import('./mocks/auth');
    return DEMO_USERS['ceo@demo.aibos.io'];
  }
  return apiFetch<T.User>('/api/v1/auth/me');
}

export async function updateProfile(payload: {
  firstName?: string
  lastName?: string
}): Promise<T.User> {
  return apiFetch<T.User>('/api/v1/auth/me', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function changePassword(payload: {
  currentPassword: string
  newPassword: string
}): Promise<{ status: string }> {
  return apiFetch<{ status: string }>('/api/v1/auth/change-password', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// --- Organizations ---
export async function getOrganizations(): Promise<T.Organization[]> {
  if (USE_MOCKS) {
    const { ORGANIZATIONS } = await import('./mocks/auth');
    return ORGANIZATIONS;
  }
  return apiFetch<T.Organization[]>('/api/v1/platform/organizations');
}

export async function getMyOrganization(): Promise<T.Organization> {
  if (USE_MOCKS) {
    const { ORGANIZATIONS } = await import('./mocks/auth');
    return ORGANIZATIONS[0];
  }
  return apiFetch<T.Organization>('/api/v1/platform/organizations/me');
}

export async function updateMyOrganization(payload: {
  name?: string;
  currency?: string;
  timezone?: string;
  locale?: string;
  address?: string;
}): Promise<T.Organization> {
  return apiFetch<T.Organization>('/api/v1/platform/organizations/me', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function getTeamMembers(): Promise<T.TeamMember[]> {
  if (USE_MOCKS) {
    return [
      { id: '1', name: 'Jean Bernard', email: 'ceo@demo.aibos.io', role: 'owner', status: 'active' },
      { id: '2', name: 'Lucas Thomas', email: 'staff@demo.aibos.io', role: 'staff', status: 'active' },
    ];
  }
  return apiFetch<T.TeamMember[]>('/api/v1/platform/team');
}

export async function getInvitations(): Promise<T.Invitation[]> {
  if (USE_MOCKS) return [];
  return apiFetch<T.Invitation[]>('/api/v1/platform/invitations');
}

export async function createInvitation(payload: {
  email: string;
  role?: string;
  message?: string;
}): Promise<T.Invitation> {
  return apiFetch<T.Invitation>('/api/v1/platform/invitations', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function revokeInvitation(invitationId: string): Promise<T.Invitation> {
  return apiFetch<T.Invitation>(`/api/v1/platform/invitations/${encodeURIComponent(invitationId)}/revoke`, {
    method: 'POST',
  });
}

export async function acceptInvitation(payload: {
  token: string;
  firstName: string;
  lastName: string;
  password: string;
}): Promise<T.TeamMember> {
  return apiFetch<T.TeamMember>('/api/v1/platform/invitations/accept', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getFeatureFlags(): Promise<T.FeatureFlag[]> {
  if (USE_MOCKS) {
    return [
      { key: 'ai.copilot', name: 'AI Copilot', description: 'Activer le copilote IA', env: 'production', enabled: true, source: 'plan' },
      { key: 'ml.forecasts', name: 'ML Forecasts', description: 'Prévisions machine learning', env: 'beta', enabled: true, source: 'plan' },
    ];
  }
  return apiFetch<T.FeatureFlag[]>('/api/v1/platform/feature-flags');
}

export async function getAdminFeatureFlags(): Promise<T.FeatureFlag[]> {
  if (USE_MOCKS) return getFeatureFlags();
  return apiFetch<T.FeatureFlag[]>('/api/v1/admin/feature-flags');
}

export async function updateFeatureFlag(
  key: string,
  payload: { enabled: boolean; reset?: boolean },
): Promise<T.FeatureFlag> {
  return apiFetch<T.FeatureFlag>(`/api/v1/admin/feature-flags/${encodeURIComponent(key)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function getApiKeys(): Promise<T.ApiKey[]> {
  if (USE_MOCKS) {
    return [
      {
        id: 'key-1',
        name: 'Production API',
        keyPrefix: 'aibos_sk_live',
        maskedKey: 'aibos_sk_live••••••••••••••••',
        scopes: ['crm.contact.read'],
        active: true,
        createdBy: 'u-1',
        createdByName: 'Jean Bernard',
        createdAt: new Date().toISOString(),
      },
    ];
  }
  return apiFetch<T.ApiKey[]>('/api/v1/platform/api-keys');
}

export async function createApiKey(payload: { name: string; scopes?: string[] }): Promise<T.ApiKey> {
  return apiFetch<T.ApiKey>('/api/v1/platform/api-keys', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function revokeApiKey(id: string): Promise<void> {
  await apiFetch<void>(`/api/v1/platform/api-keys/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}

// --- Notifications ---
export async function getNotifications(): Promise<T.AppNotification[]> {
  if (USE_MOCKS) {
    const { MOCK_NOTIFICATIONS } = await import('./mocks/auth');
    return MOCK_NOTIFICATIONS;
  }
  return apiFetch<T.AppNotification[]>('/api/v1/platform/notifications');
}

export async function markNotificationRead(id: string): Promise<T.AppNotification> {
  return apiFetch<T.AppNotification>(`/api/v1/platform/notifications/${encodeURIComponent(id)}/read`, {
    method: 'POST',
  });
}

export async function markAllNotificationsRead(): Promise<{ updated: number }> {
  return apiFetch<{ updated: number }>('/api/v1/platform/notifications/read-all', {
    method: 'POST',
  });
}

export function subscribeNotifications(
  onEvent: (payload: { type: string; notification?: T.AppNotification; orgId?: string }) => void,
): () => void {
  if (USE_MOCKS || typeof window === 'undefined' || typeof EventSource === 'undefined') {
    return () => undefined;
  }

  let closed = false;
  let source: EventSource | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;

  const connect = async () => {
    if (closed) return;
    const { useAuth } = await import('@/lib/auth/store');
    const token = useAuth.getState().token;
    if (!token) return;
    const url = `${API_URL}/api/v1/platform/notifications/stream?access_token=${encodeURIComponent(token)}`;
    source = new EventSource(url);
    source.onmessage = (event) => {
      try {
        onEvent(JSON.parse(event.data));
      } catch {
        /* ignore malformed */
      }
    };
    source.onerror = () => {
      source?.close();
      source = null;
      if (!closed) timer = setTimeout(() => void connect(), 3000);
    };
  };

  void connect();

  return () => {
    closed = true;
    if (timer) clearTimeout(timer);
    source?.close();
  };
}

// --- CRM Contacts ---
export async function getContacts(): Promise<T.Contact[]> {
  if (USE_MOCKS) {
    const { MOCK_CONTACTS } = await import('./mocks/crm');
    return MOCK_CONTACTS;
  }
  return apiFetch<T.Contact[]>('/api/v1/crm/contacts');
}

export async function getActivities(): Promise<T.Activity[]> {
  if (USE_MOCKS) {
    const { MOCK_ACTIVITIES } = await import('./mocks/crm');
    return MOCK_ACTIVITIES;
  }
  return apiFetch<T.Activity[]>('/api/v1/crm/activities');
}

// --- CRM Leads ---
export async function getLeads(): Promise<T.Lead[]> {
  if (USE_MOCKS) {
    const { MOCK_LEADS } = await import('./mocks/crm');
    return MOCK_LEADS;
  }
  return apiFetch<T.Lead[]>('/api/v1/crm/leads');
}

// --- Sales Orders ---
export async function getOrders(): Promise<T.Order[]> {
  if (USE_MOCKS) {
    const { MOCK_ORDERS } = await import('./mocks/finance');
    return MOCK_ORDERS;
  }
  return apiFetch<T.Order[]>('/api/v1/sales/orders');
}

// --- Finance ---
export async function getFinanceOverview(): Promise<T.FinanceOverview> {
  if (USE_MOCKS) {
    const { MOCK_FINANCE_OVERVIEW } = await import('./mocks/finance');
    return MOCK_FINANCE_OVERVIEW;
  }
  return apiFetch<T.FinanceOverview>('/api/v1/finance/overview');
}

export async function getInvoices(): Promise<T.Invoice[]> {
  if (USE_MOCKS) {
    const { MOCK_INVOICES } = await import('./mocks/finance');
    return MOCK_INVOICES;
  }
  return apiFetch<T.Invoice[]>('/api/v1/finance/invoices');
}

// --- Projects ---
export async function getProjects(): Promise<T.Project[]> {
  if (USE_MOCKS) {
    const { MOCK_PROJECTS } = await import('./mocks/projects');
    return MOCK_PROJECTS;
  }
  return apiFetch<T.Project[]>('/api/v1/projects');
}

// --- Tasks ---
export async function getTasks(): Promise<T.Task[]> {
  if (USE_MOCKS) {
    const { MOCK_TASKS } = await import('./mocks/projects');
    return MOCK_TASKS;
  }
  return apiFetch<T.Task[]>('/api/v1/tasks');
}

export async function updateTaskStatus(taskId: string, status: T.TaskStatus): Promise<T.Task> {
  return apiFetch<T.Task>(`/api/v1/tasks/${taskId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export async function createTask(payload: {
  title: string
  description?: string
  priority?: string
  status?: string
  dueDate: string
  assigneeId?: string
  assigneeName?: string
  projectId?: string
  projectName?: string
  tags?: string[]
}): Promise<T.Task> {
  return apiFetch<T.Task>('/api/v1/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function assignTask(
  taskId: string,
  payload: { assigneeId: string; assigneeName?: string; assigneeAvatarColor?: string },
): Promise<T.Task> {
  return apiFetch<T.Task>(`/api/v1/tasks/${taskId}/assign`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

// --- HR ---
export async function getEmployees(): Promise<T.Employee[]> {
  if (USE_MOCKS) {
    const { MOCK_EMPLOYEES } = await import('./mocks/projects');
    return MOCK_EMPLOYEES;
  }
  return apiFetch<T.Employee[]>('/api/v1/hr/employees');
}

export async function getJobOpenings(): Promise<T.JobOpening[]> {
  if (USE_MOCKS) {
    const { MOCK_JOB_OPENINGS } = await import('./mocks/projects');
    return MOCK_JOB_OPENINGS;
  }
  return apiFetch<T.JobOpening[]>('/api/v1/hr/jobs');
}

export async function getCandidates(): Promise<T.Candidate[]> {
  if (USE_MOCKS) {
    const { MOCK_CANDIDATES } = await import('./mocks/projects');
    return MOCK_CANDIDATES;
  }
  return apiFetch<T.Candidate[]>('/api/v1/hr/candidates');
}

// --- Marketing ---
export async function getCampaigns(): Promise<T.Campaign[]> {
  if (USE_MOCKS) {
    const { MOCK_CAMPAIGNS } = await import('./mocks/operations');
    return MOCK_CAMPAIGNS;
  }
  return apiFetch<T.Campaign[]>('/api/v1/marketing/campaigns');
}

// --- Support ---
export async function getTickets(): Promise<T.Ticket[]> {
  if (USE_MOCKS) {
    const { MOCK_TICKETS } = await import('./mocks/operations');
    return MOCK_TICKETS;
  }
  return apiFetch<T.Ticket[]>('/api/v1/support/tickets');
}

export async function createTicket(payload: {
  subject: string
  customerName: string
  customerEmail: string
  priority?: string
  category?: string
  message?: string
}): Promise<T.Ticket> {
  return apiFetch<T.Ticket>('/api/v1/support/tickets', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function replyToTicket(
  ticketId: string,
  payload: { content: string; isInternal?: boolean; author?: string },
): Promise<T.Ticket> {
  return apiFetch<T.Ticket>(`/api/v1/support/tickets/${ticketId}/messages`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateTicketStatus(ticketId: string, status: T.TicketStatus): Promise<T.Ticket> {
  return apiFetch<T.Ticket>(`/api/v1/support/tickets/${ticketId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

// --- Contracts ---
export async function getContracts(): Promise<T.Contract[]> {
  if (USE_MOCKS) {
    const { MOCK_CONTRACTS } = await import('./mocks/operations');
    return MOCK_CONTRACTS;
  }
  return apiFetch<T.Contract[]>('/api/v1/contracts');
}

// --- Knowledge ---
export async function getArticles(): Promise<T.KnowledgeArticle[]> {
  if (USE_MOCKS) {
    const { MOCK_ARTICLES } = await import('./mocks/operations');
    return MOCK_ARTICLES;
  }
  return apiFetch<T.KnowledgeArticle[]>('/api/v1/knowledge/articles');
}

export async function searchKnowledge(query: string, limit = 5): Promise<T.KnowledgeSearchResponse> {
  if (USE_MOCKS) {
    const articles = await getArticles();
    const q = query.toLowerCase();
    return {
      query,
      items: articles
        .filter((a) => a.title.toLowerCase().includes(q) || a.excerpt.toLowerCase().includes(q))
        .slice(0, limit)
        .map((a) => ({
          documentId: a.id,
          documentTitle: a.title,
          chunkId: a.id,
          relevanceScore: 1,
          excerpt: a.excerpt,
          sourceUri: null,
        })),
    };
  }
  return apiFetch<T.KnowledgeSearchResponse>(
    `/api/v1/knowledge/search?q=${encodeURIComponent(query)}&limit=${limit}`,
  );
}

export async function getKnowledgeStats(): Promise<T.KnowledgeStats> {
  if (USE_MOCKS) return { chunkCount: 12, documentCount: 12 };
  return apiFetch<T.KnowledgeStats>('/api/v1/knowledge/stats');
}

// --- Workflows ---
export async function getWorkflows(): Promise<T.Workflow[]> {
  if (USE_MOCKS) {
    const { MOCK_WORKFLOWS } = await import('./mocks/operations');
    return MOCK_WORKFLOWS;
  }
  return apiFetch<T.Workflow[]>('/api/v1/workflows');
}

export async function runWorkflow(workflowId: string): Promise<T.WorkflowRunResult> {
  return apiFetch<T.WorkflowRunResult>(`/api/v1/workflows/${workflowId}/run`, { method: 'POST' });
}

export async function getWorkflowExecutions(): Promise<T.WorkflowExecution[]> {
  return apiFetch<T.WorkflowExecution[]>('/api/v1/workflows/executions');
}

// --- Agents ---
export async function getAgents(): Promise<T.Agent[]> {
  if (USE_MOCKS) {
    const { MOCK_AGENTS } = await import('./mocks/operations');
    return MOCK_AGENTS;
  }
  return apiFetch<T.Agent[]>('/api/v1/ai/agents');
}

// --- Inventory ---
export async function getInventory(): Promise<T.InventoryItem[]> {
  if (USE_MOCKS) {
    const { MOCK_INVENTORY } = await import('./mocks/operations');
    return MOCK_INVENTORY;
  }
  return apiFetch<T.InventoryItem[]>('/api/v1/inventory/items');
}

// --- Calendar ---
export async function getEvents(): Promise<T.CalendarEvent[]> {
  if (USE_MOCKS) {
    const { MOCK_EVENTS } = await import('./mocks/operations');
    return MOCK_EVENTS;
  }
  return apiFetch<T.CalendarEvent[]>('/api/v1/calendar/events');
}

// --- Meetings ---
export async function getMeetings(): Promise<T.Meeting[]> {
  if (USE_MOCKS) {
    const { MOCK_MEETINGS } = await import('./mocks/operations');
    return MOCK_MEETINGS;
  }
  return apiFetch<T.Meeting[]>('/api/v1/meetings');
}

// --- Documents ---
export async function getDocuments(): Promise<T.DocumentItem[]> {
  if (USE_MOCKS) {
    const { MOCK_DOCUMENTS } = await import('./mocks/operations');
    return MOCK_DOCUMENTS;
  }
  return apiFetch<T.DocumentItem[]>('/api/v1/documents');
}

export async function uploadDocument(file: File, parentId?: string): Promise<T.DocumentItem> {
  const { useAuth } = await import('@/lib/auth/store');
  const auth = useAuth.getState();
  const form = new FormData();
  form.append('file', file);
  if (parentId) form.append('parentId', parentId);

  const res = await fetch(`${API_URL}/api/v1/documents/upload`, {
    method: 'POST',
    headers: {
      Authorization: auth.token ? `Bearer ${auth.token}` : '',
      'X-Correlation-ID': crypto.randomUUID(),
      'X-Tenant-Id': auth.orgId || '',
    },
    body: form,
  });
  if (!res.ok) {
    throw new Error(`Upload failed: ${res.status}`);
  }
  return res.json();
}

export async function downloadDocument(documentId: string, filename: string): Promise<void> {
  const { useAuth } = await import('@/lib/auth/store');
  const auth = useAuth.getState();
  const res = await fetch(`${API_URL}/api/v1/documents/${documentId}/download`, {
    headers: {
      Authorization: auth.token ? `Bearer ${auth.token}` : '',
      'X-Correlation-ID': crypto.randomUUID(),
      'X-Tenant-Id': auth.orgId || '',
    },
  });
  if (!res.ok) {
    throw new Error(`Download failed: ${res.status}`);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

// --- Analytics ---
export async function getAnalytics(): Promise<T.AnalyticsData> {
  if (USE_MOCKS) {
    const { MOCK_ANALYTICS } = await import('./mocks/analytics');
    return MOCK_ANALYTICS;
  }
  return apiFetch<T.AnalyticsData>('/api/v1/analytics/kpis');
}

// --- BI ---
export async function getBIReports(): Promise<T.BIReport[]> {
  if (USE_MOCKS) {
    const { MOCK_BI_REPORTS } = await import('./mocks/analytics');
    return MOCK_BI_REPORTS;
  }
  return apiFetch<T.BIReport[]>('/api/v1/bi/reports');
}

// --- Forecasts ---
export async function getForecast(horizon: '7d' | '30d' | '90d'): Promise<T.ForecastData> {
  if (USE_MOCKS) {
    const mocks = await import('./mocks/analytics');
    if (horizon === '7d') return mocks.MOCK_FORECAST_7D;
    if (horizon === '30d') return mocks.MOCK_FORECAST_30D;
    return mocks.MOCK_FORECAST_90D;
  }
  return apiFetch<T.ForecastData>(`/api/v1/ml/forecast?horizon=${horizon}`);
}

// --- Transactions / Accounting Ledger ---
export async function getTransactions(): Promise<T.Transaction[]> {
  if (USE_MOCKS) {
    const { MOCK_TRANSACTIONS } = await import('./mocks/finance');
    return MOCK_TRANSACTIONS;
  }
  return apiFetch<T.Transaction[]>('/api/v1/finance/transactions');
}

// --- Procurement ---
export async function getSuppliers(): Promise<T.Supplier[]> {
  if (USE_MOCKS) {
    const { MOCK_SUPPLIERS } = await import('./mocks/procurement');
    return MOCK_SUPPLIERS;
  }
  return apiFetch<T.Supplier[]>('/api/v1/procurement/suppliers');
}

export async function getPurchaseOrders(): Promise<T.PurchaseOrder[]> {
  if (USE_MOCKS) {
    const { MOCK_PURCHASE_ORDERS } = await import('./mocks/procurement');
    return MOCK_PURCHASE_ORDERS;
  }
  return apiFetch<T.PurchaseOrder[]>('/api/v1/procurement/purchase-orders');
}

// --- Audit Logs ---
export async function getAuditLogs(): Promise<T.AuditLog[]> {
  if (USE_MOCKS) {
    const { MOCK_AUDIT_LOGS } = await import('./mocks/analytics');
    return MOCK_AUDIT_LOGS;
  }
  return apiFetch<T.AuditLog[]>('/api/v1/platform/audit-logs');
}

// --- Billing ---
export async function getBillingOverview(): Promise<T.BillingOverview> {
  return apiFetch<T.BillingOverview>('/api/v1/billing/overview');
}

export async function getBillingPlans(): Promise<T.BillingPlan[]> {
  return apiFetch<T.BillingPlan[]>('/api/v1/billing/plans');
}

export async function createBillingCheckout(planCode: string): Promise<T.CheckoutSession> {
  return apiFetch<T.CheckoutSession>('/api/v1/billing/checkout', {
    method: 'POST',
    body: JSON.stringify({ planCode }),
  });
}

// --- CRM Contacts mutations ---
export async function createContact(payload: {
  firstName: string
  lastName: string
  email: string
  company: string
  phone?: string
  position?: string
  tags?: string[]
  status?: string
}): Promise<T.Contact> {
  return apiFetch<T.Contact>('/api/v1/crm/contacts', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateContact(
  contactId: string,
  payload: Partial<{
    firstName: string
    lastName: string
    email: string
    company: string
    phone: string
    position: string
    status: string
    tags: string[]
  }>,
): Promise<T.Contact> {
  return apiFetch<T.Contact>(`/api/v1/crm/contacts/${encodeURIComponent(contactId)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteContact(contactId: string): Promise<void> {
  await apiFetch<void>(`/api/v1/crm/contacts/${encodeURIComponent(contactId)}`, {
    method: 'DELETE',
  });
}

export async function createLead(payload: {
  title: string
  company: string
  contactName: string
  value: number
  currency?: string
  stage?: string
  expectedCloseDate: string
}): Promise<T.Lead> {
  return apiFetch<T.Lead>('/api/v1/crm/leads', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateLeadStage(leadId: string, stage: string): Promise<T.Lead> {
  return apiFetch<T.Lead>(`/api/v1/crm/leads/${encodeURIComponent(leadId)}/stage`, {
    method: 'PATCH',
    body: JSON.stringify({ stage }),
  });
}

export async function createInvoice(payload: {
  clientId: string
  clientName: string
  currency?: string
  issueDate?: string
  dueDate?: string
  lineItems: Array<{
    description: string
    quantity: number
    unitPrice: number
    taxRate?: number
  }>
}): Promise<T.Invoice> {
  return apiFetch<T.Invoice>('/api/v1/finance/invoices', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function sendInvoice(invoiceId: string): Promise<T.Invoice> {
  return apiFetch<T.Invoice>(`/api/v1/finance/invoices/${encodeURIComponent(invoiceId)}/send`, {
    method: 'POST',
  });
}

// --- Copilot (SSE backend) ---
export type CopilotSource = {
  documentId: string
  documentTitle: string
  chunkId?: string
  relevanceScore: number
  excerpt: string
  sourceUri?: string
}

export type CopilotStreamEvent =
  | { type: 'chunk'; content: string }
  | { type: 'done'; sources: CopilotSource[]; provider?: string }

export async function* streamCopilotResponse(
  prompt: string,
  agentId?: string,
  context?: string,
): AsyncGenerator<CopilotStreamEvent> {
  if (USE_MOCKS) {
    const responses = [
      `Basé sur l'analyse de vos données, voici ce que j'ai trouvé concernant "${prompt}":\n\n` +
      `• Le revenu mensuel est en hausse de 12.5% par rapport au mois dernier\n` +
      `• 3 factures sont en retard de paiement, totalisant 45 200 €\n` +
      `• Le pipeline commercial contient 12 deals actifs pour une valeur de 340 000 €\n\n` +
      `Je recommande de prioriser le suivi des factures impayées et de contacter les clients concernés.`,
      `Voici un résumé de la situation:\n\n` +
      `**Performance globale:** Excellente. Tous les indicateurs clés sont au vert.\n\n` +
      `**Points d'attention:**\n` +
      `- 2 contrats arrivent à échéance dans les 30 prochains jours\n` +
      `- Le stock de 3 articles est critique\n\n` +
      `Souhaitez-vous que je prépare un plan d'action détaillé ?`,
    ];
    const response = responses[Math.floor(Math.random() * responses.length)];
    const words = response.split(' ');
    for (let i = 0; i < words.length; i++) {
      yield { type: 'chunk', content: words[i] + (i < words.length - 1 ? ' ' : '') };
      await new Promise((r) => setTimeout(r, 30 + Math.random() * 40));
    }
    yield {
      type: 'done',
      provider: 'mock',
      sources: [
        {
          documentId: 'doc-mock-1',
          documentTitle: 'README_00_Vision.md',
          relevanceScore: 0.92,
          excerpt: 'AI BOS — vision produit et positionnement SaaS B2B.',
          sourceUri: 'Document/README_00_Vision.md',
        },
      ],
    };
    return;
  }

  const { useAuth } = await import('@/lib/auth/store');
  const auth = useAuth.getState();
  const chatbotToken = import.meta.env.VITE_CHATBOT_API_TOKEN?.trim();
  const res = await fetch(`${API_URL}/api/v1/ai/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: auth.token ? `Bearer ${auth.token}` : '',
      'X-Correlation-ID': crypto.randomUUID(),
      'X-Tenant-Id': auth.orgId || '',
      ...(chatbotToken ? { 'X-Chatbot-Token': chatbotToken } : {}),
    },
    body: JSON.stringify({ message: prompt, agentId, context }),
  });

  if (!res.ok) {
    throw new Error(`Copilot API error: ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      try {
        const payload = JSON.parse(line.slice(6)) as {
          type?: string
          content?: string
          message?: string
          sources?: CopilotSource[]
          provider?: string
        };
        if (payload.type === 'chunk' && payload.content) {
          yield { type: 'chunk', content: payload.content };
        }
        if (payload.type === 'done') {
          yield { type: 'done', sources: payload.sources || [], provider: payload.provider };
        }
        if (payload.type === 'error') {
          throw new Error(payload.message || 'Copilot stream error');
        }
      } catch (error) {
        if (error instanceof SyntaxError) continue;
        throw error;
      }
    }
  }
}
