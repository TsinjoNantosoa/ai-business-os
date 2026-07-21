import { describe, expect, it } from 'vitest';
import { allNavItems } from '@/lib/navigation';
import { checkAnyPermission, checkPermission, hasFullAccess } from '@/lib/auth/permissions';

const ceo = { role: 'owner', permissions: ['dashboard.read'] as string[] };
const staff = {
  role: 'staff',
  permissions: ['dashboard.read', 'task.read', 'crm.contact.read'] as string[],
};

describe('Phase 1 — CEO permissions & navigation', () => {
  it('owner has full access regardless of sparse permission array', () => {
    expect(hasFullAccess(ceo.role, ceo.permissions)).toBe(true);
    expect(checkPermission(ceo.role, ceo.permissions, 'knowledge.read')).toBe(true);
    expect(checkPermission(ceo.role, ceo.permissions, 'finance.payment.read')).toBe(true);
    expect(checkPermission(ceo.role, ceo.permissions, 'hr.leave.read')).toBe(true);
    expect(checkPermission(ceo.role, ceo.permissions, 'settings.profile')).toBe(true);
  });

  it('staff is limited to granted permissions', () => {
    expect(hasFullAccess(staff.role, staff.permissions)).toBe(false);
    expect(checkPermission(staff.role, staff.permissions, 'task.read')).toBe(true);
    expect(checkPermission(staff.role, staff.permissions, 'knowledge.read')).toBe(false);
    expect(checkAnyPermission(staff.role, staff.permissions, ['crm.contact.read', 'sales.order.read'])).toBe(true);
  });

  it('wildcard permission grants full access', () => {
    expect(checkPermission('viewer', ['*'], 'admin.audit')).toBe(true);
  });

  it('every nav item is visible for CEO/owner', () => {
    const hidden = allNavItems().filter((item) => {
      if (item.permission) return !checkPermission(ceo.role, ceo.permissions, item.permission);
      if (item.permissions) return !checkAnyPermission(ceo.role, ceo.permissions, item.permissions);
      return false;
    });
    expect(hidden.map((i) => i.path)).toEqual([]);
  });

  it('includes leaves route in navigation', () => {
    expect(allNavItems().some((i) => i.path === '/app/hr/leaves')).toBe(true);
  });
});
