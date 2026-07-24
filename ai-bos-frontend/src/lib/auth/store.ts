import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Organization, AuthResponse } from '@/lib/api/types';
import { login as apiLogin, register as apiRegister, getOrganizations } from '@/lib/api/services';
import { checkAnyPermission, checkPermission } from '@/lib/auth/permissions';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  orgId: string | null;
  organizations: Organization[];
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (input: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    organizationName: string;
  }) => Promise<void>;
  applyAuthResponse: (res: AuthResponse) => Promise<void>;
  logout: () => void;
  logoutAll: () => void;
  setTokens: (token: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  setOrg: (orgId: string) => void;
  loadOrganizations: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      orgId: null,
      organizations: [],
      isLoading: false,
      error: null,

      applyAuthResponse: async (res: AuthResponse) => {
        set({
          user: res.user,
          token: res.token,
          refreshToken: res.refreshToken,
          orgId: res.user.orgId,
          isLoading: false,
          error: null,
        });
        await get().loadOrganizations();
      },

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const res = await apiLogin(email, password);
          await get().applyAuthResponse(res);
        } catch (err) {
          set({ isLoading: false, error: (err as Error).message });
          throw err;
        }
      },

      register: async (input) => {
        set({ isLoading: true, error: null });
        try {
          const res = await apiRegister(input);
          await get().applyAuthResponse(res);
        } catch (err) {
          set({ isLoading: false, error: (err as Error).message });
          throw err;
        }
      },

      logout: () => {
        set({ user: null, token: null, refreshToken: null, orgId: null, organizations: [] });
      },

      logoutAll: () => {
        set({ user: null, token: null, refreshToken: null, orgId: null, organizations: [] });
      },

      setTokens: (token, refreshToken) => set({ token, refreshToken }),

      setUser: (user) => set({ user }),

      setOrg: (orgId) => set({ orgId }),

      loadOrganizations: async () => {
        try {
          const orgs = await getOrganizations();
          set({ organizations: orgs });
        } catch {
          // silent fail in mock mode
        }
      },

      hasPermission: (permission: string) => {
        const { user } = get();
        if (!user) return false;
        return checkPermission(user.role, user.permissions, permission);
      },

      hasAnyPermission: (permissions: string[]) => {
        const { user } = get();
        if (!user) return false;
        return checkAnyPermission(user.role, user.permissions, permissions);
      },
    }),
    {
      name: 'aibos-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        orgId: state.orgId,
        organizations: state.organizations,
      }),
    }
  )
);
