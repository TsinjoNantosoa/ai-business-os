import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Download, Send, MoreHorizontal, FileText, Eye, Bell, Trash2 } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { ExportMenu } from '@/components/shared/ExportMenu';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TableSkeleton } from '@/components/shared/Skeletons';
import { EmptyState } from '@/components/shared/EmptyState';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { createInvoice, getContacts, getInvoices, sendInvoice } from '@/lib/api/services';
import { useI18n } from '@/lib/i18n/store';
import { useAuth } from '@/lib/auth/store';
import { formatCurrency, formatDate } from '@/lib/utils';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';
import type { Invoice } from '@/lib/api/types';
import { exportTextPdf, type ExportColumn } from '@/lib/export';

type LineDraft = { description: string; quantity: string; unitPrice: string };

const emptyLine = (): LineDraft => ({ description: '', quantity: '1', unitPrice: '' });

export function InvoicesPage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('finance.invoice.write');
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [createOpen, setCreateOpen] = useState(false);
  const [clientId, setClientId] = useState('');
  const [issueDate, setIssueDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [dueDate, setDueDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return d.toISOString().slice(0, 10);
  });
  const [taxRate, setTaxRate] = useState('20');
  const [lines, setLines] = useState<LineDraft[]>([emptyLine()]);
  const [viewInvoice, setViewInvoice] = useState<Invoice | null>(null);

  const { data: invoices, isLoading } = useQuery({ queryKey: ['invoices'], queryFn: getInvoices });
  const { data: contacts } = useQuery({
    queryKey: ['contacts'],
    queryFn: getContacts,
    enabled: createOpen,
  });

  const createMutation = useMutation({
    mutationFn: createInvoice,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['invoices'] });
      setCreateOpen(false);
      resetForm();
      toast.success('Facture créée');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer la facture'),
  });

  const sendMutation = useMutation({
    mutationFn: sendInvoice,
    onSuccess: (inv) => {
      void queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast.success(`Facture ${inv.invoiceNumber} envoyée`);
    },
    onError: (err: Error) => toast.error(err.message || "Impossible d'envoyer la facture"),
  });

  const filtered = useMemo(() => {
    if (!invoices) return [];
    return invoices.filter((inv) => {
      const matchSearch =
        !search ||
        inv.invoiceNumber.toLowerCase().includes(search.toLowerCase()) ||
        inv.clientName.toLowerCase().includes(search.toLowerCase());
      const matchStatus = statusFilter === 'all' || inv.status === statusFilter;
      return matchSearch && matchStatus;
    });
  }, [invoices, search, statusFilter]);

  const totalPaid = filtered.filter((i) => i.status === 'paid').reduce((s, i) => s + i.totalAmount, 0);
  const totalOverdue = filtered.filter((i) => i.status === 'overdue').reduce((s, i) => s + i.totalAmount, 0);
  const totalOutstanding = filtered
    .filter((i) => i.status === 'sent' || i.status === 'overdue')
    .reduce((s, i) => s + i.totalAmount, 0);

  const resetForm = () => {
    setClientId('');
    setIssueDate(new Date().toISOString().slice(0, 10));
    const d = new Date();
    d.setDate(d.getDate() + 30);
    setDueDate(d.toISOString().slice(0, 10));
    setTaxRate('20');
    setLines([emptyLine()]);
  };

  const exportColumns: ExportColumn<Invoice>[] = [
    { header: 'N° Facture', value: (inv) => inv.invoiceNumber },
    { header: 'Client', value: (inv) => inv.clientName },
    { header: 'Émission', value: (inv) => inv.issueDate },
    { header: 'Échéance', value: (inv) => inv.dueDate },
    { header: 'Montant', value: (inv) => inv.totalAmount },
    { header: 'Devise', value: (inv) => inv.currency },
    { header: 'Statut', value: (inv) => inv.status },
  ];

  const selectedContact = (contacts || []).find((c) => c.id === clientId);
  const canSubmit =
    !!clientId &&
    lines.some((l) => l.description && Number(l.quantity) > 0 && Number(l.unitPrice) >= 0) &&
    lines.every((l) => !l.description || (Number(l.quantity) > 0 && l.unitPrice !== ''));

  return (
    <div>
      <PageHeader
        title={t('nav.invoices')}
        description="Gérez vos factures et relances"
        actions={
          <>
            <ExportMenu
              filename="factures"
              title="Factures AI BOS"
              sheetName="Factures"
              columns={exportColumns}
              rows={filtered}
              label={t('common.export')}
            />
            {canWrite && (
              <Button
                onClick={() => {
                  resetForm();
                  setCreateOpen(true);
                }}
              >
                <Plus className="h-4 w-4" />
                Nouvelle facture
              </Button>
            )}
          </>
        }
      />

      <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Encaissé</p>
            <p className="mt-1 text-2xl font-bold text-emerald-600">{formatCurrency(totalPaid)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">En attente</p>
            <p className="mt-1 text-2xl font-bold text-amber-600">{formatCurrency(totalOutstanding)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">En retard</p>
            <p className="mt-1 text-2xl font-bold text-red-600">{formatCurrency(totalOverdue)}</p>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-4">
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder={t('common.search')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder={t('common.status')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('common.all')}</SelectItem>
              <SelectItem value="draft">Brouillon</SelectItem>
              <SelectItem value="sent">Envoyée</SelectItem>
              <SelectItem value="paid">Payée</SelectItem>
              <SelectItem value="overdue">En retard</SelectItem>
              <SelectItem value="cancelled">Annulée</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4">
              <TableSkeleton />
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState icon={FileText} title={t('common.noResults')} description="Aucune facture ne correspond à vos critères." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>N° Facture</TableHead>
                  <TableHead>Client</TableHead>
                  <TableHead className="hidden md:table-cell">Date émission</TableHead>
                  <TableHead>Échéance</TableHead>
                  <TableHead>Montant</TableHead>
                  <TableHead>{t('common.status')}</TableHead>
                  <TableHead className="text-right">{t('common.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell className="font-mono text-sm font-medium">{inv.invoiceNumber}</TableCell>
                    <TableCell className="text-sm">{inv.clientName}</TableCell>
                    <TableCell className="hidden md:table-cell text-sm text-muted-foreground">{formatDate(inv.issueDate)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatDate(inv.dueDate)}</TableCell>
                    <TableCell className="font-semibold">{formatCurrency(inv.totalAmount)}</TableCell>
                    <TableCell>
                      <StatusBadge status={inv.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon-sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => setViewInvoice(inv)}>
                            <Eye className="h-4 w-4" /> Voir
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => {
                              try {
                                exportTextPdf(inv.invoiceNumber, `Facture ${inv.invoiceNumber}`, [
                                  `Client: ${inv.clientName}`,
                                  `Émission: ${inv.issueDate}`,
                                  `Échéance: ${inv.dueDate}`,
                                  `Total: ${inv.totalAmount} ${inv.currency}`,
                                  `Statut: ${inv.status}`,
                                  ...(inv.lineItems || []).map(
                                    (li) =>
                                      `- ${li.description}: ${li.quantity} x ${li.unitPrice} = ${li.total}`,
                                  ),
                                ]);
                                toast.success('PDF téléchargé');
                              } catch (err) {
                                toast.error(err instanceof Error ? err.message : 'Export PDF impossible');
                              }
                            }}
                          >
                            <Download className="h-4 w-4" /> PDF
                          </DropdownMenuItem>
                          {canWrite && inv.status === 'draft' && (
                            <DropdownMenuItem
                              disabled={sendMutation.isPending}
                              onClick={() => sendMutation.mutate(inv.id)}
                            >
                              <Send className="h-4 w-4" /> Envoyer
                            </DropdownMenuItem>
                          )}
                          {inv.status === 'overdue' && (
                            <DropdownMenuItem onClick={() => toast.message('Relance enregistrée (simulation)')}>
                              <Bell className="h-4 w-4" /> Relancer
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Nouvelle facture</DialogTitle>
            <DialogDescription>Créez une nouvelle facture pour un client</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-2">
            <div className="col-span-2 space-y-2">
              <Label>Client</Label>
              <Select value={clientId} onValueChange={setClientId}>
                <SelectTrigger>
                  <SelectValue placeholder="Sélectionner un contact" />
                </SelectTrigger>
                <SelectContent>
                  {(contacts || []).map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.firstName} {c.lastName} — {c.company}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="invoiceDate">Date d&apos;émission</Label>
              <Input id="invoiceDate" type="date" value={issueDate} onChange={(e) => setIssueDate(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dueDate">Date d&apos;échéance</Label>
              <Input id="dueDate" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="taxRate">Taux de TVA (%)</Label>
              <Input id="taxRate" type="number" min={0} value={taxRate} onChange={(e) => setTaxRate(e.target.value)} />
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Lignes de facturation</Label>
              <div className="space-y-2">
                {lines.map((line, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2">
                    <Input
                      className="col-span-5"
                      placeholder="Description"
                      value={line.description}
                      onChange={(e) => {
                        const next = [...lines];
                        next[idx] = { ...line, description: e.target.value };
                        setLines(next);
                      }}
                    />
                    <Input
                      className="col-span-2"
                      type="number"
                      min={1}
                      placeholder="Qté"
                      value={line.quantity}
                      onChange={(e) => {
                        const next = [...lines];
                        next[idx] = { ...line, quantity: e.target.value };
                        setLines(next);
                      }}
                    />
                    <Input
                      className="col-span-3"
                      type="number"
                      min={0}
                      placeholder="Prix unit."
                      value={line.unitPrice}
                      onChange={(e) => {
                        const next = [...lines];
                        next[idx] = { ...line, unitPrice: e.target.value };
                        setLines(next);
                      }}
                    />
                    <div className="col-span-2 flex gap-1">
                      {idx === lines.length - 1 ? (
                        <Button type="button" variant="outline" size="icon" onClick={() => setLines([...lines, emptyLine()])}>
                          <Plus className="h-4 w-4" />
                        </Button>
                      ) : (
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          onClick={() => setLines(lines.filter((_, i) => i !== idx))}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              disabled={!canWrite || createMutation.isPending || !canSubmit || !selectedContact}
              onClick={() => {
                if (!selectedContact) return;
                const rate = Number(taxRate) || 0;
                createMutation.mutate({
                  clientId: selectedContact.id,
                  clientName: `${selectedContact.firstName} ${selectedContact.lastName}`.trim() || selectedContact.company,
                  issueDate: new Date(issueDate).toISOString(),
                  dueDate: new Date(dueDate).toISOString(),
                  lineItems: lines
                    .filter((l) => l.description && Number(l.quantity) > 0)
                    .map((l) => ({
                      description: l.description,
                      quantity: Number(l.quantity),
                      unitPrice: Number(l.unitPrice),
                      taxRate: rate,
                    })),
                });
              }}
            >
              <FileText className="h-4 w-4" />
              {createMutation.isPending ? 'Création…' : 'Créer la facture'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!viewInvoice} onOpenChange={(open) => !open && setViewInvoice(null)}>
        <DialogContent className="max-w-lg">
          {viewInvoice && (
            <>
              <DialogHeader>
                <DialogTitle>{viewInvoice.invoiceNumber}</DialogTitle>
                <DialogDescription>{viewInvoice.clientName}</DialogDescription>
              </DialogHeader>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Statut</span>
                  <StatusBadge status={viewInvoice.status} />
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Émission</span>
                  <span>{formatDate(viewInvoice.issueDate)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Échéance</span>
                  <span>{formatDate(viewInvoice.dueDate)}</span>
                </div>
                <div className="flex justify-between font-semibold">
                  <span>Total</span>
                  <span>{formatCurrency(viewInvoice.totalAmount)}</span>
                </div>
                {viewInvoice.lineItems?.length > 0 && (
                  <div className="space-y-1 border-t pt-3">
                    {viewInvoice.lineItems.map((li) => (
                      <div key={li.id} className="flex justify-between gap-2">
                        <span className="text-muted-foreground">
                          {li.description} × {li.quantity}
                        </span>
                        <span>{formatCurrency(li.total)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <DialogFooter>
                {canWrite && viewInvoice.status === 'draft' && (
                  <Button
                    disabled={sendMutation.isPending}
                    onClick={() => {
                      sendMutation.mutate(viewInvoice.id, {
                        onSuccess: (inv) => setViewInvoice(inv),
                      });
                    }}
                  >
                    <Send className="h-4 w-4" /> Envoyer
                  </Button>
                )}
                <Button variant="outline" onClick={() => setViewInvoice(null)}>
                  Fermer
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
