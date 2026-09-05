import { Suspense, lazy, type ReactNode } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
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

function Lazy({ children }: { children: ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
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
