import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, ArrowRight, Check, Trash2, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { ExportMenu } from '@/components/shared/ExportMenu';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { createOrder, getOrders } from '@/lib/api/services';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { formatCurrency, formatDate } from '@/lib/utils';
import { toast } from 'sonner';
import type { Order } from '@/lib/api/types';
import type { ExportColumn } from '@/lib/export';

interface LineItemDraft {
  description: string;
  quantity: string;
  unitPrice: string;
}

const EMPTY_LINE: LineItemDraft = { description: '', quantity: '1', unitPrice: '' };

export function SalesOrdersPage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('sales.order.write');
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [wizardStep, setWizardStep] = useState(0);
  const [customerName, setCustomerName] = useState('');
  const [lines, setLines] = useState<LineItemDraft[]>([{ ...EMPTY_LINE }]);
  const { data: orders } = useQuery({ queryKey: ['orders'], queryFn: getOrders });

  const filtered = (orders || []).filter((o) => !search || o.orderNumber.toLowerCase().includes(search.toLowerCase()) || o.customerName.toLowerCase().includes(search.toLowerCase()));

  const validLines = lines
    .filter((line) => line.description.trim() && Number(line.quantity) > 0 && Number(line.unitPrice) >= 0)
    .map((line) => ({
      description: line.description.trim(),
      quantity: Number(line.quantity),
      unitPrice: Number(line.unitPrice),
    }));
  const total = validLines.reduce((sum, line) => sum + line.quantity * line.unitPrice, 0);

  const resetWizard = () => {
    setWizardStep(0);
    setCustomerName('');
    setLines([{ ...EMPTY_LINE }]);
  };

  const createMutation = useMutation({
    mutationFn: createOrder,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['orders'] });
      setCreateOpen(false);
      resetWizard();
      toast.success('Devis créé');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer le devis'),
  });

  const setLine = (index: number, patch: Partial<LineItemDraft>) => {
    setLines((prev) => prev.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  };

  const canGoNext = wizardStep === 0 ? customerName.trim().length > 0 : wizardStep === 1 ? validLines.length > 0 : true;

  const handleNext = () => {
    if (wizardStep < 2) {
      setWizardStep(wizardStep + 1);
      return;
    }
    createMutation.mutate({ customerName: customerName.trim(), lineItems: validLines });
  };

  return (
    <div>
      <PageHeader
        title={t('nav.salesOrders')}
        description="Gérez vos devis et commandes"
        actions={
          <>
            <ExportMenu
              filename="devis-commandes"
              title="Devis & Commandes"
              sheetName="Commandes"
              columns={[
                { header: 'N°', value: (o) => o.orderNumber },
                { header: 'Client', value: (o) => o.customerName },
                { header: 'Date', value: (o) => o.date },
                { header: 'Montant', value: (o) => o.amount },
                { header: 'Statut', value: (o) => o.status },
                { header: 'Commercial', value: (o) => o.salesRepName },
              ] satisfies ExportColumn<Order>[]}
              rows={filtered}
              label={t('common.export')}
            />
            {canWrite ? (
              <Button onClick={() => setCreateOpen(true)}>
                <Plus className="h-4 w-4" />
                Nouveau devis
              </Button>
            ) : undefined}
          </>
        }
      />
      <Card className="mb-4">
        <CardContent className="p-4">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Rechercher..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader><TableRow><TableHead>N°</TableHead><TableHead>Client</TableHead><TableHead className="hidden md:table-cell">Date</TableHead><TableHead>Montant</TableHead><TableHead>Statut</TableHead><TableHead className="hidden lg:table-cell">Commercial</TableHead></TableRow></TableHeader>
            <TableBody>
              {filtered.map((o) => (
                <TableRow key={o.id}>
                  <TableCell className="font-mono text-sm font-medium">{o.orderNumber}</TableCell>
                  <TableCell className="text-sm">{o.customerName}</TableCell>
                  <TableCell className="hidden md:table-cell text-sm text-muted-foreground">{formatDate(o.date)}</TableCell>
                  <TableCell className="font-semibold">{formatCurrency(o.amount)}</TableCell>
                  <TableCell><StatusBadge status={o.status} /></TableCell>
                  <TableCell className="hidden lg:table-cell text-sm">{o.salesRepName}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={(open) => { setCreateOpen(open); if (!open) resetWizard(); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Créer un devis</DialogTitle><DialogDescription>Étape {wizardStep + 1} sur 3</DialogDescription></DialogHeader>
          <div className="flex items-center justify-between mb-4">
            {['Client', 'Produits', 'Confirmation'].map((step, i) => (
              <div key={i} className="flex items-center">
                <div className={`flex h-8 w-8 items-center justify-center rounded-lg text-xs font-medium ${i <= wizardStep ? 'bg-primary text-white' : 'bg-muted text-muted-foreground'}`}>
                  {i < wizardStep ? <Check className="h-4 w-4" /> : i + 1}
                </div>
                {i < 2 && <div className={`mx-1 h-0.5 w-12 ${i < wizardStep ? 'bg-primary' : 'bg-muted'}`} />}
              </div>
            ))}
          </div>
          {wizardStep === 0 && (
            <div className="space-y-3">
              <Input placeholder="Nom du client" value={customerName} onChange={(e) => setCustomerName(e.target.value)} autoFocus />
            </div>
          )}
          {wizardStep === 1 && (
            <div className="space-y-2">
              {lines.map((line, i) => (
                <div key={i} className="grid grid-cols-12 gap-2">
                  <Input className="col-span-6" placeholder="Description" value={line.description} onChange={(e) => setLine(i, { description: e.target.value })} />
                  <Input className="col-span-2" placeholder="Qté" type="number" min="1" value={line.quantity} onChange={(e) => setLine(i, { quantity: e.target.value })} />
                  <Input className="col-span-3" placeholder="Prix €" type="number" min="0" value={line.unitPrice} onChange={(e) => setLine(i, { unitPrice: e.target.value })} />
                  <Button variant="ghost" size="icon-sm" className="col-span-1" disabled={lines.length === 1} onClick={() => setLines((prev) => prev.filter((_, idx) => idx !== i))}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
              <Button variant="outline" size="sm" onClick={() => setLines((prev) => [...prev, { ...EMPTY_LINE }])}>
                <Plus className="h-3.5 w-3.5" />Ajouter ligne
              </Button>
            </div>
          )}
          {wizardStep === 2 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">Récapitulatif — {customerName}</p>
              <div className="rounded-lg border border-border p-3 space-y-1">
                {validLines.map((line, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span>{line.description} × {line.quantity}</span>
                    <span>{formatCurrency(line.quantity * line.unitPrice)}</span>
                  </div>
                ))}
                <div className="flex justify-between border-t border-border pt-1 font-semibold">
                  <span>Total</span>
                  <span>{formatCurrency(total)}</span>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            {wizardStep > 0 && <Button variant="outline" onClick={() => setWizardStep(wizardStep - 1)}>Retour</Button>}
            <Button onClick={handleNext} disabled={!canGoNext || createMutation.isPending}>
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : wizardStep < 2 ? <><span>Suivant</span><ArrowRight className="h-4 w-4" /></> : 'Créer le devis'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
