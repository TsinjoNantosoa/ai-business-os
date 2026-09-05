import { Navigate, useLocation } from 'react-router-dom';
import { useEffect, useState, type ReactNode } from 'react';
import { useAuth } from './store';
import { ensureFreshAccessToken } from '@/lib/api/client';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, token } = useAuth();
  const location = useLocation();
  const [checkingSession, setCheckingSession] = useState(Boolean(user && !token));

  useEffect(() => {
    if (!user || token) {
      setCheckingSession(false);
      return;
    }
    let active = true;
    setCheckingSession(true);
    void ensureFreshAccessToken().finally(() => {
      if (active) setCheckingSession(false);
    });
    return () => {
      active = false;
    };
  }, [user, token]);

  if (checkingSession) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Restauration de la session…</div>;
  }

  if (!user || !token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

/**
 * Route-level RBAC. Owner/admin always pass (see permissions.ts).
 * Staff/viewer only see routes matching their permission grants.
 */
export function RequirePermission({
  permission,
  permissions,
  fallback = <Navigate to="/403" replace />,
  children,
}: {
  permission?: string;
  permissions?: string[];
  fallback?: ReactNode;
  children: ReactNode;
}) {
  const { user, hasPermission, hasAnyPermission } = useAuth();

  if (!user) {
    return <>{fallback}</>;
  }

  const allowed = permission
    ? hasPermission(permission)
    : permissions
      ? hasAnyPermission(permissions)
      : true;

  if (!allowed) return <>{fallback}</>;
  return <>{children}</>;
}
