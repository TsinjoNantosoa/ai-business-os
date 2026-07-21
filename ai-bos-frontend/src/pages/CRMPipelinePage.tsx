import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Plus, Filter, Calendar, GripVertical } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { useI18n } from '@/lib/i18n/store';
import { useAuth } from '@/lib/auth/store';
import { createLead, getLeads, updateLeadStage } from '@/lib/api/services';
import type { Lead, LeadStage } from '@/lib/api/types';
import { cn, formatCurrency, initials } from '@/lib/utils';
import { toast } from 'sonner';

const STAGES: { id: LeadStage; label: string; color: string; bg: string }[] = [
  { id: 'new', label: 'Nouveaux', color: 'text-slate-600', bg: 'bg-slate-100' },
  { id: 'qualified', label: 'Qualifiés', color: 'text-blue-600', bg: 'bg-blue-100' },
  { id: 'proposal', label: 'Proposition', color: 'text-violet-600', bg: 'bg-violet-100' },
  { id: 'negotiation', label: 'Négociation', color: 'text-amber-600', bg: 'bg-amber-100' },
  { id: 'won', label: 'Gagnés', color: 'text-emerald-600', bg: 'bg-emerald-100' },
  { id: 'lost', label: 'Perdus', color: 'text-red-600', bg: 'bg-red-100' },
];

const emptyLeadForm = {
  title: '',
  company: '',
  contactName: '',
  value: '',
  expectedCloseDate: '',
  stage: 'new' as LeadStage,
};

export function CRMPipelinePage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('crm.lead.write');
  const queryClient = useQueryClient();
  const [ownerFilter, setOwnerFilter] = useState('all');
  const [draggedLead, setDraggedLead] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState(emptyLeadForm);

  const { data: leads, isLoading } = useQuery({
    queryKey: ['leads'],
    queryFn: getLeads,
  });

  const displayLeads = leads || [];
  const owners = Array.from(new Set(displayLeads.map((l) => l.ownerName).filter(Boolean)));
  const filteredLeads = displayLeads.filter((l) => ownerFilter === 'all' || l.ownerName === ownerFilter);

  const getLeadsByStage = (stage: LeadStage) => filteredLeads.filter((l) => l.stage === stage);
  const getStageValue = (stage: LeadStage) => getLeadsByStage(stage).reduce((sum, l) => sum + l.value, 0);

  const stageMutation = useMutation({
    mutationFn: ({ leadId, stage }: { leadId: string; stage: LeadStage }) => updateLeadStage(leadId, stage),
    onMutate: async ({ leadId, stage }) => {
      await queryClient.cancelQueries({ queryKey: ['leads'] });
      const previous = queryClient.getQueryData<Lead[]>(['leads']);
      queryClient.setQueryData<Lead[]>(['leads'], (old) =>
        (old || []).map((l) => (l.id === leadId ? { ...l, stage, daysInStage: 0 } : l)),
      );
      return { previous };
    },
    onError: (err: Error, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['leads'], context.previous);
      }
      toast.error(err.message || 'Impossible de déplacer le lead');
    },
    onSuccess: (updated) => {
      const label = STAGES.find((s) => s.id === updated.stage)?.label || updated.stage;
      toast.success(`Lead déplacé → ${label}`);
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['leads'] });
    },
  });

  const createMutation = useMutation({
    mutationFn: createLead,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['leads'] });
      setCreateOpen(false);
      setForm(emptyLeadForm);
      toast.success('Lead créé');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer le lead'),
  });

  useEffect(() => {
    if (!createOpen) return;
    const d = new Date();
    d.setDate(d.getDate() + 30);
    setForm((prev) => ({
      ...prev,
      expectedCloseDate: prev.expectedCloseDate || d.toISOString().slice(0, 10),
    }));
  }, [createOpen]);

  const handleDrop = (stage: LeadStage) => {
    if (!draggedLead || !canWrite) {
      setDraggedLead(null);
      return;
    }
    const lead = displayLeads.find((l) => l.id === draggedLead);
    if (!lead || lead.stage === stage) {
      setDraggedLead(null);
      return;
    }
    stageMutation.mutate({ leadId: draggedLead, stage });
    setDraggedLead(null);
  };

  return (
    <div>
      <PageHeader
        title={t('nav.crmPipeline')}
        description="Suivez vos opportunités commerciales"
        actions={
          <>
            <Select value={ownerFilter} onValueChange={setOwnerFilter}>
              <SelectTrigger className="w-40">
                <Filter className="h-4 w-4 mr-1" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('common.all')}</SelectItem>
                {owners.map((o) => (
                  <SelectItem key={o} value={o}>
                    {o}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {canWrite && (
              <Button
                onClick={() => {
                  setForm(emptyLeadForm);
                  setCreateOpen(true);
                }}
              >
                <Plus className="h-4 w-4" />
                {t('common.create')}
              </Button>
            )}
          </>
        }
      />

      <Card className="mb-4">
        <CardContent className="flex flex-wrap items-center gap-4 p-4">
          {STAGES.map((stage) => {
            const count = getLeadsByStage(stage.id).length;
            const value = getStageValue(stage.id);
            return (
              <div key={stage.id} className="flex items-center gap-2">
                <div className={cn('h-2.5 w-2.5 rounded-full', stage.bg)} />
                <div>
                  <p className="text-xs text-muted-foreground">{stage.label}</p>
                  <p className="text-sm font-semibold">
                    {count} • {formatCurrency(value)}
                  </p>
                </div>
              </div>
            );
          })}
          <div className="ml-auto text-right">
            <p className="text-xs text-muted-foreground">Total pipeline</p>
            <p className="text-lg font-bold text-primary">
              {formatCurrency(
                filteredLeads.filter((l) => l.stage !== 'won' && l.stage !== 'lost').reduce((s, l) => s + l.value, 0),
              )}
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-4 overflow-x-auto scrollbar-thin pb-4">
        {STAGES.map((stage) => {
          const stageLeads = getLeadsByStage(stage.id);
          return (
            <div
              key={stage.id}
              className="w-72 shrink-0"
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => handleDrop(stage.id)}
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={cn('h-2.5 w-2.5 rounded-full', stage.bg)} />
                  <h3 className="text-sm font-semibold">{stage.label}</h3>
                  <span className="text-xs text-muted-foreground">{stageLeads.length}</span>
                </div>
                <span className="text-xs font-medium text-muted-foreground">{formatCurrency(getStageValue(stage.id))}</span>
              </div>

              <div
                className="min-h-[200px] space-y-2 rounded-xl border border-dashed border-border bg-muted/20 p-2 transition-colors"
                onDragOver={(e) => {
                  e.preventDefault();
                  e.currentTarget.classList.add('bg-primary/5');
                }}
                onDragLeave={(e) => e.currentTarget.classList.remove('bg-primary/5')}
                onDrop={(e) => {
                  e.currentTarget.classList.remove('bg-primary/5');
                  handleDrop(stage.id);
                }}
              >
                {isLoading ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-28 animate-pulse rounded-lg bg-muted" />
                    ))}
                  </div>
                ) : (
                  stageLeads.map((lead) => (
                    <motion.div
                      key={lead.id}
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      draggable={canWrite}
                      onDragStart={() => canWrite && setDraggedLead(lead.id)}
                      onDragEnd={() => setDraggedLead(null)}
                      className={cn(
                        'group rounded-lg border border-border bg-card p-3 shadow-soft transition-all hover:shadow-elevated',
                        canWrite ? 'cursor-grab active:cursor-grabbing' : 'cursor-default',
                        draggedLead === lead.id && 'opacity-50',
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium">{lead.title}</p>
                          <p className="truncate text-xs text-muted-foreground">{lead.company}</p>
                        </div>
                        {canWrite && <GripVertical className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100" />}
                      </div>

                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-sm font-bold text-primary">{formatCurrency(lead.value)}</span>
                        <Badge variant="muted" className="text-2xs">
                          {lead.probability}%
                        </Badge>
                      </div>

                      <div className="mt-3 flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <Avatar className="h-6 w-6" style={{ backgroundColor: `${lead.ownerAvatarColor}20` }}>
                            <AvatarFallback
                              style={{ color: lead.ownerAvatarColor, backgroundColor: 'transparent' }}
                              className="text-2xs"
                            >
                              {initials(lead.ownerName)}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-xs text-muted-foreground">{lead.ownerName.split(' ')[0]}</span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {lead.daysInStage}j
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}

                {stageLeads.length === 0 && !isLoading && (
                  <div className="flex h-24 items-center justify-center text-xs text-muted-foreground">Glissez les deals ici</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nouveau lead</DialogTitle>
            <DialogDescription>Ajoutez une opportunité au pipeline</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-2">
            <div className="col-span-2 space-y-2">
              <Label htmlFor="lead-title">Titre</Label>
              <Input
                id="lead-title"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Deal Acme — Enterprise"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lead-company">Entreprise</Label>
              <Input id="lead-company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lead-contact">Contact</Label>
              <Input
                id="lead-contact"
                value={form.contactName}
                onChange={(e) => setForm({ ...form, contactName: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lead-value">Valeur (€)</Label>
              <Input
                id="lead-value"
                type="number"
                min={0}
                value={form.value}
                onChange={(e) => setForm({ ...form, value: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lead-close">Clôture prévue</Label>
              <Input
                id="lead-close"
                type="date"
                value={form.expectedCloseDate}
                onChange={(e) => setForm({ ...form, expectedCloseDate: e.target.value })}
              />
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Étape</Label>
              <Select value={form.stage} onValueChange={(v) => setForm({ ...form, stage: v as LeadStage })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STAGES.filter((s) => s.id !== 'won' && s.id !== 'lost').map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              disabled={
                createMutation.isPending ||
                !form.title ||
                !form.company ||
                !form.contactName ||
                !form.value ||
                !form.expectedCloseDate
              }
              onClick={() =>
                createMutation.mutate({
                  title: form.title,
                  company: form.company,
                  contactName: form.contactName,
                  value: Number(form.value),
                  stage: form.stage,
                  expectedCloseDate: new Date(form.expectedCloseDate).toISOString(),
                })
              }
            >
              {createMutation.isPending ? 'Enregistrement…' : t('common.save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
