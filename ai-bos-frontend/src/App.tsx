import { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageLoader } from '@/components/shared/PageLoader';
import { ProtectedRoute } from '@/lib/auth/guards';
import { LoginPage } from '@/pages/LoginPage';
import { ForbiddenPage } from '@/pages/ForbiddenPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { OnboardingPage } from '@/pages/OnboardingPage';
import * as Pages from '@/routes/lazy-pages';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30000, retry: 1 } },
});

function Lazy({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/403" element={<ForbiddenPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/app" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/app/dashboard" replace />} />
            <Route path="dashboard" element={<Lazy><Pages.DashboardPage /></Lazy>} />
            <Route path="copilot" element={<Lazy><Pages.CopilotPage /></Lazy>} />
            <Route path="inbox" element={<Lazy><Pages.InboxPage /></Lazy>} />
            <Route path="crm/contacts" element={<Lazy><Pages.CRMContactsPage /></Lazy>} />
            <Route path="crm/pipeline" element={<Lazy><Pages.CRMPipelinePage /></Lazy>} />
            <Route path="sales/orders" element={<Lazy><Pages.SalesOrdersPage /></Lazy>} />
            <Route path="marketing/campaigns" element={<Lazy><Pages.MarketingCampaignsPage /></Lazy>} />
            <Route path="finance" element={<Lazy><Pages.FinancePage /></Lazy>} />
            <Route path="finance/invoices" element={<Lazy><Pages.InvoicesPage /></Lazy>} />
            <Route path="finance/payments" element={<Lazy><Pages.FinancePaymentsPage /></Lazy>} />
            <Route path="finance/accounting" element={<Lazy><Pages.FinanceAccountingPage /></Lazy>} />
            <Route path="finance/reports" element={<Lazy><Pages.FinanceReportsPage /></Lazy>} />
            <Route path="projects" element={<Lazy><Pages.ProjectsPage /></Lazy>} />
            <Route path="tasks" element={<Lazy><Pages.TasksPage /></Lazy>} />
            <Route path="calendar" element={<Lazy><Pages.CalendarPage /></Lazy>} />
            <Route path="meetings" element={<Lazy><Pages.MeetingsPage /></Lazy>} />
            <Route path="documents" element={<Lazy><Pages.DocumentsPage /></Lazy>} />
            <Route path="inventory" element={<Lazy><Pages.InventoryPage /></Lazy>} />
            <Route path="procurement" element={<Lazy><Pages.ProcurementPage /></Lazy>} />
            <Route path="hr/employees" element={<Lazy><Pages.HREmployeesPage /></Lazy>} />
            <Route path="hr/org-chart" element={<Lazy><Pages.HROrgChartPage /></Lazy>} />
            <Route path="hr/recruitment" element={<Lazy><Pages.RecruitmentPage /></Lazy>} />
            <Route path="hr/payroll" element={<Lazy><Pages.HRPayrollPage /></Lazy>} />
            <Route path="support/tickets" element={<Lazy><Pages.SupportTicketsPage /></Lazy>} />
            <Route path="contracts" element={<Lazy><Pages.ContractsPage /></Lazy>} />
            <Route path="knowledge" element={<Lazy><Pages.KnowledgePage /></Lazy>} />
            <Route path="analytics" element={<Lazy><Pages.AnalyticsPage /></Lazy>} />
            <Route path="bi" element={<Lazy><Pages.BIPage /></Lazy>} />
            <Route path="forecasts" element={<Lazy><Pages.ForecastsPage /></Lazy>} />
            <Route path="workflows" element={<Lazy><Pages.WorkflowsPage /></Lazy>} />
            <Route path="agents" element={<Lazy><Pages.AgentsPage /></Lazy>} />
            <Route path="settings/profile" element={<Lazy><Pages.SettingsProfilePage /></Lazy>} />
            <Route path="settings/organization" element={<Lazy><Pages.SettingsOrgPage /></Lazy>} />
            <Route path="settings/team" element={<Lazy><Pages.SettingsTeamPage /></Lazy>} />
            <Route path="settings/billing" element={<Lazy><Pages.SettingsBillingPage /></Lazy>} />
            <Route path="settings/integrations" element={<Lazy><Pages.SettingsIntegrationsPage /></Lazy>} />
            <Route path="settings/notifications" element={<Lazy><Pages.SettingsNotificationsPage /></Lazy>} />
            <Route path="settings/api-keys" element={<Lazy><Pages.SettingsApiKeysPage /></Lazy>} />
            <Route path="admin/audit" element={<Lazy><Pages.AdminAuditPage /></Lazy>} />
            <Route path="admin/flags" element={<Lazy><Pages.AdminFlagsPage /></Lazy>} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  );
}
