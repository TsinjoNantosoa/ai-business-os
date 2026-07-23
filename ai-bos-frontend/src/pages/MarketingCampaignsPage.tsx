import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Mail, Megaphone, Users, MousePointerClick, Target,
  DollarSign, Eye, Calendar, Loader2,
} from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { createCampaign, getCampaigns } from '@/lib/api/services';
import type { Campaign } from '@/lib/api/types';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { cn, formatCurrency, formatNumber, formatPercent, formatDate } from '@/lib/utils';
import { toast } from 'sonner';

const CAMPAIGN_TYPES = [
  { value: 'email', label: 'Email' },
  { value: 'social', label: 'Réseaux sociaux' },
  { value: 'ads', label: 'Publicité (Ads)' },
  { value: 'webinar', label: 'Webinar' },
  { value: 'content', label: 'Contenu / SEO' },
  { value: 'sms', label: 'SMS' },
];

export function MarketingCampaignsPage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('marketing.campaign.write');
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [detail, setDetail] = useState<Campaign | null>(null);
  const [name, setName] = useState('');
  const [type, setType] = useState('email');
  const [budget, setBudget] = useState('');
  const [startDate, setStartDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState('');
  const { data: campaigns } = useQuery({ queryKey: ['campaigns'], queryFn: getCampaigns });

  const createMutation = useMutation({
    mutationFn: createCampaign,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setCreateOpen(false);
      setName('');
      setType('email');
      setBudget('');
      setEndDate('');
      toast.success('Campagne créée');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer la campagne'),
  });

  const handleCreate = () => {
    createMutation.mutate({
      name: name.trim(),
      type,
      budget: budget ? Number(budget) : 0,
      startDate,
      endDate: endDate || undefined,
    });
  };

  const totalReach = (campaigns || []).reduce((s, c) => s + c.reach, 0);
  const totalConversions = (campaigns || []).reduce((s, c) => s + c.conversions, 0);
  const totalBudget = (campaigns || []).reduce((s, c) => s + c.budget, 0);
  const spendPct = detail && detail.budget > 0 ? Math.min(100, Math.round((detail.spent / detail.budget) * 100)) : 0;

  return (
    <div>
      <PageHeader
        title={t('nav.marketing')}
        description="Gérez vos campagnes marketing"
        actions={canWrite ? <Button onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" />Nouvelle campagne</Button> : undefined}
      />

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card><CardContent className="p-4">
          <div className="flex items-center gap-2"><Users className="h-5 w-5 text-primary" /><p className="text-sm text-muted-foreground">Portée totale</p></div>
          <p className="mt-1 text-2xl font-bold">{formatNumber(totalReach)}</p>
        </CardContent></Card>
        <Card><CardContent className="p-4">
          <div className="flex items-center gap-2"><Target className="h-5 w-5 text-emerald-500" /><p className="text-sm text-muted-foreground">Conversions</p></div>
          <p className="mt-1 text-2xl font-bold">{formatNumber(totalConversions)}</p>
        </CardContent></Card>
        <Card><CardContent className="p-4">
          <div className="flex items-center gap-2"><DollarSign className="h-5 w-5 text-amber-500" /><p className="text-sm text-muted-foreground">Budget total</p></div>
          <p className="mt-1 text-2xl font-bold">{formatCurrency(totalBudget)}</p>
        </CardContent></Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {(campaigns || []).map((c) => (
          <Card key={c.id} className="flex flex-col transition-all hover:shadow-elevated">
            <CardContent className="flex flex-1 flex-col p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <div className={cn('flex h-10 w-10 shrink-0 items-center justify-center rounded-lg',
                    c.type === 'email' && 'bg-primary-50 text-primary',
                    c.type === 'social' && 'bg-pink-50 text-pink-600',
                    c.type === 'sms' && 'bg-emerald-50 text-emerald-600',
                    c.type === 'webinar' && 'bg-amber-50 text-amber-600',
                    (c.type === 'ads' || c.type === 'content') && 'bg-violet-50 text-violet-600',
                  )}>
                    {c.type === 'email' && <Mail className="h-5 w-5" />}
                    {c.type === 'social' && <Megaphone className="h-5 w-5" />}
                    {c.type === 'sms' && <Mail className="h-5 w-5" />}
                    {c.type === 'webinar' && <Users className="h-5 w-5" />}
                    {(c.type === 'ads' || c.type === 'content') && <Target className="h-5 w-5" />}
                  </div>
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-semibold">{c.name}</h3>
                    <p className="text-xs text-muted-foreground">
                      {CAMPAIGN_TYPES.find((t) => t.value === c.type)?.label || c.type}
                    </p>
                  </div>
                </div>
                <StatusBadge status={c.status} />
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-lg bg-muted/40 px-2.5 py-2">
                  <p className="flex items-center gap-1 text-[11px] font-medium text-slate-500"><Eye className="h-3 w-3" />Portée</p>
                  <p className="mt-0.5 text-sm font-semibold tabular-nums">{formatNumber(c.reach)}</p>
                </div>
                <div className="rounded-lg bg-muted/40 px-2.5 py-2">
                  <p className="flex items-center gap-1 text-[11px] font-medium text-slate-500"><Mail className="h-3 w-3" />Ouverture</p>
                  <p className="mt-0.5 text-sm font-semibold tabular-nums">{formatPercent(c.openRate)}</p>
                </div>
                <div className="rounded-lg bg-muted/40 px-2.5 py-2">
                  <p className="flex items-center gap-1 text-[11px] font-medium text-slate-500"><MousePointerClick className="h-3 w-3" />Clics</p>
                  <p className="mt-0.5 text-sm font-semibold tabular-nums">{formatPercent(c.clickRate)}</p>
                </div>
                <div className="rounded-lg bg-muted/40 px-2.5 py-2">
                  <p className="flex items-center gap-1 text-[11px] font-medium text-slate-500"><Target className="h-3 w-3" />Conv.</p>
                  <p className="mt-0.5 text-sm font-semibold tabular-nums">{c.conversions}</p>
                </div>
              </div>

              <div className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
                <div className="flex flex-col gap-1 text-xs text-muted-foreground sm:flex-row sm:items-center sm:gap-3">
                  <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{formatDate(c.startDate)}</span>
                  <span className="font-medium text-foreground/80">{formatCurrency(c.spent)} / {formatCurrency(c.budget)}</span>
                </div>
                <Button variant="outline" size="sm" className="shrink-0" onClick={() => setDetail(c)}>
                  Voir détails
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={!!detail} onOpenChange={(open) => !open && setDetail(null)}>
        <DialogContent className="max-w-lg">
          {detail && (
            <>
              <DialogHeader>
                <DialogTitle>{detail.name}</DialogTitle>
                <DialogDescription>
                  {CAMPAIGN_TYPES.find((t) => t.value === detail.type)?.label || detail.type}
                </DialogDescription>
                <div className="pt-1"><StatusBadge status={detail.status} /></div>
              </DialogHeader>
              <div className="space-y-4 py-1">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-lg bg-muted/40 p-3">
                    <p className="text-xs text-muted-foreground">Portée</p>
                    <p className="font-semibold">{formatNumber(detail.reach)}</p>
                  </div>
                  <div className="rounded-lg bg-muted/40 p-3">
                    <p className="text-xs text-muted-foreground">Conversions</p>
                    <p className="font-semibold">{formatNumber(detail.conversions)}</p>
                  </div>
                  <div className="rounded-lg bg-muted/40 p-3">
                    <p className="text-xs text-muted-foreground">Taux d&apos;ouverture</p>
                    <p className="font-semibold">{formatPercent(detail.openRate)}</p>
                  </div>
                  <div className="rounded-lg bg-muted/40 p-3">
                    <p className="text-xs text-muted-foreground">Taux de clic</p>
                    <p className="font-semibold">{formatPercent(detail.clickRate)}</p>
                  </div>
                </div>
                <div>
                  <div className="mb-1.5 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Budget consommé</span>
                    <span className="font-medium">{spendPct}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${spendPct}%` }} />
                  </div>
                  <p className="mt-1.5 text-xs text-muted-foreground">
                    {formatCurrency(detail.spent)} / {formatCurrency(detail.budget)}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Début</p>
                    <p className="font-medium">{formatDate(detail.startDate)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Fin</p>
                    <p className="font-medium">{detail.endDate ? formatDate(detail.endDate) : '—'}</p>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button onClick={() => setDetail(null)}>Fermer</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Créer une campagne</DialogTitle>
            <DialogDescription>La campagne est créée en brouillon.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="campaign-name">Nom</Label>
              <Input id="campaign-name" placeholder="Ex : Newsletter rentrée 2026" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Type</Label>
                <Select value={type} onValueChange={setType}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {CAMPAIGN_TYPES.map((option) => (
                      <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="campaign-budget">Budget (€)</Label>
                <Input id="campaign-budget" type="number" min="0" placeholder="5000" value={budget} onChange={(e) => setBudget(e.target.value)} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="campaign-start">Début</Label>
                <Input id="campaign-start" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="campaign-end">Fin (optionnel)</Label>
                <Input id="campaign-end" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Annuler</Button>
            <Button onClick={handleCreate} disabled={!name.trim() || createMutation.isPending}>
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Créer la campagne'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
