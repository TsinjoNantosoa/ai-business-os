import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Area, BarChart, Bar, Line, LineChart, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell,
} from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { ExportMenu } from '@/components/shared/ExportMenu';
import { KpiCard } from '@/components/shared/KpiCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getAnalytics } from '@/lib/api/services';
import { useI18n } from '@/lib/i18n/store';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/utils';
import type { ExportColumn } from '@/lib/export';

const PERIODS = [
  { id: '3m', label: '3 mois', months: 3 },
  { id: '6m', label: '6 mois', months: 6 },
  { id: '12m', label: '12 mois', months: 12 },
] as const;

const PIE_COLORS = ['#4f46e5', '#0d9488', '#f59e0b', '#ec4899', '#3b82f6'];

function sliceTail<T>(rows: T[], n: number): T[] {
  if (!rows.length) return rows;
  return rows.slice(Math.max(0, rows.length - n));
}

export function AnalyticsPage() {
  const { t } = useI18n();
  const [period, setPeriod] = useState<(typeof PERIODS)[number]['id']>('12m');
  const { data: analytics } = useQuery({ queryKey: ['analytics'], queryFn: getAnalytics });

  const months = PERIODS.find((p) => p.id === period)?.months ?? 12;

  const kpis = analytics?.kpis || [];
  const revenue = useMemo(() => sliceTail(analytics?.revenue || [], months), [analytics?.revenue, months]);
  const users = useMemo(() => sliceTail(analytics?.users || [], months), [analytics?.users, months]);
  const conversion = analytics?.conversion || [];
  const churn = useMemo(() => sliceTail(analytics?.churn || [], months), [analytics?.churn, months]);

  const exportRows = useMemo(
    () => [
      ...revenue.map((r) => ({
        section: 'Revenu',
        label: r.month,
        metric: 'revenu',
        value: r.revenue,
      })),
      ...revenue.map((r) => ({
        section: 'Revenu',
        label: r.month,
        metric: 'objectif',
        value: r.target,
      })),
      ...users.map((u) => ({
        section: 'Utilisateurs',
        label: u.month,
        metric: 'actifs',
        value: u.active,
      })),
      ...users.map((u) => ({
        section: 'Utilisateurs',
        label: u.month,
        metric: 'nouveaux',
        value: u.new,
      })),
      ...churn.map((c) => ({
        section: 'Churn',
        label: c.month,
        metric: 'taux',
        value: c.rate,
      })),
      ...conversion.map((c) => ({
        section: 'Conversion',
        label: c.stage,
        metric: 'valeur',
        value: c.value,
      })),
    ],
    [revenue, users, churn, conversion],
  );

  const exportColumns: ExportColumn<(typeof exportRows)[number]>[] = [
    { header: 'Section', value: (r) => r.section },
    { header: 'Période / Étape', value: (r) => r.label },
    { header: 'Métrique', value: (r) => r.metric },
    { header: 'Valeur', value: (r) => r.value },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.analytics')}
        description="Analysez vos métriques et performances"
        actions={
          <>
            <div className="flex items-center rounded-lg border border-border bg-card p-0.5">
              {PERIODS.map((p) => (
                <Button key={p.id} variant={period === p.id ? 'default' : 'ghost'} size="sm" onClick={() => setPeriod(p.id)}>
                  {p.label}
                </Button>
              ))}
            </div>
            <ExportMenu
              filename={`analytics-${period}`}
              title={`Analytics AI BOS (${PERIODS.find((p) => p.id === period)?.label})`}
              sheetName="Analytics"
              columns={exportColumns}
              rows={exportRows}
            />
          </>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 xl:gap-5">
        {kpis.map((kpi, i) => (
          <KpiCard
            key={i}
            label={kpi.label}
            value={
              kpi.unit === '€'
                ? formatCurrency(kpi.value)
                : kpi.unit === '%'
                  ? formatPercent(kpi.value)
                  : formatNumber(kpi.value)
            }
            change={kpi.change}
            icon={kpi.change >= 0 ? TrendingUp : TrendingDown}
            trend={kpi.change >= 0 ? 'up' : 'down'}
          />
        ))}
      </div>

      <Card className="mt-6">
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="text-base">Revenu vs Objectif ({PERIODS.find((p) => p.id === period)?.label})</CardTitle>
          <Badge variant="success" className="gap-1">
            <TrendingUp className="h-3 w-3" />
            +12.5%
          </Badge>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={revenue} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4f46e5" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#4f46e5" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 12, fill: '#64748b' }}
                axisLine={false}
                tickLine={false}
                interval={0}
                padding={{ left: 8, right: 8 }}
              />
              <YAxis
                tick={{ fontSize: 12, fill: '#64748b' }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${v / 1000}k`}
              />
              <Tooltip
                contentStyle={{ borderRadius: '0.75rem', border: '1px solid #e2e8f0' }}
                formatter={(v) => formatCurrency(Number(v))}
              />
              <Legend />
              <Area type="monotone" dataKey="revenue" stroke="#4f46e5" strokeWidth={2.5} fill="url(#rev)" name="Revenu" />
              <Line type="monotone" dataKey="target" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" name="Objectif" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Utilisateurs</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={users}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #e2e8f0' }} />
                <Legend />
                <Bar dataKey="active" fill="#4f46e5" radius={[4, 4, 0, 0]} name="Actifs" />
                <Bar dataKey="new" fill="#0d9488" radius={[4, 4, 0, 0]} name="Nouveaux" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Tunnel de conversion</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={conversion} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="stage"
                  tick={{ fontSize: 12, fill: '#64748b' }}
                  axisLine={false}
                  tickLine={false}
                  width={70}
                />
                <Tooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #e2e8f0' }} />
                <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                  {conversion.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Taux de churn</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={churn}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fontSize: 12, fill: '#64748b' }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #e2e8f0' }} formatter={(v) => `${v}%`} />
              <Line type="monotone" dataKey="rate" stroke="#ef4444" strokeWidth={2.5} dot={{ fill: '#ef4444', r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
