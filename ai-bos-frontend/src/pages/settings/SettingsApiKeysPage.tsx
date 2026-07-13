import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { PageHeader } from '@/components/shared/PageHeader';
import { useI18n } from '@/lib/i18n/store';
import { Plus, Copy, Trash2, KeyRound, Loader2 } from 'lucide-react';
import { createApiKey, getApiKeys, revokeApiKey } from '@/lib/api/services';
import type { ApiKey } from '@/lib/api/types';
import { formatRelativeTime } from '@/lib/utils';

export function SettingsApiKeysPage() {
  const { t } = useI18n();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState('');
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setKeys(await getApiKeys());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const created = await createApiKey({ name: name.trim() });
      setCreatedSecret(created.secret || null);
      setName('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de création');
    } finally {
      setSaving(false);
    }
  };

  const handleRevoke = async (id: string) => {
    setSaving(true);
    try {
      await revokeApiKey(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de révocation');
    } finally {
      setSaving(false);
    }
  };

  const copy = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
    } catch {
      /* ignore */
    }
  };

  return (
    <div>
      <PageHeader
        title={t('nav.settingsApiKeys')}
        description="Gérez vos clés API pour intégrations M2M"
        actions={
          <Button
            onClick={() => {
              setCreatedSecret(null);
              setCreateOpen(true);
            }}
          >
            <Plus className="h-4 w-4" />
            Nouvelle clé
          </Button>
        }
      />
      {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center p-10">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nom</TableHead>
                  <TableHead>Clé</TableHead>
                  <TableHead>Statut</TableHead>
                  <TableHead>Créée le</TableHead>
                  <TableHead>Dernière utilisation</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.map((k) => (
                  <TableRow key={k.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <KeyRound className="h-4 w-4 text-muted-foreground" />
                        {k.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="rounded bg-muted px-2 py-1 text-xs">{k.maskedKey}</code>
                    </TableCell>
                    <TableCell>
                      <Badge variant={k.active ? 'success' : 'muted'}>{k.active ? 'active' : 'revoked'}</Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(k.createdAt).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {k.lastUsedAt ? formatRelativeTime(k.lastUsedAt) : '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon-sm" onClick={() => void copy(k.maskedKey)}>
                          <Copy className="h-4 w-4" />
                        </Button>
                        {k.active && (
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            className="text-destructive"
                            disabled={saving}
                            onClick={() => void handleRevoke(k.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={createOpen}
        onOpenChange={(open) => {
          setCreateOpen(open);
          if (!open) setCreatedSecret(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nouvelle clé API</DialogTitle>
            <DialogDescription>
              La clé secrète ne sera affichée qu&apos;une seule fois. Stockez-la en lieu sûr.
            </DialogDescription>
          </DialogHeader>
          {!createdSecret ? (
            <div className="space-y-3 py-2">
              <div className="space-y-2">
                <Label htmlFor="key-name">Nom</Label>
                <Input
                  id="key-name"
                  placeholder="Production API"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
            </div>
          ) : (
            <div className="space-y-2 py-2">
              <Label>Secret (copiez maintenant)</Label>
              <code className="block break-all rounded bg-muted p-3 text-xs">{createdSecret}</code>
              <Button variant="outline" size="sm" onClick={() => void copy(createdSecret)}>
                <Copy className="h-4 w-4" />
                Copier
              </Button>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              {t('common.cancel')}
            </Button>
            {!createdSecret && (
              <Button onClick={() => void handleCreate()} disabled={saving || !name.trim()}>
                {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                Créer
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
