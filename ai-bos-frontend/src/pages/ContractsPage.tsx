import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, Search, AlertTriangle } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { getContracts } from '@/lib/api/services';
import type { Contract } from '@/lib/api/types';
import { useI18n } from '@/lib/i18n/store';
import { formatCurrency, formatDate } from '@/lib/utils';

type StatusFilter = 'all' | 'expiring' | Contract['status'];

export function ContractsPage() {
  const { t } = useI18n();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [selected, setSelected] = useState<Contract | null>(null);
  const { data: contracts } = useQuery({ queryKey: ['contracts'], queryFn: getContracts });

  const expiringList = useMemo(
    () => (contracts || []).filter((c) => c.status === 'expiring'),
    [contracts],
  );

  const filtered = useMemo(() => {
    return (contracts || []).filter((c) => {
      const matchSearch =
        !search ||
        c.title.toLowerCase().includes(search.toLowerCase()) ||
        c.counterparty.toLowerCase().includes(search.toLowerCase());
      const matchStatus = statusFilter === 'all' ? true : c.status === statusFilter;
      return matchSearch && matchStatus;
    });
  }, [contracts, search, statusFilter]);

  return (
    <div>
      <PageHeader
        title={t('nav.contracts')}
        description="Gérez vos contrats et accords"
        actions={<Button><Plus className="h-4 w-4" />Nouveau contrat</Button>}
      />
      {expiringList.length > 0 && (
        <Card className="mb-4 border-amber-200 bg-amber-50/30">
          <CardContent className="flex flex-wrap items-center gap-3 p-4">
            <AlertTriangle className="h-5 w-5 shrink-0 text-amber-500" />
            <p className="text-sm">
              {expiringList.length} contrat(s) arrivent à échéance dans les 30 prochains jours
            </p>
            <Button
              variant="outline"
              size="sm"
              className="ml-auto"
              onClick={() => {
                setStatusFilter('expiring');
                setSearch('');
              }}
            >
              Voir
            </Button>
          </CardContent>
        </Card>
      )}
      <Card className="mb-4">
        <CardContent className="flex flex-wrap items-center gap-3 p-4">
          <div className="relative max-w-md flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Rechercher..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          {statusFilter !== 'all' && (
            <Button variant="ghost" size="sm" onClick={() => setStatusFilter('all')}>
              Effacer le filtre ({statusFilter})
            </Button>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Titre</TableHead>
                <TableHead>Contrepartie</TableHead>
                <TableHead className="hidden md:table-cell">Type</TableHead>
                <TableHead>Valeur</TableHead>
                <TableHead>Échéance</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead className="hidden lg:table-cell">Responsable</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((c) => (
                <TableRow
                  key={c.id}
                  className="cursor-pointer"
                  onClick={() => setSelected(c)}
                >
                  <TableCell className="text-sm font-medium">{c.title}</TableCell>
                  <TableCell className="text-sm">{c.counterparty}</TableCell>
                  <TableCell className="hidden md:table-cell">
                    <Badge variant="muted" className="capitalize">{c.type}</Badge>
                  </TableCell>
                  <TableCell className="font-semibold">{formatCurrency(c.value)}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{formatDate(c.endDate)}</TableCell>
                  <TableCell><StatusBadge status={c.status} /></TableCell>
                  <TableCell className="hidden text-sm lg:table-cell">{c.owner}</TableCell>
                </TableRow>
              ))}
              {filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-sm text-muted-foreground">
                    Aucun contrat pour ce filtre.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-md">
          {selected && (
            <>
              <DialogHeader>
                <DialogTitle>{selected.title}</DialogTitle>
                <DialogDescription>{selected.counterparty}</DialogDescription>
                <div className="pt-1"><StatusBadge status={selected.status} /></div>
              </DialogHeader>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Type</p>
                  <p className="font-medium capitalize">{selected.type}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Valeur</p>
                  <p className="font-medium">{formatCurrency(selected.value)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Début</p>
                  <p className="font-medium">{formatDate(selected.startDate)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Échéance</p>
                  <p className="font-medium">{formatDate(selected.endDate)}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-xs text-muted-foreground">Responsable</p>
                  <p className="font-medium">{selected.owner}</p>
                </div>
              </div>
              <DialogFooter>
                <Button onClick={() => setSelected(null)}>Fermer</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
