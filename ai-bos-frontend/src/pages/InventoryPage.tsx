import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Package, AlertTriangle, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { createInventoryItem, getInventory } from '@/lib/api/services';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

export function InventoryPage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('inventory.write');
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [sku, setSku] = useState('');
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [warehouse, setWarehouse] = useState('');
  const [quantity, setQuantity] = useState('0');
  const [reorderLevel, setReorderLevel] = useState('10');
  const [unitPrice, setUnitPrice] = useState('0');
  const { data: items } = useQuery({ queryKey: ['inventory'], queryFn: getInventory });

  const filtered = (items || []).filter(
    (i) =>
      !search ||
      i.name.toLowerCase().includes(search.toLowerCase()) ||
      i.sku.toLowerCase().includes(search.toLowerCase()),
  );
  const lowStock = (items || []).filter((i) => i.status === 'low_stock').length;
  const outOfStock = (items || []).filter((i) => i.status === 'out_of_stock').length;
  const totalValue = (items || []).reduce((s, i) => s + i.quantity * i.unitPrice, 0);

  const reset = () => {
    setSku('');
    setName('');
    setCategory('');
    setWarehouse('');
    setQuantity('0');
    setReorderLevel('10');
    setUnitPrice('0');
  };

  const createMutation = useMutation({
    mutationFn: createInventoryItem,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['inventory'] });
      setCreateOpen(false);
      reset();
      toast.success('Article créé');
    },
    onError: (err: Error) => toast.error(err.message || 'Création impossible'),
  });

  const canSubmit = sku.trim() && name.trim() && category.trim() && warehouse.trim();

  return (
    <div>
      <PageHeader
        title={t('nav.inventory')}
        description="Gérez vos stocks"
        actions={
          canWrite ? (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              Nouvel article
            </Button>
          ) : undefined
        }
      />
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Package className="h-5 w-5 text-primary" />
              <p className="text-sm text-muted-foreground">Articles</p>
            </div>
            <p className="mt-1 text-2xl font-bold">{items?.length || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              <p className="text-sm text-muted-foreground">Stock faible</p>
            </div>
            <p className="mt-1 text-2xl font-bold text-amber-600">{lowStock}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <p className="text-sm text-muted-foreground">Rupture</p>
            </div>
            <p className="mt-1 text-2xl font-bold text-red-600">{outOfStock}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Package className="h-5 w-5 text-emerald-500" />
              <p className="text-sm text-muted-foreground">Valeur stock</p>
            </div>
            <p className="mt-1 text-2xl font-bold">{formatCurrency(totalValue)}</p>
          </CardContent>
        </Card>
      </div>
      <Card className="mb-4">
        <CardContent className="p-4">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Rechercher..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>SKU</TableHead>
                <TableHead>Article</TableHead>
                <TableHead>Catégorie</TableHead>
                <TableHead>Quantité</TableHead>
                <TableHead>Seuil</TableHead>
                <TableHead>Entrepôt</TableHead>
                <TableHead>Prix unit.</TableHead>
                <TableHead>Statut</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((i) => (
                <TableRow key={i.id}>
                  <TableCell className="font-mono text-sm">{i.sku}</TableCell>
                  <TableCell className="text-sm font-medium">{i.name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{i.category}</TableCell>
                  <TableCell className="text-sm font-semibold">{i.quantity}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{i.reorderLevel}</TableCell>
                  <TableCell className="text-sm">{i.warehouse}</TableCell>
                  <TableCell className="text-sm">{formatCurrency(i.unitPrice)}</TableCell>
                  <TableCell>
                    <StatusBadge status={i.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nouvel article</DialogTitle>
            <DialogDescription>Ajouter un article au stock.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-3 py-2 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>SKU</Label>
              <Input value={sku} onChange={(e) => setSku(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Nom</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Catégorie</Label>
              <Input value={category} onChange={(e) => setCategory(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Entrepôt</Label>
              <Input value={warehouse} onChange={(e) => setWarehouse(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Quantité</Label>
              <Input type="number" min={0} value={quantity} onChange={(e) => setQuantity(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Seuil réappro</Label>
              <Input
                type="number"
                min={0}
                value={reorderLevel}
                onChange={(e) => setReorderLevel(e.target.value)}
              />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label>Prix unitaire</Label>
              <Input type="number" min={0} value={unitPrice} onChange={(e) => setUnitPrice(e.target.value)} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Annuler
            </Button>
            <Button
              disabled={!canSubmit || createMutation.isPending}
              onClick={() =>
                createMutation.mutate({
                  sku: sku.trim(),
                  name: name.trim(),
                  category: category.trim(),
                  warehouse: warehouse.trim(),
                  quantity: Number(quantity) || 0,
                  reorderLevel: Number(reorderLevel) || 0,
                  unitPrice: Number(unitPrice) || 0,
                })
              }
            >
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Créer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
