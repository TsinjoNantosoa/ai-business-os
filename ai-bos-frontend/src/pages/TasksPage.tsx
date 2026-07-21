import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Plus, List, Columns3, Calendar } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { createTask, getTasks, updateTaskStatus } from '@/lib/api/services';
import type { TaskStatus } from '@/lib/api/types';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { cn, formatDate, initials } from '@/lib/utils';
import { toast } from 'sonner';

const COLUMNS: { id: TaskStatus; label: string; color: string; bg: string }[] = [
  { id: 'todo', label: 'À faire', color: 'text-slate-600', bg: 'bg-slate-100' },
  { id: 'in_progress', label: 'En cours', color: 'text-blue-600', bg: 'bg-blue-100' },
  { id: 'review', label: 'Revue', color: 'text-amber-600', bg: 'bg-amber-100' },
  { id: 'done', label: 'Terminé', color: 'text-emerald-600', bg: 'bg-emerald-100' },
];

const PRIORITY_COLORS: Record<string, string> = {
  urgent: 'bg-red-500', high: 'bg-amber-500', medium: 'bg-blue-500', low: 'bg-slate-400',
};

export function TasksPage() {
  const { t } = useI18n();
  const { user, hasPermission } = useAuth();
  const canWrite = hasPermission('task.write');
  const queryClient = useQueryClient();
  const [view, setView] = useState<'kanban' | 'list'>('kanban');
  const [draggedTask, setDraggedTask] = useState<string | null>(null);
  const [myTasksOnly, setMyTasksOnly] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [dueDate, setDueDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    return d.toISOString().slice(0, 10);
  });

  const { data: tasks } = useQuery({ queryKey: ['tasks'], queryFn: getTasks });

  const statusMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: TaskStatus }) =>
      updateTaskStatus(taskId, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const createMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setCreateOpen(false);
      setTitle('');
      setDescription('');
      setPriority('medium');
      toast.success('Tâche créée');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer la tâche'),
  });

  const displayTasks = tasks || [];
  const filtered = myTasksOnly && user
    ? displayTasks.filter((task) => task.assigneeId === user.id)
    : displayTasks;

  const getTasksByStatus = (status: TaskStatus) => filtered.filter((task) => task.status === status);

  const handleDrop = (status: TaskStatus) => {
    if (!draggedTask || !canWrite) return;
    const task = displayTasks.find((item) => item.id === draggedTask);
    if (task && task.status !== status) {
      statusMutation.mutate({ taskId: draggedTask, status });
    }
    setDraggedTask(null);
  };

  return (
    <div>
      <PageHeader
        title={t('nav.tasks')}
        description="Gérez vos tâches et suivez leur progression"
        actions={
          <>
            <div className="flex items-center rounded-lg border border-border bg-card p-0.5">
              <Button variant={view === 'kanban' ? 'default' : 'ghost'} size="icon-sm" onClick={() => setView('kanban')}>
                <Columns3 className="h-4 w-4" />
              </Button>
              <Button variant={view === 'list' ? 'default' : 'ghost'} size="icon-sm" onClick={() => setView('list')}>
                <List className="h-4 w-4" />
              </Button>
            </div>
            <Button variant="outline" onClick={() => setMyTasksOnly(!myTasksOnly)}>
              {myTasksOnly ? 'Toutes les tâches' : 'Mes tâches'}
            </Button>
            {canWrite && (
              <Button onClick={() => setCreateOpen(true)}>
                <Plus className="h-4 w-4" />
                {t('common.create')}
              </Button>
            )}
          </>
        }
      />

      {view === 'kanban' ? (
        <div className="flex gap-4 overflow-x-auto scrollbar-thin pb-4">
          {COLUMNS.map((col) => {
            const colTasks = getTasksByStatus(col.id);
            return (
              <div
                key={col.id}
                className="w-72 shrink-0"
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => handleDrop(col.id)}
              >
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={cn('h-2.5 w-2.5 rounded-full', col.bg)} />
                    <h3 className="text-sm font-semibold">{col.label}</h3>
                    <span className="text-xs text-muted-foreground">{colTasks.length}</span>
                  </div>
                </div>
                <div className="min-h-[200px] space-y-2 rounded-xl border border-dashed border-border bg-muted/20 p-2">
                  {colTasks.map((task) => (
                    <motion.div
                      key={task.id}
                      layout
                      draggable={canWrite}
                      onDragStart={() => canWrite && setDraggedTask(task.id)}
                      onDragEnd={() => setDraggedTask(null)}
                      className={cn(
                        'rounded-lg border border-border bg-card p-3 shadow-soft transition-all hover:shadow-elevated',
                        canWrite ? 'cursor-grab active:cursor-grabbing' : 'cursor-default',
                        draggedTask === task.id && 'opacity-50',
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <p className="flex-1 text-sm font-medium">{task.title}</p>
                        <div className={cn('mt-1.5 h-2 w-2 shrink-0 rounded-full', PRIORITY_COLORS[task.priority])} />
                      </div>
                      <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">{task.projectName}</p>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {task.tags.map((tag) => (
                          <Badge key={tag} variant="muted" className="text-2xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      <div className="mt-3 flex items-center justify-between">
                        <Avatar className="h-6 w-6" style={{ backgroundColor: `${task.assigneeAvatarColor}20` }}>
                          <AvatarFallback
                            style={{ color: task.assigneeAvatarColor, backgroundColor: 'transparent' }}
                            className="text-2xs"
                          >
                            {initials(task.assigneeName)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {formatDate(task.dueDate)}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  {colTasks.length === 0 && (
                    <div className="flex h-24 items-center justify-center text-xs text-muted-foreground">
                      Glissez les tâches ici
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tâche</TableHead>
                  <TableHead>Projet</TableHead>
                  <TableHead>Priorité</TableHead>
                  <TableHead>{t('common.status')}</TableHead>
                  <TableHead>Assigné à</TableHead>
                  <TableHead>Échéance</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell className="font-medium">{task.title}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{task.projectName}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <div className={cn('h-2 w-2 rounded-full', PRIORITY_COLORS[task.priority])} />
                        <span className="text-sm capitalize">{task.priority}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={task.status} />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Avatar className="h-6 w-6" style={{ backgroundColor: `${task.assigneeAvatarColor}20` }}>
                          <AvatarFallback
                            style={{ color: task.assigneeAvatarColor, backgroundColor: 'transparent' }}
                            className="text-2xs"
                          >
                            {initials(task.assigneeName)}
                          </AvatarFallback>
                        </Avatar>
                        <span className="text-sm">{task.assigneeName}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatDate(task.dueDate)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nouvelle tâche</DialogTitle>
            <DialogDescription>Créer une tâche assignée à vous par défaut</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="task-title">Titre</Label>
              <Input id="task-title" value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="task-desc">Description</Label>
              <Textarea id="task-desc" value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Priorité</Label>
                <Select value={priority} onValueChange={setPriority}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="urgent">Urgent</SelectItem>
                    <SelectItem value="high">Haute</SelectItem>
                    <SelectItem value="medium">Moyenne</SelectItem>
                    <SelectItem value="low">Basse</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="task-due">Échéance</Label>
                <Input id="task-due" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              disabled={createMutation.isPending || !title.trim() || !dueDate}
              onClick={() =>
                createMutation.mutate({
                  title: title.trim(),
                  description: description.trim() || undefined,
                  priority,
                  dueDate: new Date(dueDate).toISOString(),
                  assigneeId: user?.id,
                  assigneeName: user ? `${user.firstName} ${user.lastName}` : undefined,
                })
              }
            >
              {createMutation.isPending ? 'Création…' : t('common.save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
