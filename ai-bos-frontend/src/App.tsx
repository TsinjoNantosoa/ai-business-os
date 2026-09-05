import { Suspense, lazy, type ReactNode, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { PageLoader } from '@/components/shared/PageLoader';
import { LandingPage } from '@/pages/LandingPage';

const AppShell = lazy(() => import('@/routes/AppShell'));
const LoginPage = lazy(() =>
  import('@/pages/LoginPage').then((m) => ({ default: m.LoginPage })),
);
const RegisterPage = lazy(() =>
  import('@/pages/RegisterPage').then((m) => ({ default: m.RegisterPage })),
);
const ForgotPasswordPage = lazy(() =>
  import('@/pages/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage })),
);
const ResetPasswordPage = lazy(() =>
  import('@/pages/ResetPasswordPage').then((m) => ({ default: m.ResetPasswordPage })),
);
const ForbiddenPage = lazy(() =>
  import('@/pages/ForbiddenPage').then((m) => ({ default: m.ForbiddenPage })),
);
const NotFoundPage = lazy(() =>
  import('@/pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage })),
);

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30000, retry: 1 } },
});

const ROUTE_TITLES: Record<string, string> = {
  dashboard: 'Dashboard',
  copilot: 'Copilote IA',
  inbox: 'Boîte de réception',
  crm: 'CRM',
  sales: 'Ventes',
  marketing: 'Marketing',
  finance: 'Finance',
  projects: 'Projets',
  tasks: 'Tâches',
  calendar: 'Calendrier',
  meetings: 'Réunions',
  documents: 'Documents',
  inventory: 'Inventaire',
  procurement: 'Achats',
  hr: 'Ressources humaines',
  support: 'Support',
  contracts: 'Contrats',
  knowledge: 'Connaissances',
  analytics: 'Analytics',
  bi: 'Business Intelligence',
  forecasts: 'Prévisions',
  workflows: 'Workflows',
  agents: 'Agents IA',
  settings: 'Paramètres',
  admin: 'Administration',
};

function DocumentTitle() {
  const { pathname } = useLocation();
  useEffect(() => {
    if (pathname === '/') document.title = 'AI BOS — Business Operating System';
    else if (pathname === '/login') document.title = 'Connexion | AI BOS';
    else if (pathname === '/register') document.title = 'Créer un compte | AI BOS';
    else if (pathname === '/forgot-password') document.title = 'Mot de passe oublié | AI BOS';
    else if (pathname === '/reset-password') document.title = 'Réinitialiser le mot de passe | AI BOS';
    else if (pathname === '/onboarding') document.title = 'Configuration | AI BOS';
    else {
      const section = pathname.split('/').filter(Boolean)[1];
      document.title = `${ROUTE_TITLES[section] || 'AI BOS'} | AI BOS`;
    }
  }, [pathname]);
  return null;
}

function Lazy({ children }: { children: ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <DocumentTitle />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Lazy><LoginPage /></Lazy>} />
          <Route path="/register" element={<Lazy><RegisterPage /></Lazy>} />
          <Route path="/forgot-password" element={<Lazy><ForgotPasswordPage /></Lazy>} />
          <Route path="/reset-password" element={<Lazy><ResetPasswordPage /></Lazy>} />
          <Route path="/403" element={<Lazy><ForbiddenPage /></Lazy>} />
          {/* Authenticated area (auth store + shell loaded only here) */}
          <Route path="/onboarding" element={<Lazy><AppShell /></Lazy>} />
          <Route path="/app/*" element={<Lazy><AppShell /></Lazy>} />
          <Route path="*" element={<Lazy><NotFoundPage /></Lazy>} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors theme="system" />
    </QueryClientProvider>
  );
}
