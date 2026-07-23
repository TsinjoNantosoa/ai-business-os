import { useAuth } from './store';
import { APP_PERMISSIONS, checkAnyPermission, checkPermission, hasFullAccess } from './permissions';

export function hasPermission(permission: string): boolean {
  return useAuth.getState().hasPermission(permission);
}

export function hasAnyPermission(permissions: string[]): boolean {
  return useAuth.getState().hasAnyPermission(permissions);
}

export function hasRole(role: string | string[]): boolean {
  const user = useAuth.getState().user;
  if (!user) return false;
  const current = (user.role || '').toLowerCase();
  return Array.isArray(role) ? role.map((r) => r.toLowerCase()).includes(current) : current === role.toLowerCase();
}

export function isOwnerOrAdmin(): boolean {
  const user = useAuth.getState().user;
  if (!user) return false;
  return hasFullAccess(user.role, user.permissions);
}

/** Evaluate permission against a plain user-like object (tests / SSE / non-React). */
export function evaluatePermission(
  user: { role?: string; permissions?: string[] } | null | undefined,
  permission: string,
): boolean {
  if (!user) return false;
  return checkPermission(user.role, user.permissions, permission);
}

export function evaluateAnyPermission(
  user: { role?: string; permissions?: string[] } | null | undefined,
  permissions: string[],
): boolean {
  if (!user) return false;
  return checkAnyPermission(user.role, user.permissions, permissions);
}

// Permission constants for easy reference (aligned with APP_PERMISSIONS)
export const PERMS = {
  CRM_READ: 'crm.contact.read',
  CRM_WRITE: 'crm.contact.write',
  LEAD_READ: 'crm.lead.read',
  LEAD_WRITE: 'crm.lead.write',
  SALES_READ: 'sales.order.read',
  MARKETING_READ: 'marketing.campaign.read',
  FINANCE_READ: 'finance.invoice.read',
  FINANCE_WRITE: 'finance.invoice.write',
  PAYMENT_READ: 'finance.payment.read',
  HR_READ: 'hr.employee.read',
  HR_WRITE: 'hr.employee.write',
  HR_RECRUITMENT: 'hr.recruitment.read',
  HR_LEAVE: 'hr.leave.read',
  PROJECT_READ: 'project.read',
  PROJECT_WRITE: 'project.write',
  TASK_READ: 'task.read',
  CALENDAR_READ: 'calendar.read',
  MEETING_READ: 'meeting.read',
  INVENTORY_READ: 'inventory.read',
  CONTRACT_READ: 'contract.read',
  KNOWLEDGE_READ: 'knowledge.read',
  AI_USE: 'ai.agent.use',
  COPILOT_USE: 'ai.copilot.use',
  AI_APPROVAL_DECIDE: 'ai.approval.decide',
  ANALYTICS_READ: 'analytics.read',
  BI_READ: 'bi.read',
  FORECAST_READ: 'ml.forecast.read',
  WORKFLOW_READ: 'workflow.read',
  WORKFLOW_WRITE: 'workflow.write',
  SETTINGS_PROFILE: 'settings.profile',
  SETTINGS_ORG: 'settings.org',
  SETTINGS_TEAM: 'settings.team',
  SETTINGS_BILLING: 'settings.billing',
  ADMIN_AUDIT: 'admin.audit',
  ADMIN_FLAGS: 'admin.flags',
} as const;

export { APP_PERMISSIONS };
