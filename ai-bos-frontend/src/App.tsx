import { Suspense, type ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageLoader } from '@/components/shared/PageLoader';
import { ProtectedRoute, RequirePermission } from '@/lib/auth/guards';
import { LandingPage } from '@/pages/LandingPage';
import { LoginPage } from '@/pages/LoginPage';
import { ForgotPasswordPage } from '@/pages/ForgotPasswordPage';
import { ResetPasswordPage } from '@/pages/ResetPasswordPage';
import { ForbiddenPage } from '@/pages/ForbiddenPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { OnboardingPage } from '@/pages/OnboardingPage';
import * as Pages from '@/routes/lazy-pages';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30000, retry: 1 } },
});

function Lazy({ children }: { children: ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

/** Authenticated + permission-gated route shell (owner/admin always allowed). */
function Gate({
  permission,
  permissions,
  children,
}: {
  permission?: string;
  permissions?: string[];
  children: ReactNode;
}) {
  return (
    <RequirePermission permission={permission} permissions={permissions}>
      <Lazy>{children}</Lazy>
    </RequirePermission>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/403" element={<ForbiddenPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/app" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/app/dashboard" replace />} />
            <Route path="dashboard" element={<Lazy><Pages.DashboardPage /></Lazy>} />
            <Route path="copilot" element={<Gate permission="ai.copilot.use"><Pages.CopilotPage /></Gate>} />
            <Route path="inbox" element={<Lazy><Pages.InboxPage /></Lazy>} />
            <Route path="crm/contacts" element={<Gate permission="crm.contact.read"><Pages.CRMContactsPage /></Gate>} />
            <Route path="crm/pipeline" element={<Gate permission="crm.lead.read"><Pages.CRMPipelinePage /></Gate>} />
            <Route path="sales/orders" element={<Gate permissions={['crm.contact.read', 'sales.order.read']}><Pages.SalesOrdersPage /></Gate>} />
            <Route path="marketing/campaigns" element={<Gate permission="marketing.campaign.read"><Pages.MarketingCampaignsPage /></Gate>} />
            <Route path="finance" element={<Gate permission="finance.invoice.read"><Pages.FinancePage /></Gate>} />
            <Route path="finance/invoices" element={<Gate permission="finance.invoice.read"><Pages.InvoicesPage /></Gate>} />
            <Route path="finance/payments" element={<Gate permission="finance.payment.read"><Pages.FinancePaymentsPage /></Gate>} />
            <Route path="finance/accounting" element={<Gate permission="finance.invoice.read"><Pages.FinanceAccountingPage /></Gate>} />
            <Route path="finance/reports" element={<Gate permission="finance.invoice.read"><Pages.FinanceReportsPage /></Gate>} />
            <Route path="projects" element={<Gate permission="project.read"><Pages.ProjectsPage /></Gate>} />
            <Route path="projects/:projectId" element={<Gate permission="project.read"><Pages.ProjectDetailPage /></Gate>} />
            <Route path="tasks" element={<Gate permission="task.read"><Pages.TasksPage /></Gate>} />
            <Route path="calendar" element={<Gate permission="calendar.read"><Pages.CalendarPage /></Gate>} />
            <Route path="meetings" element={<Gate permission="meeting.read"><Pages.MeetingsPage /></Gate>} />
            <Route path="documents" element={<Gate permission="document.read"><Pages.DocumentsPage /></Gate>} />
            <Route path="inventory" element={<Gate permission="inventory.read"><Pages.InventoryPage /></Gate>} />
            <Route path="procurement" element={<Gate permission="inventory.read"><Pages.ProcurementPage /></Gate>} />
            <Route path="hr/employees" element={<Gate permission="hr.employee.read"><Pages.HREmployeesPage /></Gate>} />
            <Route path="hr/org-chart" element={<Gate permission="hr.employee.read"><Pages.HROrgChartPage /></Gate>} />
            <Route path="hr/recruitment" element={<Gate permission="hr.recruitment.read"><Pages.RecruitmentPage /></Gate>} />
            <Route path="hr/payroll" element={<Gate permission="hr.employee.read"><Pages.HRPayrollPage /></Gate>} />
            <Route path="hr/leaves" element={<Gate permissions={['hr.leave.read', 'hr.employee.read']}><Pages.HRLeavesPage /></Gate>} />
            <Route path="support/tickets" element={<Gate permission="support.ticket.read"><Pages.SupportTicketsPage /></Gate>} />
            <Route path="contracts" element={<Gate permission="contract.read"><Pages.ContractsPage /></Gate>} />
            <Route path="knowledge" element={<Gate permission="knowledge.read"><Pages.KnowledgePage /></Gate>} />
            <Route path="analytics" element={<Gate permission="analytics.read"><Pages.AnalyticsPage /></Gate>} />
            <Route path="bi" element={<Gate permission="bi.read"><Pages.BIPage /></Gate>} />
            <Route path="forecasts" element={<Gate permission="ml.forecast.read"><Pages.ForecastsPage /></Gate>} />
            <Route path="workflows" element={<Gate permission="workflow.read"><Pages.WorkflowsPage /></Gate>} />
            <Route path="agents" element={<Gate permission="ai.agent.use"><Pages.AgentsPage /></Gate>} />
            <Route path="settings/profile" element={<Gate permission="settings.profile"><Pages.SettingsProfilePage /></Gate>} />
            <Route path="settings/organization" element={<Gate permission="settings.org"><Pages.SettingsOrgPage /></Gate>} />
            <Route path="settings/team" element={<Gate permission="settings.team"><Pages.SettingsTeamPage /></Gate>} />
            <Route path="settings/billing" element={<Gate permission="settings.billing"><Pages.SettingsBillingPage /></Gate>} />
            <Route path="settings/integrations" element={<Gate permission="settings.org"><Pages.SettingsIntegrationsPage /></Gate>} />
            <Route path="settings/notifications" element={<Gate permission="settings.profile"><Pages.SettingsNotificationsPage /></Gate>} />
            <Route path="settings/api-keys" element={<Gate permission="settings.org"><Pages.SettingsApiKeysPage /></Gate>} />
            <Route path="admin/audit" element={<Gate permission="admin.audit"><Pages.AdminAuditPage /></Gate>} />
            <Route path="admin/flags" element={<Gate permission="admin.flags"><Pages.AdminFlagsPage /></Gate>} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  );
}
