// ============================================================
// AI BOS — API Services
// Every service: try apiFetch → catch → return mock data
// ============================================================

import { apiFetch, tryRefresh, ensureFreshAccessToken, USE_MOCKS, API_URL } from './client';
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

export async function createOrder(input: {
  customerName: string;
  customerId?: string;
  status?: string;
  currency?: string;
  date?: string;
  lineItems: { description: string; quantity: number; unitPrice: number }[];
}): Promise<T.Order> {
  return apiFetch<T.Order>('/api/v1/sales/orders', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateOrder(
  orderId: string,
  input: {
    customerName?: string;
    status?: string;
    lineItems?: { description: string; quantity: number; unitPrice: number }[];
  },
): Promise<T.Order> {
  return apiFetch<T.Order>(`/api/v1/sales/orders/${orderId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
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

export async function createProject(input: {
  name: string;
  description?: string;
  status?: string;
  startDate?: string;
  endDate?: string;
  budget?: number;
  color?: string;
}): Promise<T.Project> {
  return apiFetch<T.Project>('/api/v1/projects', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateProject(
  projectId: string,
  input: {
    name?: string;
    description?: string;
    status?: string;
    progress?: number;
    startDate?: string;
    endDate?: string;
    budget?: number;
    spent?: number;
    color?: string;
  },
): Promise<T.Project> {
  return apiFetch<T.Project>(`/api/v1/projects/${projectId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
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

export async function createEmployee(input: {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  position: string;
  department: string;
  startDate?: string;
  status?: string;
  salary?: number;
  location?: string;
  managerId?: string;
}): Promise<T.Employee> {
  return apiFetch<T.Employee>('/api/v1/hr/employees', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateEmployee(
  employeeId: string,
  input: Partial<{
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    position: string;
    department: string;
    startDate: string;
    status: string;
    salary: number;
    location: string;
    managerId: string;
  }>,
): Promise<T.Employee> {
  return apiFetch<T.Employee>(`/api/v1/hr/employees/${employeeId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
}

export async function getJobOpenings(): Promise<T.JobOpening[]> {
  if (USE_MOCKS) {
    const { MOCK_JOB_OPENINGS } = await import('./mocks/projects');
    return MOCK_JOB_OPENINGS;
  }
  return apiFetch<T.JobOpening[]>('/api/v1/hr/jobs');
}

export async function createJobOpening(input: {
  title: string;
  department: string;
  status?: string;
  location: string;
  type?: string;
  postedDate?: string;
}): Promise<T.JobOpening> {
  return apiFetch<T.JobOpening>('/api/v1/hr/jobs', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateJobOpening(
  jobId: string,
  input: Partial<{
    title: string;
    department: string;
    status: string;
    location: string;
    type: string;
    applicants: number;
  }>,
): Promise<T.JobOpening> {
  return apiFetch<T.JobOpening>(`/api/v1/hr/jobs/${jobId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
}

export async function getCandidates(): Promise<T.Candidate[]> {
  if (USE_MOCKS) {
    const { MOCK_CANDIDATES } = await import('./mocks/projects');
    return MOCK_CANDIDATES;
  }
  return apiFetch<T.Candidate[]>('/api/v1/hr/candidates');
}

export async function createCandidate(input: {
  name: string;
  email: string;
  jobId?: string;
  jobTitle?: string;
  stage?: string;
  score?: number;
}): Promise<T.Candidate> {
  return apiFetch<T.Candidate>('/api/v1/hr/candidates', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateCandidate(
  candidateId: string,
  input: Partial<{
    name: string;
    email: string;
    jobId: string;
    jobTitle: string;
    stage: string;
    score: number;
  }>,
): Promise<T.Candidate> {
  return apiFetch<T.Candidate>(`/api/v1/hr/candidates/${candidateId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
}

// --- Marketing ---
export async function getCampaigns(): Promise<T.Campaign[]> {
  if (USE_MOCKS) {
    const { MOCK_CAMPAIGNS } = await import('./mocks/operations');
    return MOCK_CAMPAIGNS;
  }
  return apiFetch<T.Campaign[]>('/api/v1/marketing/campaigns');
}

export async function createCampaign(input: {
  name: string;
  type?: string;
  status?: string;
  budget?: number;
  startDate?: string;
  endDate?: string;
}): Promise<T.Campaign> {
  return apiFetch<T.Campaign>('/api/v1/marketing/campaigns', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateCampaign(
  campaignId: string,
  input: {
    name?: string;
    type?: string;
    status?: string;
    budget?: number;
    spent?: number;
    startDate?: string;
    endDate?: string;
  },
): Promise<T.Campaign> {
  return apiFetch<T.Campaign>(`/api/v1/marketing/campaigns/${campaignId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
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

export async function getWorkflow(workflowId: string): Promise<T.Workflow> {
  return apiFetch<T.Workflow>(`/api/v1/workflows/${workflowId}`);
}

export async function createWorkflow(payload: T.WorkflowUpsertPayload): Promise<T.Workflow> {
  return apiFetch<T.Workflow>('/api/v1/workflows', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateWorkflow(workflowId: string, payload: T.WorkflowUpsertPayload): Promise<T.Workflow> {
  return apiFetch<T.Workflow>(`/api/v1/workflows/${workflowId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function runWorkflow(workflowId: string): Promise<T.WorkflowRunResult> {
  return apiFetch<T.WorkflowRunResult>(`/api/v1/workflows/${workflowId}/run`, { method: 'POST' });
}

export async function getWorkflowExecutions(): Promise<T.WorkflowExecution[]> {
  return apiFetch<T.WorkflowExecution[]>('/api/v1/workflows/executions');
}

export async function getDomainEvents(): Promise<T.DomainEvent[]> {
  return apiFetch<T.DomainEvent[]>('/api/v1/events');
}

export async function getEventCatalog(): Promise<T.EventCatalogItem[]> {
  return apiFetch<T.EventCatalogItem[]>('/api/v1/events/catalog');
}

export async function getWebhookEndpoints(): Promise<T.WebhookEndpoint[]> {
  return apiFetch<T.WebhookEndpoint[]>('/api/v1/webhooks/endpoints');
}

export async function createWebhookEndpoint(payload: {
  name: string;
  description?: string;
  eventTypes?: string[];
}): Promise<T.WebhookEndpoint> {
  return apiFetch<T.WebhookEndpoint>('/api/v1/webhooks/endpoints', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function deleteWebhookEndpoint(endpointId: string): Promise<void> {
  await apiFetch(`/api/v1/webhooks/endpoints/${endpointId}`, { method: 'DELETE' });
}

// --- Agents ---
export async function getAgents(): Promise<T.Agent[]> {
  if (USE_MOCKS) {
    const { MOCK_AGENTS } = await import('./mocks/operations');
    return MOCK_AGENTS;
  }
  return apiFetch<T.Agent[]>('/api/v1/ai/agents');
}

export async function getAiUsageSummary(days = 30): Promise<T.AiUsageSummary> {
  return apiFetch<T.AiUsageSummary>(`/api/v1/ai/usage/summary?days=${days}`);
}

export async function getAiTraces(limit = 30): Promise<T.AiTrace[]> {
  return apiFetch<T.AiTrace[]>(`/api/v1/ai/traces?limit=${limit}`);
}

export async function getAgentDocs(): Promise<T.AgentDocs> {
  return apiFetch<T.AgentDocs>('/api/v1/ai/docs');
}

export async function getAgentDocsGuide(): Promise<T.AgentDocsGuide> {
  return apiFetch<T.AgentDocsGuide>('/api/v1/ai/docs/guide');
}

// --- Inventory ---
export async function getInventory(): Promise<T.InventoryItem[]> {
  if (USE_MOCKS) {
    const { MOCK_INVENTORY } = await import('./mocks/operations');
    return MOCK_INVENTORY;
  }
  return apiFetch<T.InventoryItem[]>('/api/v1/inventory/items');
}

export async function createInventoryItem(input: {
  sku: string;
  name: string;
  category: string;
  quantity?: number;
  reorderLevel?: number;
  warehouse: string;
  unitPrice?: number;
  status?: string;
}): Promise<T.InventoryItem> {
  return apiFetch<T.InventoryItem>('/api/v1/inventory/items', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateInventoryItem(
  itemId: string,
  input: Partial<{
    sku: string;
    name: string;
    category: string;
    quantity: number;
    reorderLevel: number;
    warehouse: string;
    unitPrice: number;
    status: string;
  }>,
): Promise<T.InventoryItem> {
  return apiFetch<T.InventoryItem>(`/api/v1/inventory/items/${itemId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
}

// --- Calendar ---
export async function getEvents(): Promise<T.CalendarEvent[]> {
  if (USE_MOCKS) {
    const { MOCK_EVENTS } = await import('./mocks/operations');
    return MOCK_EVENTS;
  }
  return apiFetch<T.CalendarEvent[]>('/api/v1/calendar/events');
}

export async function createEvent(input: {
  title: string;
  type?: string;
  startDate: string;
  endDate?: string;
  color?: string;
  location?: string;
  attendees?: string[];
  description?: string;
}): Promise<T.CalendarEvent> {
  return apiFetch<T.CalendarEvent>('/api/v1/calendar/events', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateEvent(
  eventId: string,
  input: {
    title?: string;
    type?: string;
    startDate?: string;
    endDate?: string;
    color?: string;
    location?: string;
    attendees?: string[];
    description?: string;
  },
): Promise<T.CalendarEvent> {
  return apiFetch<T.CalendarEvent>(`/api/v1/calendar/events/${eventId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
}

// --- Meetings ---
export async function getMeetings(): Promise<T.Meeting[]> {
  if (USE_MOCKS) {
    const { MOCK_MEETINGS } = await import('./mocks/operations');
    return MOCK_MEETINGS;
  }
  return apiFetch<T.Meeting[]>('/api/v1/meetings');
}

export async function createMeeting(input: {
  title: string;
  date: string;
  duration?: number;
  location?: string;
  agenda?: string[];
}): Promise<T.Meeting> {
  return apiFetch<T.Meeting>('/api/v1/meetings', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateMeeting(
  meetingId: string,
  input: {
    title?: string;
    date?: string;
    duration?: number;
    status?: string;
    location?: string;
    agenda?: string[];
    summary?: string;
  },
): Promise<T.Meeting> {
  return apiFetch<T.Meeting>(`/api/v1/meetings/${meetingId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
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

export async function createTransaction(input: {
  description: string;
  amount: number;
  type?: string;
  category: string;
  date?: string;
  account: string;
}): Promise<T.Transaction> {
  return apiFetch<T.Transaction>('/api/v1/finance/transactions', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateTransaction(
  txId: string,
  input: Partial<{
    description: string;
    amount: number;
    type: string;
    category: string;
    date: string;
    account: string;
  }>,
): Promise<T.Transaction> {
  return apiFetch<T.Transaction>(`/api/v1/finance/transactions/${txId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
}

// --- Procurement ---
export async function getSuppliers(): Promise<T.Supplier[]> {
  if (USE_MOCKS) {
    const { MOCK_SUPPLIERS } = await import('./mocks/procurement');
    return MOCK_SUPPLIERS;
  }
  return apiFetch<T.Supplier[]>('/api/v1/procurement/suppliers');
}

export async function createSupplier(input: {
  name: string;
  email: string;
  phone?: string;
  rating?: number;
  country?: string;
  status?: string;
}): Promise<T.Supplier> {
  return apiFetch<T.Supplier>('/api/v1/procurement/suppliers', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateSupplier(
  supplierId: string,
  input: Partial<{
    name: string;
    email: string;
    phone: string;
    rating: number;
    country: string;
    status: string;
  }>,
): Promise<T.Supplier> {
  return apiFetch<T.Supplier>(`/api/v1/procurement/suppliers/${supplierId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
}

export async function getPurchaseOrders(): Promise<T.PurchaseOrder[]> {
  if (USE_MOCKS) {
    const { MOCK_PURCHASE_ORDERS } = await import('./mocks/procurement');
    return MOCK_PURCHASE_ORDERS;
  }
  return apiFetch<T.PurchaseOrder[]>('/api/v1/procurement/purchase-orders');
}

export async function createPurchaseOrder(input: {
  supplierId?: string;
  supplierName: string;
  status?: string;
  totalAmount?: number;
  currency?: string;
  expectedAt?: string;
  itemCount?: number;
}): Promise<T.PurchaseOrder> {
  return apiFetch<T.PurchaseOrder>('/api/v1/procurement/purchase-orders', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updatePurchaseOrder(
  poId: string,
  input: Partial<{
    supplierId: string;
    supplierName: string;
    status: string;
    totalAmount: number;
    currency: string;
    expectedAt: string;
    itemCount: number;
  }>,
): Promise<T.PurchaseOrder> {
  return apiFetch<T.PurchaseOrder>(`/api/v1/procurement/purchase-orders/${poId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
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

export type CopilotToolEvent = {
  type: 'tool_call' | 'tool_result'
  name: string
  callId?: string
  arguments?: Record<string, unknown>
  ok?: boolean
  result?: unknown
  error?: string
  round?: number
}

export type CopilotApprovalEvent = {
  type: 'approval_required'
  approvalId: string
  name: string
  arguments?: Record<string, unknown>
  callId?: string
  message?: string
}

export type CopilotPendingAction = {
  id: string
  toolName: string
  arguments: Record<string, unknown>
  callId: string
  status: string
  conversationId?: string | null
  agentId?: string | null
  userMessage?: string
  result?: unknown
  error?: string | null
  createdAt?: string | null
  decidedAt?: string | null
  decidedBy?: string | null
}

export type CopilotStreamEvent =
  | { type: 'chunk'; content: string }
  | { type: 'step'; round: number; toolCount: number }
  | { type: 'tool_call'; name: string; arguments?: Record<string, unknown>; callId?: string; round?: number }
  | { type: 'tool_result'; name: string; callId?: string; ok: boolean; result?: unknown; error?: string; round?: number }
  | CopilotApprovalEvent
  | {
      type: 'done'
      sources: CopilotSource[]
      provider?: string
      toolsUsed?: string[]
      status?: string
      approvalId?: string
    }

export async function decideCopilotApproval(
  approvalId: string,
  decision: 'approve' | 'reject',
): Promise<CopilotPendingAction> {
  return apiFetch<CopilotPendingAction>(`/api/v1/ai/approvals/${approvalId}/decide`, {
    method: 'POST',
    body: JSON.stringify({ decision }),
  });
}

export async function listCopilotApprovals(status = 'pending'): Promise<{ items: CopilotPendingAction[] }> {
  return apiFetch<{ items: CopilotPendingAction[] }>(`/api/v1/ai/approvals?status=${encodeURIComponent(status)}`);
}

export async function* streamCopilotResponse(
  prompt: string,
  agentId?: string,
  context?: string,
  conversationId?: string,
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
  const chatbotToken = import.meta.env.VITE_CHATBOT_API_TOKEN?.trim();

  // Access JWT expires in ~60 min; also recovers after backend restart via refresh JWT.
  const ready = await ensureFreshAccessToken();
  if (!ready) {
    useAuth.getState().logout();
    throw new Error('Session expirée — reconnectez-vous, puis réessayez.');
  }

  async function postChat(): Promise<Response> {
    const auth = useAuth.getState();
    return fetch(`${API_URL}/api/v1/ai/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: auth.token ? `Bearer ${auth.token}` : '',
        'X-Correlation-ID': crypto.randomUUID(),
        'X-Tenant-Id': auth.orgId || '',
        ...(chatbotToken ? { 'X-Chatbot-Token': chatbotToken } : {}),
      },
      body: JSON.stringify({ message: prompt, agentId, context, conversationId }),
    });
  }

  let res = await postChat();
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) res = await postChat();
  }

  if (!res.ok) {
    if (res.status === 401) {
      useAuth.getState().logout();
      throw new Error('Session expirée — reconnectez-vous, puis réessayez.');
    }
    const detail = await res.text().catch(() => '');
    throw new Error(`Copilot API error: ${res.status}${detail ? ` — ${detail.slice(0, 180)}` : ''}`);
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
          toolsUsed?: string[]
          name?: string
          arguments?: Record<string, unknown>
          callId?: string
          ok?: boolean
          result?: unknown
          error?: string
          round?: number
          toolCount?: number
          approvalId?: string
          status?: string
        };
        if (payload.type === 'chunk' && payload.content) {
          yield { type: 'chunk', content: payload.content };
        }
        if (payload.type === 'step' && payload.round) {
          yield { type: 'step', round: payload.round, toolCount: payload.toolCount || 0 };
        }
        if (payload.type === 'tool_call' && payload.name) {
          yield {
            type: 'tool_call',
            name: payload.name,
            arguments: payload.arguments,
            callId: payload.callId,
            round: payload.round,
          };
        }
        if (payload.type === 'tool_result' && payload.name) {
          yield {
            type: 'tool_result',
            name: payload.name,
            callId: payload.callId,
            ok: Boolean(payload.ok),
            result: payload.result,
            error: payload.error,
            round: payload.round,
          };
        }
        if (payload.type === 'approval_required' && payload.approvalId && payload.name) {
          yield {
            type: 'approval_required',
            approvalId: payload.approvalId,
            name: payload.name,
            arguments: payload.arguments,
            callId: payload.callId,
            message: payload.message,
          };
        }
        if (payload.type === 'done') {
          yield {
            type: 'done',
            sources: payload.sources || [],
            provider: payload.provider,
            toolsUsed: payload.toolsUsed,
            status: payload.status,
            approvalId: payload.approvalId,
          };
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
