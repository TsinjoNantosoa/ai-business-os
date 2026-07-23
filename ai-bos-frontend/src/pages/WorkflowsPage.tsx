import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Play, Zap, Mail, Webhook, Database, Bot, CheckSquare,
  GitBranch, Clock, Activity, Settings, Pencil,
} from 'lucide-react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { WorkflowCanvas } from '@/components/workflows/WorkflowCanvas';
import {
  createWorkflow,
  getWorkflowExecutions,
  getWorkflows,
  runWorkflow,
  updateWorkflow,
} from '@/lib/api/services';
import type { Workflow, WorkflowStatus, WorkflowUpsertPayload } from '@/lib/api/types';
import { useI18n } from '@/lib/i18n/store';
import { formatRelativeTime } from '@/lib/utils';

const ACTION_ICONS: Record<string, React.ElementType> = {
  'Envoyer email': Mail,
  'Créer tâche': CheckSquare,
  'Notifier Slack': Zap,
  'Mettre à jour CRM': Database,
  'Run AI agent': Bot,
  'Call API': Webhook,
};

export function WorkflowsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState('list');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const { data: workflows } = useQuery({ queryKey: ['workflows'], queryFn: getWorkflows });
  const { data: executions } = useQuery({ queryKey: ['workflow-executions'], queryFn: getWorkflowExecutions });

  const editingWorkflow = useMemo(
    () => (editingId ? (workflows || []).find((wf) => wf.id === editingId) || null : null),
    [editingId, workflows],
  );

  const runMutation = useMutation({
    mutationFn: runWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflow-executions'] });
      toast.success('Workflow exécuté');
    },
    onError: (err: Error) => toast.error(err.message || 'Échec exécution'),
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: WorkflowUpsertPayload & { id?: string }) => {
      if (payload.id) {
        const { id, ...body } = payload;
        return updateWorkflow(id, body);
      }
      return createWorkflow(payload);
    },
    onSuccess: (wf) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      setEditingId(wf.id);
      setIsCreating(false);
      toast.success('Workflow enregistré');
    },
    onError: (err: Error) => toast.error(err.message || 'Échec enregistrement'),
  });

  const openCreate = () => {
    setIsCreating(true);
    setEditingId(null);
    setTab('builder');
  };

  const openEdit = (wf: Workflow) => {
    setIsCreating(false);
    setEditingId(wf.id);
    setTab('builder');
  };

  const handleSave = async (payload: {
    name: string
    description: string
    status: WorkflowStatus
    definition: NonNullable<Workflow['definition']>
  }) => {
    await saveMutation.mutateAsync({
      id: editingWorkflow?.id,
      name: payload.name,
      description: payload.description,
      status: payload.status,
      definition: payload.definition,
    });
  };

  return (
    <div>
      <PageHeader
        title={t('nav.workflows')}
        description="Automatisez vos processus métier — designer visuel S32"
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Nouveau workflow
          </Button>
        }
      />

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="list">Workflows</TabsTrigger>
          <TabsTrigger value="builder">Constructeur visuel</TabsTrigger>
          <TabsTrigger value="history">Historique</TabsTrigger>
        </TabsList>

        <TabsContent value="list">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {(workflows || []).map((wf) => (
              <Card key={wf.id} className="transition-all hover:shadow-elevated">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-sm font-semibold">{wf.name}</h3>
                      <p className="text-xs text-muted-foreground">{wf.description}</p>
                    </div>
                    <StatusBadge status={wf.status} />
                  </div>

                  <div className="mt-4 flex items-center gap-2 overflow-x-auto scrollbar-thin">
                    <div className="flex shrink-0 items-center gap-1.5 rounded-lg bg-amber-50 px-2.5 py-1.5 text-xs font-medium text-amber-700">
                      <Zap className="h-3.5 w-3.5" />
                      {wf.trigger}
                    </div>
                    <GitBranch className="h-3 w-3 shrink-0 text-muted-foreground" />
                    {wf.actions.map((action, i) => {
                      const Icon = ACTION_ICONS[action] || CheckSquare;
                      return (
                        <div
                          key={`${wf.id}-${action}-${i}`}
                          className="flex shrink-0 items-center gap-1.5 rounded-lg bg-primary-50 px-2.5 py-1.5 text-xs font-medium text-primary"
                        >
                          <Icon className="h-3.5 w-3.5" />
                          {action}
                        </div>
                      );
                    })}
                  </div>

                  <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Activity className="h-3 w-3" />
                        {wf.runCount} exécutions
                      </span>
                      <span className="flex items-center gap-1">
                        <CheckSquare className="h-3 w-3" />
                        {wf.successRate}% succès
                      </span>
                      {wf.lastRun && <span>{formatRelativeTime(wf.lastRun)}</span>}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon-sm" onClick={() => openEdit(wf)} title="Éditer">
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon-sm" onClick={() => openEdit(wf)} title="Paramètres">
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={wf.status === 'draft' || runMutation.isPending}
                        onClick={() => runMutation.mutate(wf.id)}
                      >
                        <Play className="h-3.5 w-3.5" />
                        Exécuter
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="builder">
          <Card>
            <CardContent className="p-6">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold">
                    {isCreating || !editingWorkflow ? 'Nouveau workflow' : `Édition · ${editingWorkflow.name}`}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Glissez les nœuds, ajoutez des actions, enregistrez puis activez pour exécuter.
                  </p>
                </div>
                {editingWorkflow && editingWorkflow.status !== 'draft' && (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={runMutation.isPending}
                    onClick={() => runMutation.mutate(editingWorkflow.id)}
                  >
                    <Play className="h-4 w-4" />
                    Exécuter
                  </Button>
                )}
              </div>
              <WorkflowCanvas
                key={editingWorkflow?.id || 'new'}
                workflow={isCreating ? null : editingWorkflow}
                saving={saveMutation.isPending}
                onSave={handleSave}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Workflow</TableHead>
                    <TableHead>Statut</TableHead>
                    <TableHead>Démarré</TableHead>
                    <TableHead>Durée</TableHead>
                    <TableHead>Résultat</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(executions || []).map((ex) => (
                    <TableRow key={ex.id}>
                      <TableCell className="font-medium">{ex.workflowName || ex.workflowId}</TableCell>
                      <TableCell>
                        <StatusBadge status={ex.status} />
                      </TableCell>
                      <TableCell className="text-muted-foreground">{formatRelativeTime(ex.startedAt)}</TableCell>
                      <TableCell>{ex.durationMs != null ? `${ex.durationMs} ms` : '—'}</TableCell>
                      <TableCell className="max-w-xs truncate text-xs text-muted-foreground">
                        {ex.resultMessage || ex.errorMessage || '—'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
