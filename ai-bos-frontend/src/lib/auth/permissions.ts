/**
 * Canonical permission catalog for AI BOS frontend.
 * Must stay aligned with navigation.ts and backend ROLE_PERMISSIONS.
 */
export const APP_PERMISSIONS = [
  'dashboard.read',
  'ai.copilot.use',
  'ai.agent.use',
  'crm.contact.read',
  'crm.contact.write',
  'crm.lead.read',
  'crm.lead.write',
  'sales.order.read',
  'sales.order.write',
  'marketing.campaign.read',
  'marketing.campaign.write',
  'finance.invoice.read',
  'finance.invoice.write',
  'finance.payment.read',
  'finance.payment.write',
  'project.read',
  'project.write',
  'task.read',
  'task.write',
  'calendar.read',
  'calendar.write',
  'meeting.read',
  'meeting.write',
  'document.read',
  'document.write',
  'inventory.read',
  'inventory.write',
  'hr.employee.read',
  'hr.employee.write',
  'hr.recruitment.read',
  'hr.recruitment.write',
  'hr.leave.read',
  'hr.leave.write',
  'support.ticket.read',
  'support.ticket.write',
  'contract.read',
  'contract.write',
  'knowledge.read',
  'knowledge.write',
  'analytics.read',
  'bi.read',
  'ml.forecast.read',
  'workflow.read',
  'workflow.write',
  'settings.profile',
  'settings.org',
  'settings.team',
  'settings.billing',
  'admin.audit',
  'admin.flags',
] as const;

export type AppPermission = (typeof APP_PERMISSIONS)[number];

/** Roles that receive full application access (SaaS org owners / admins). */
export const FULL_ACCESS_ROLES = new Set(['owner', 'admin']);

export function normalizeRole(role: string | null | undefined): string {
  return (role || '').trim().toLowerCase();
}

export function hasFullAccess(role: string | null | undefined, permissions: string[] | null | undefined): boolean {
  if (FULL_ACCESS_ROLES.has(normalizeRole(role))) return true;
  const perms = permissions || [];
  return perms.includes('*') || perms.includes('*.*');
}

export function checkPermission(
  role: string | null | undefined,
  permissions: string[] | null | undefined,
  permission: string,
): boolean {
  if (!permission) return true;
  if (hasFullAccess(role, permissions)) return true;
  return (permissions || []).includes(permission);
}

export function checkAnyPermission(
  role: string | null | undefined,
  permissions: string[] | null | undefined,
  required: string[],
): boolean {
  if (!required.length) return true;
  if (hasFullAccess(role, permissions)) return true;
  const perms = permissions || [];
  return required.some((p) => perms.includes(p));
}
