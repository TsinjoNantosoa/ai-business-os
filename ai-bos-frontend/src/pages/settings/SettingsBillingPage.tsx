import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { PageHeader } from '@/components/shared/PageHeader';
import { TableSkeleton } from '@/components/shared/Skeletons';
import { useI18n } from '@/lib/i18n/store';
import { Check, Zap, Database, Users, Download } from 'lucide-react';
import { createBillingCheckout, getBillingOverview } from '@/lib/api/services';
import { formatCurrency, formatDate } from '@/lib/utils';
import { toast } from 'sonner';

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

  const { subscription, invoices } = data;
  const plan = subscription.plan;
  const usageCards = [
    { icon: Users, label: 'Sièges', ...subscription.usage.seats, color: 'bg-primary' },
    { icon: Zap, label: 'Tokens IA', ...subscription.usage.aiTokens, color: 'bg-violet-500' },
    { icon: Database, label: 'Stockage (Go)', ...subscription.usage.storageGb, color: 'bg-emerald-500' },
  ];

  return (
    <div>
      <PageHeader title={t('nav.settingsBilling')} description="Gérez votre abonnement et facturation" />
      <div className="space-y-6 max-w-4xl">
        <Card className="border-primary/20 bg-gradient-to-br from-primary-50/50 to-violet-50/30">
          <CardContent className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <Badge variant="default">Plan {plan.name}</Badge>
                  <span className="text-sm text-muted-foreground">
                    Renouvellement le {formatDate(subscription.renewalDate)}
                  </span>
                </div>
                <p className="mt-2 text-3xl font-bold">
                  {formatCurrency(plan.priceMonthly, plan.currency)}
                  <span className="text-base font-normal text-muted-foreground">/mois</span>
                </p>
              </div>
              <Button
                variant="outline"
                disabled={checkoutMutation.isPending}
                onClick={() => checkoutMutation.mutate(plan.code === 'enterprise' ? 'pro' : 'enterprise')}
              >
                Changer de plan
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {usageCards.map((u) => (
            <Card key={u.label}>
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${u.color} text-white`}>
                    <u.icon className="h-4 w-4" />
                  </div>
                  <span className="text-sm font-medium">{u.label}</span>
                </div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="font-semibold">{u.used.toLocaleString()}</span>
                  <span className="text-muted-foreground">{u.limit.toLocaleString()}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full rounded-full ${u.color}`}
                    style={{ width: `${Math.min(100, (u.used / Math.max(u.limit, 1)) * 100)}%` }}
                  />
                </div>
              </CardContent>
            </Card>
          ))}
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
                      {inv.pdfUrl ? (
                        <Button variant="ghost" size="sm" asChild>
                          <a href={inv.pdfUrl} target="_blank" rel="noreferrer">
                            <Download className="h-3.5 w-3.5" />PDF
                          </a>
                        </Button>
                      ) : (
                        <Button variant="ghost" size="sm" disabled><Download className="h-3.5 w-3.5" />PDF</Button>
                      )}
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
