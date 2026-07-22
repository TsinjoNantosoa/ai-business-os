import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Plus, Calendar, CheckCircle2, DollarSign, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { createProject, getProjects } from '@/lib/api/services';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { formatCurrency, formatDate, initials } from '@/lib/utils';
import { toast } from 'sonner';

const PROJECT_COLORS = ['#4f46e5', '#0d9488', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#ef4444', '#64748b'];

export function ProjectsPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('project.write');
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [budget, setBudget] = useState('');
  const [endDate, setEndDate] = useState('');
  const [color, setColor] = useState(PROJECT_COLORS[0]);
  const { data: projects, isLoading } = useQuery({ queryKey: ['projects'], queryFn: getProjects });

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['projects'] });
      setCreateOpen(false);
      setName('');
      setDescription('');
      setBudget('');
      setEndDate('');
      toast.success('Projet créé');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer le projet'),
  });

  const handleCreate = () => {
    createMutation.mutate({
      name: name.trim(),
      description: description.trim() || undefined,
      budget: budget ? Number(budget) : 0,
      endDate: endDate || undefined,
      color,
    });
  };

  return (
    <div>
      <PageHeader
        title={t('nav.projects')}
        description="Gérez vos projets et suivez leur avancement"
        actions={
          canWrite ? (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              {t('common.create')}
            </Button>
          ) : undefined
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {(projects || []).map((p) => (
          <Card key={p.id} className="group cursor-pointer transition-all hover:shadow-elevated" onClick={() => navigate(`/app/projects/${p.id}`)}>
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: p.color }} />
                  <h3 className="text-sm font-semibold truncate">{p.name}</h3>
                </div>
                <StatusBadge status={p.status} />
              </div>

              <p className="mt-2 text-xs text-muted-foreground line-clamp-2">{p.description}</p>

              <div className="mt-4">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Progression</span>
                  <span className="font-medium">{p.progress}%</span>
                </div>
                <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-muted">
                  <div className="h-full rounded-full transition-all" style={{ width: `${p.progress}%`, backgroundColor: p.color }} />
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <div className="flex -space-x-2">
                  {p.teamMembers.slice(0, 4).map((m, i) => (
                    <Avatar key={i} className="h-7 w-7 border-2 border-card" style={{ backgroundColor: `${m.avatarColor}20` }}>
                      <AvatarFallback style={{ color: m.avatarColor, backgroundColor: 'transparent' }} className="text-2xs">
                        {initials(m.name)}
                      </AvatarFallback>
                    </Avatar>
                  ))}
                  {p.teamMembers.length > 4 && (
                    <div className="flex h-7 w-7 items-center justify-center rounded-full border-2 border-card bg-muted text-2xs font-medium">
                      +{p.teamMembers.length - 4}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                  {p.completedTasks}/{p.taskCount}
                </div>
              </div>

              <div className="mt-3 flex items-center justify-between border-t border-border pt-3 text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  {formatDate(p.endDate)}
                </div>
                <div className="flex items-center gap-1">
                  <DollarSign className="h-3.5 w-3.5" />
                  {formatCurrency(p.spent)} / {formatCurrency(p.budget)}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        {isLoading && [1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-56 animate-pulse rounded-xl bg-muted" />
        ))}
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Créer un projet</DialogTitle>
            <DialogDescription>Le projet démarre en statut « planning ».</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="project-name">Nom</Label>
              <Input id="project-name" placeholder="Ex : Refonte site web" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-description">Description</Label>
              <Textarea id="project-description" rows={3} placeholder="Objectif du projet…" value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="project-budget">Budget (€)</Label>
                <Input id="project-budget" type="number" min="0" placeholder="50000" value={budget} onChange={(e) => setBudget(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="project-end">Échéance</Label>
                <Input id="project-end" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Couleur</Label>
              <div className="flex gap-2">
                {PROJECT_COLORS.map((c) => (
                  <button
                    key={c}
                    type="button"
                    className={`h-7 w-7 rounded-full border-2 transition-transform ${color === c ? 'scale-110 border-foreground' : 'border-transparent'}`}
                    style={{ backgroundColor: c }}
                    onClick={() => setColor(c)}
                  />
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Annuler</Button>
            <Button onClick={handleCreate} disabled={!name.trim() || createMutation.isPending}>
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Créer le projet'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
