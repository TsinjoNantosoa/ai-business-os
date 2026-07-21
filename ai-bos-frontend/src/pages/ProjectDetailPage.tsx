import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Calendar, CheckCircle2, DollarSign } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { getProjects } from '@/lib/api/services';
import { formatCurrency, formatDate, initials } from '@/lib/utils';

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { data: projects, isLoading } = useQuery({ queryKey: ['projects'], queryFn: getProjects });
  const project = (projects || []).find((p) => p.id === projectId);

  if (isLoading) {
    return (
      <div>
        <PageHeader title="Projet" description="Chargement…" />
        <div className="h-64 animate-pulse rounded-xl bg-muted" />
      </div>
    );
  }

  if (!project) {
    return (
      <div>
        <Button variant="ghost" className="mb-4" onClick={() => navigate('/app/projects')}>
          <ArrowLeft className="h-4 w-4" /> Retour aux projets
        </Button>
        <EmptyState
          icon={CheckCircle2}
          title="Projet introuvable"
          description="Ce projet n’existe pas ou n’est plus accessible."
        />
      </div>
    );
  }

  const budgetPct = project.budget > 0 ? Math.min(100, Math.round((project.spent / project.budget) * 100)) : 0;

  return (
    <div>
      <Button variant="ghost" className="mb-2" onClick={() => navigate('/app/projects')}>
        <ArrowLeft className="h-4 w-4" /> Retour
      </Button>
      <PageHeader
        title={project.name}
        description={project.description}
        actions={<StatusBadge status={project.status} />}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Avancement</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="mb-1.5 flex justify-between text-sm">
                <span className="text-muted-foreground">Progression</span>
                <span className="font-medium">{project.progress}%</span>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full" style={{ width: `${project.progress}%`, backgroundColor: project.color }} />
              </div>
            </div>
            <div>
              <div className="mb-1.5 flex justify-between text-sm">
                <span className="text-muted-foreground">Budget consommé</span>
                <span className="font-medium">
                  {formatCurrency(project.spent)} / {formatCurrency(project.budget)} ({budgetPct}%)
                </span>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full bg-amber-500" style={{ width: `${budgetPct}%` }} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 border-t border-border pt-4 text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Calendar className="h-4 w-4" />
                Début {formatDate(project.startDate)}
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Calendar className="h-4 w-4" />
                Fin {formatDate(project.endDate)}
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                {project.completedTasks}/{project.taskCount} tâches
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <DollarSign className="h-4 w-4" />
                {formatCurrency(project.budget - project.spent)} restant
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Équipe ({project.teamMembers.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {project.teamMembers.map((m) => (
              <div key={m.id} className="flex items-center gap-3">
                <Avatar className="h-9 w-9" style={{ backgroundColor: `${m.avatarColor}20` }}>
                  <AvatarFallback style={{ color: m.avatarColor, backgroundColor: 'transparent' }} className="text-xs">
                    {initials(m.name)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="text-sm font-medium">{m.name}</p>
                  <p className="text-xs text-muted-foreground">{m.role}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
