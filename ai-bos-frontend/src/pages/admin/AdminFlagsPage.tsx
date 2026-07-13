import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/PageHeader';
import { useI18n } from '@/lib/i18n/store';
import { Flag, Loader2 } from 'lucide-react';
import { getAdminFeatureFlags, updateFeatureFlag } from '@/lib/api/services';
import type { FeatureFlag } from '@/lib/api/types';

const ENV_COLORS: Record<string, string> = {
  production: 'success',
  beta: 'warning',
  alpha: 'danger',
  planned: 'muted',
};

export function AdminFlagsPage() {
  const { t } = useI18n();
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setFlags(await getAdminFeatureFlags());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const toggle = async (flag: FeatureFlag, enabled: boolean) => {
    setSavingKey(flag.key);
    setError(null);
    try {
      const updated = await updateFeatureFlag(flag.key, { enabled });
      setFlags((prev) => prev.map((f) => (f.key === updated.key ? { ...f, ...updated } : f)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de mise à jour');
      await load();
    } finally {
      setSavingKey(null);
    }
  };

  return (
    <div>
      <PageHeader title={t('nav.adminFlags')} description="Activez ou désactivez les fonctionnalités par organisation" />
      {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
      {loading ? (
        <div className="flex items-center justify-center p-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {flags.map((flag) => (
            <Card key={flag.key}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50 text-primary">
                      <Flag className="h-4 w-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold">{flag.name}</h3>
                      <p className="text-xs text-muted-foreground">{flag.description}</p>
                      <p className="mt-1 text-[10px] text-muted-foreground">{flag.key}</p>
                    </div>
                  </div>
                  <Switch
                    checked={flag.enabled}
                    disabled={savingKey === flag.key}
                    onCheckedChange={(checked) => void toggle(flag, checked)}
                  />
                </div>
                <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
                  <Badge variant={(ENV_COLORS[flag.env] as 'success' | 'warning' | 'danger' | 'muted') || 'muted'} className="capitalize">
                    {flag.env}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {flag.enabled ? 'Activé' : 'Désactivé'}
                    {flag.source ? ` · ${flag.source}` : ''}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
