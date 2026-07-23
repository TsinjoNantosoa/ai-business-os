import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { PageHeader } from '@/components/shared/PageHeader';
import { ExportMenu } from '@/components/shared/ExportMenu';
import { TableSkeleton } from '@/components/shared/Skeletons';
import { useI18n } from '@/lib/i18n/store';
import { Check, Zap, Database, Users, Download } from 'lucide-react';
import { createBillingCheckout, getBillingOverview } from '@/lib/api/services';
import { formatCurrency, formatDate } from '@/lib/utils';
import { toast } from 'sonner';
import { exportTextPdf, type ExportColumn } from '@/lib/export';
import type { BillingInvoice } from '@/lib/api/types';

export function SettingsBillingPage() {
  const { t } = useI18n();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['billing-overview'],
    queryFn: getBillingOverview,
  });

  const checkoutMutation = useMutation({
    mutationFn: (planCode: string) => createBillingCheckout(planCode),
    onSuccess: (session) => {
      window.location.href = session.checkoutUrl;
    },
    onError: () => toast.error('Impossible de démarrer le checkout'),
  });

  if (isLoading || !data) {
    return (
      <div>
        <PageHeader title={t('nav.settingsBilling')} description="Gérez votre abonnement et facturation" />
        <TableSkeleton rows={4} />
      </div>
    );
  }

  const { subscription, invoices, quotas } = data;
  const plan = subscription.plan;
  const usageCards = [
    { icon: Users, label: 'Sièges', ...subscription.usage.seats, color: 'bg-primary' },
    { icon: Zap, label: 'Tokens IA', ...subscription.usage.aiTokens, color: 'bg-violet-500' },
    { icon: Database, label: 'Stockage (Go)', ...subscription.usage.storageGb, color: 'bg-emerald-500' },
  ];
  const rpmLimit = quotas?.aiRpm ?? plan.aiRpm ?? subscription.usage.aiRpm?.limit ?? 20;

  const invoiceColumns: ExportColumn<BillingInvoice>[] = [
    { header: 'N°', value: (inv) => inv.invoiceNumber },
    { header: 'Date', value: (inv) => inv.createdAt },
    { header: 'Montant', value: (inv) => inv.amount },
    { header: 'Devise', value: (inv) => inv.currency },
    { header: 'Statut', value: (inv) => inv.status },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.settingsBilling')}
        description="Gérez votre abonnement et facturation"
        actions={
          <ExportMenu
            filename="factures-abonnement"
            title="Factures abonnement AI BOS"
            sheetName="Factures"
            columns={invoiceColumns}
            rows={invoices}
          />
        }
      />
      <div className="space-y-6">
        <Card className="border-primary/20 bg-gradient-to-br from-primary-50/50 to-violet-50/30">
          <CardContent className="p-6 sm:p-7">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="default">Plan {plan.name}</Badge>
                  <span className="text-sm text-muted-foreground">
                    Renouvellement le {formatDate(subscription.renewalDate)}
                  </span>
                </div>
                <p className="mt-3 text-3xl font-bold tracking-tight">
                  {formatCurrency(plan.priceMonthly, plan.currency)}
                  <span className="text-base font-normal text-muted-foreground">/mois</span>
                </p>
              </div>
              <Button
                className="shrink-0"
                disabled={checkoutMutation.isPending}
                onClick={() => checkoutMutation.mutate(plan.code === 'enterprise' ? 'pro' : 'enterprise')}
              >
                Changer de plan
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {usageCards.map((u) => (
            <Card key={u.label}>
              <CardContent className="p-5">
                <div className="mb-4 flex items-center gap-2.5">
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${u.color} text-white`}>
                    <u.icon className="h-4 w-4" />
                  </div>
                  <span className="text-sm font-medium">{u.label}</span>
                </div>
                <div className="mb-2 flex items-baseline justify-between gap-2 text-sm">
                  <span className="text-lg font-semibold tabular-nums">{u.used.toLocaleString('fr-FR')}</span>
                  <span className="text-muted-foreground tabular-nums">/ {u.limit.toLocaleString('fr-FR')}</span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full rounded-full ${u.color}`}
                    style={{ width: `${Math.min(100, (u.used / Math.max(u.limit, 1)) * 100)}%` }}
                  />
                </div>
              </CardContent>
            </Card>
          ))}
          <Card>
            <CardContent className="p-5">
              <div className="mb-4 flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500 text-white">
                  <Zap className="h-4 w-4" />
                </div>
                <span className="text-sm font-medium">RPM Copilot</span>
              </div>
              <p className="text-lg font-semibold tabular-nums">{rpmLimit} / min</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Hard limit plan {plan.name} (S35)
              </p>
              {quotas?.tokensExhausted && (
                <p className="mt-3 text-xs font-medium text-destructive">
                  Quota tokens épuisé — upgradez le plan.
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Historique des factures</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => refetch()}>Actualiser</Button>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>N°</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Montant</TableHead>
                  <TableHead>Statut</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell className="font-mono text-sm">{inv.invoiceNumber}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatDate(inv.createdAt)}</TableCell>
                    <TableCell className="font-semibold">{formatCurrency(inv.amount, inv.currency)}</TableCell>
                    <TableCell>
                      <Badge variant={inv.status === 'paid' ? 'success' : 'muted'} className="gap-1">
                        {inv.status === 'paid' && <Check className="h-3 w-3" />}
                        {inv.status === 'paid' ? 'Payée' : inv.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          try {
                            exportTextPdf(inv.invoiceNumber, `Facture ${inv.invoiceNumber}`, [
                              `Date: ${formatDate(inv.createdAt)}`,
                              `Montant: ${inv.amount} ${inv.currency}`,
                              `Statut: ${inv.status}`,
                              `Plan: ${plan.name}`,
                            ]);
                            toast.success('PDF téléchargé');
                          } catch (err) {
                            toast.error(err instanceof Error ? err.message : 'Export PDF impossible');
                          }
                        }}
                      >
                        <Download className="h-3.5 w-3.5" />
                        PDF
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
