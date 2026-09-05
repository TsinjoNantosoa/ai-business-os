import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeState {
  mode: ThemeMode;
  resolved: 'light' | 'dark';
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
}

function systemPrefersDark(): boolean {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export function resolveTheme(mode: ThemeMode): 'light' | 'dark' {
  if (mode === 'system') return systemPrefersDark() ? 'dark' : 'light';
  return mode;
}

function paint(mode: ThemeMode): 'light' | 'dark' {
  const resolved = resolveTheme(mode);
  const root = document.documentElement;
  root.classList.toggle('dark', resolved === 'dark');
  root.dataset.theme = resolved;
  root.style.colorScheme = resolved;
  return resolved;
}

export const useTheme = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'dark',
      resolved: 'dark',
      setMode: (mode) => {
        set({ mode, resolved: paint(mode) });
      },
      toggle: () => {
        const next: ThemeMode = get().resolved === 'dark' ? 'light' : 'dark';
        set({ mode: next, resolved: paint(next) });
      },
    }),
    {
      name: 'aibos-theme',
      partialize: (state) => ({ mode: state.mode }),
      onRehydrateStorage: () => (state) => {
        if (!state) {
          paint('dark');
          return;
        }
        state.resolved = paint(state.mode);
      },
    },
  ),
);

/** Call once at app boot. */
export function initTheme(): void {
  try {
    const raw = localStorage.getItem('aibos-theme');
    const parsed = raw ? (JSON.parse(raw) as { state?: { mode?: ThemeMode } }) : null;
    const mode = parsed?.state?.mode ?? 'dark';
    useTheme.setState({ mode, resolved: paint(mode) });
  } catch {
    useTheme.setState({ mode: 'dark', resolved: paint('dark') });
  }

  if (typeof window === 'undefined') return;
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  const onChange = () => {
    const { mode } = useTheme.getState();
    if (mode === 'system') {
      useTheme.setState({ resolved: paint('system') });
    }
  };
  mq.addEventListener('change', onChange);
}
