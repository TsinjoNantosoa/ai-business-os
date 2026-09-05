import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export function KpiCard({
  label,
  value,
  change,
  icon: Icon,
  trend = 'up',
  emphasis = false,
  className,
}: {
  label: string;
  value: string | number;
  change?: number;
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'neutral';
  format?: 'number' | 'currency' | 'percent';
  emphasis?: boolean;
  className?: string;
}) {
  const isPositive = trend === 'up';
  const isNegative = trend === 'down';

  return (
    <Card className={cn('group relative overflow-hidden transition-[border-color,box-shadow] hover:border-primary/25 hover:shadow-elevated', emphasis && 'border-primary/20 bg-gradient-to-br from-primary/[.065] to-card', className)}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <p className={cn('mt-2 font-bold leading-none tracking-[-0.03em]', emphasis ? 'text-[2rem]' : 'text-[1.65rem]')}>{value}</p>
            {change !== undefined && (
              <div className="mt-2 flex items-center gap-1.5">
                <span
                  className={cn(
                    'inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-xs font-medium',
                    isPositive && 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
                    isNegative && 'bg-red-500/10 text-red-600 dark:text-red-400',
                    trend === 'neutral' && 'bg-muted text-muted-foreground'
                  )}
                >
                  {isPositive && <ArrowUpRight className="h-3 w-3" />}
                  {isNegative && <ArrowDownRight className="h-3 w-3" />}
                  {change > 0 ? '+' : ''}{change}%
                </span>
                <span className="text-xs text-muted-foreground">vs mois dernier</span>
              </div>
            )}
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary transition-colors group-hover:bg-primary/15">
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
