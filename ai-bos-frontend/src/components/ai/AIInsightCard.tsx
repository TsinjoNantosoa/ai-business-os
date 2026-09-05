import type { ReactNode } from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type InsightMetric = { label: string; value: string; tone?: 'default' | 'warning' | 'danger' };

export function AIInsightCard({
  eyebrow = 'AI Business Insight',
  title,
  description,
  metrics = [],
  recommendation,
  primaryAction,
  secondaryAction,
  className,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  metrics?: InsightMetric[];
  recommendation?: string;
  primaryAction?: { label: string; onClick: () => void };
  secondaryAction?: { label: string; onClick: () => void };
  className?: string;
}) {
  return (
    <section className={cn('ai-surface relative overflow-hidden rounded-lg p-5', className)} aria-labelledby="ai-insight-title">
      <div className="absolute inset-y-0 left-0 w-0.5 bg-primary" aria-hidden />
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary/15 text-primary">
          <Sparkles className="h-[18px] w-[18px]" aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-primary">{eyebrow}</p>
            <Badge variant="default" className="h-5 bg-primary/15 px-1.5 text-[10px] text-primary shadow-none">IA</Badge>
          </div>
          <h2 id="ai-insight-title" className="mt-2 text-lg font-semibold tracking-tight">{title}</h2>
          {description && <p className="mt-1.5 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p>}

          {metrics.length > 0 && (
            <dl className="mt-4 grid gap-2 sm:grid-cols-3">
              {metrics.map((metric) => (
                <div key={metric.label} className="rounded-md border border-border/70 bg-background/35 px-3 py-2.5">
                  <dt className="text-xs text-muted-foreground">{metric.label}</dt>
                  <dd className={cn('mt-1 text-base font-semibold', metric.tone === 'warning' && 'text-amber-500', metric.tone === 'danger' && 'text-red-500')}>
                    {metric.value}
                  </dd>
                </div>
              ))}
            </dl>
          )}

          {recommendation && (
            <div className="mt-4 border-l-2 border-primary/45 pl-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Recommandation</p>
              <p className="mt-1 text-sm text-foreground">{recommendation}</p>
            </div>
          )}

          {(primaryAction || secondaryAction) && (
            <div className="mt-4 flex flex-wrap gap-2">
              {primaryAction && (
                <Button size="sm" onClick={primaryAction.onClick}>
                  {primaryAction.label}<ArrowRight aria-hidden />
                </Button>
              )}
              {secondaryAction && <Button size="sm" variant="outline" onClick={secondaryAction.onClick}>{secondaryAction.label}</Button>}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export function AIDecisionBadge({ children }: { children: ReactNode }) {
  return <span className="inline-flex items-center gap-1 rounded-full border border-primary/25 bg-primary/10 px-2 py-1 text-xs font-medium text-primary"><Sparkles className="h-3 w-3" />{children}</span>;
}
