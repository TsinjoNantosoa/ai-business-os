import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/PageHeader';
import { useI18n } from '@/lib/i18n/store';
import { Flag, Loader2 } from 'lucide-react';
import { getAdminFeatureFlags, updateFeatureFlag } from '@/lib/api/services';
import type { FeatureFlag } from '@/lib/api/types';
import { cn } from '@/lib/utils';

const ENV_META: Record<string, { variant: 'success' | 'warning' | 'danger' | 'muted'; label: string }> = {
  production: { variant: 'success', label: 'Production' },
  beta: { variant: 'warning', label: 'Bêta' },
  alpha: { variant: 'danger', label: 'Alpha' },
  planned: { variant: 'muted', label: 'Planifié' },
};

const SOURCE_LABEL: Record<string, string> = {
  plan: 'plan',
  org: 'organisation',
  default: 'défaut',
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
          {flags.map((flag) => {
            const env = ENV_META[flag.env] || { variant: 'muted' as const, label: flag.env };
            const source = flag.source ? SOURCE_LABEL[flag.source] || flag.source : null;
            return (
              <Card key={flag.key} className="transition-shadow hover:shadow-elevated">
                <CardContent className="flex h-full flex-col p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex min-w-0 items-start gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-50 text-primary">
                        <Flag className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <h3 className="text-sm font-semibold leading-snug">{flag.name}</h3>
                        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{flag.description}</p>
                        <code className="mt-2 inline-block rounded bg-muted px-1.5 py-0.5 text-[10px] text-slate-600">
                          {flag.key}
                        </code>
                      </div>
                    </div>
                    <Switch
                      checked={flag.enabled}
                      disabled={savingKey === flag.key}
                      onCheckedChange={(checked) => void toggle(flag, checked)}
                    />
                  </div>
                  <div className="mt-auto flex items-center justify-between gap-2 border-t border-border pt-4 mt-4">
                    <Badge variant={env.variant}>{env.label}</Badge>
                    <span
                      className={cn(
                        'text-xs font-medium',
                        flag.enabled ? 'text-emerald-600' : 'text-muted-foreground',
                      )}
                    >
                      {flag.enabled ? 'Activé' : 'Désactivé'}
                      {source ? ` · ${source}` : ''}
                    </span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
