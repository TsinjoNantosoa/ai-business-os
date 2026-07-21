import { lazy, type ComponentType } from 'react';

function lazyNamed<T extends Record<string, ComponentType<unknown>>>(
  factory: () => Promise<T>,
  exportName: keyof T,
) {
  return lazy(() => factory().then((mod) => ({ default: mod[exportName] as ComponentType<unknown> })));
}

export const DashboardPage = lazyNamed(() => import('@/pages/DashboardPage'), 'DashboardPage');
export const CRMContactsPage = lazyNamed(() => import('@/pages/CRMContactsPage'), 'CRMContactsPage');
export const CRMPipelinePage = lazyNamed(() => import('@/pages/CRMPipelinePage'), 'CRMPipelinePage');
export const FinancePage = lazyNamed(() => import('@/pages/FinancePage'), 'FinancePage');
export const InvoicesPage = lazyNamed(() => import('@/pages/InvoicesPage'), 'InvoicesPage');
export const FinancePaymentsPage = lazyNamed(() => import('@/pages/FinancePaymentsPage'), 'FinancePaymentsPage');
export const FinanceAccountingPage = lazyNamed(() => import('@/pages/FinanceAccountingPage'), 'FinanceAccountingPage');
export const FinanceReportsPage = lazyNamed(() => import('@/pages/FinanceReportsPage'), 'FinanceReportsPage');
export const ProjectsPage = lazyNamed(() => import('@/pages/ProjectsPage'), 'ProjectsPage');
export const ProjectDetailPage = lazyNamed(() => import('@/pages/ProjectDetailPage'), 'ProjectDetailPage');
export const TasksPage = lazyNamed(() => import('@/pages/TasksPage'), 'TasksPage');
export const CalendarPage = lazyNamed(() => import('@/pages/CalendarPage'), 'CalendarPage');
export const MeetingsPage = lazyNamed(() => import('@/pages/MeetingsPage'), 'MeetingsPage');
export const DocumentsPage = lazyNamed(() => import('@/pages/DocumentsPage'), 'DocumentsPage');
export const HREmployeesPage = lazyNamed(() => import('@/pages/HREmployeesPage'), 'HREmployeesPage');
export const RecruitmentPage = lazyNamed(() => import('@/pages/RecruitmentPage'), 'RecruitmentPage');
export const HROrgChartPage = lazyNamed(() => import('@/pages/HROrgChartPage'), 'HROrgChartPage');
export const HRPayrollPage = lazyNamed(() => import('@/pages/HRPayrollPage'), 'HRPayrollPage');
export const HRLeavesPage = lazyNamed(() => import('@/pages/HRLeavesPage'), 'HRLeavesPage');
export const CopilotPage = lazyNamed(() => import('@/pages/CopilotPage'), 'CopilotPage');
export const AgentsPage = lazyNamed(() => import('@/pages/AgentsPage'), 'AgentsPage');
export const AnalyticsPage = lazyNamed(() => import('@/pages/AnalyticsPage'), 'AnalyticsPage');
export const BIPage = lazyNamed(() => import('@/pages/BIPage'), 'BIPage');
export const ForecastsPage = lazyNamed(() => import('@/pages/ForecastsPage'), 'ForecastsPage');
export const WorkflowsPage = lazyNamed(() => import('@/pages/WorkflowsPage'), 'WorkflowsPage');
export const SupportTicketsPage = lazyNamed(() => import('@/pages/SupportTicketsPage'), 'SupportTicketsPage');
export const MarketingCampaignsPage = lazyNamed(() => import('@/pages/MarketingCampaignsPage'), 'MarketingCampaignsPage');
export const InboxPage = lazyNamed(() => import('@/pages/InboxPage'), 'InboxPage');
export const SalesOrdersPage = lazyNamed(() => import('@/pages/SalesOrdersPage'), 'SalesOrdersPage');
export const InventoryPage = lazyNamed(() => import('@/pages/InventoryPage'), 'InventoryPage');
export const ProcurementPage = lazyNamed(() => import('@/pages/ProcurementPage'), 'ProcurementPage');
export const ContractsPage = lazyNamed(() => import('@/pages/ContractsPage'), 'ContractsPage');
export const KnowledgePage = lazyNamed(() => import('@/pages/KnowledgePage'), 'KnowledgePage');
export const SettingsProfilePage = lazyNamed(() => import('@/pages/settings/SettingsProfilePage'), 'SettingsProfilePage');
export const SettingsOrgPage = lazyNamed(() => import('@/pages/settings/SettingsOrgPage'), 'SettingsOrgPage');
export const SettingsTeamPage = lazyNamed(() => import('@/pages/settings/SettingsTeamPage'), 'SettingsTeamPage');
export const SettingsBillingPage = lazyNamed(() => import('@/pages/settings/SettingsBillingPage'), 'SettingsBillingPage');
export const SettingsIntegrationsPage = lazyNamed(() => import('@/pages/settings/SettingsIntegrationsPage'), 'SettingsIntegrationsPage');
export const SettingsNotificationsPage = lazyNamed(() => import('@/pages/settings/SettingsNotificationsPage'), 'SettingsNotificationsPage');
export const SettingsApiKeysPage = lazyNamed(() => import('@/pages/settings/SettingsApiKeysPage'), 'SettingsApiKeysPage');
export const AdminAuditPage = lazyNamed(() => import('@/pages/admin/AdminAuditPage'), 'AdminAuditPage');
export const AdminFlagsPage = lazyNamed(() => import('@/pages/admin/AdminFlagsPage'), 'AdminFlagsPage');
