import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Palmtree, Search, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { getEmployees, updateEmployee } from '@/lib/api/services';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { PageLoader } from '@/components/shared/PageLoader';
import { toast } from 'sonner';

export function HRLeavesPage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('hr.leave.write') || hasPermission('hr.employee.write');
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [leaveOpen, setLeaveOpen] = useState(false);
  const [employeeId, setEmployeeId] = useState('');

  const { data: employees, isLoading, isError, refetch } = useQuery({
    queryKey: ['employees'],
    queryFn: getEmployees,
  });

  const isOnLeave = (status: string | undefined) => {
    const s = (status || '').toLowerCase();
    return s === 'on_leave' || s === 'leave' || s.includes('leave');
  };

  const onLeave = useMemo(() => {
    const list = employees || [];
    return list.filter((e) => {
      if (!isOnLeave(e.status)) return false;
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      const name = `${e.firstName || ''} ${e.lastName || ''}`.toLowerCase();
      return name.includes(q) || (e.department || '').toLowerCase().includes(q) || (e.email || '').toLowerCase().includes(q);
    });
  }, [employees, search]);

  const activeEmployees = useMemo(
    () => (employees || []).filter((e) => (e.status || '').toLowerCase() === 'active'),
    [employees],
  );

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateEmployee(id, { status }),
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: ['employees'] });
      setLeaveOpen(false);
      setEmployeeId('');
      toast.success(vars.status === 'active' ? 'Retour enregistré' : 'Congé enregistré');
    },
    onError: (err: Error) => toast.error(err.message || 'Mise à jour impossible'),
  });

  if (isLoading) return <PageLoader />;

  return (
    <div>
      <PageHeader
        title={t('nav.leaves')}
        description="Employés actuellement en congé (données RH live)"
        actions={
          canWrite ? (
            <Button onClick={() => setLeaveOpen(true)}>
              Mettre en congé
            </Button>
          ) : undefined
        }
      />

      <div className="mb-4 relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Rechercher un collaborateur..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isError && (
        <Card className="mb-4 border-destructive/40">
          <CardContent className="flex items-center justify-between p-4 text-sm">
            <span>Impossible de charger les congés.</span>
            <button type="button" className="underline" onClick={() => void refetch()}>
              Réessayer
            </button>
          </CardContent>
        </Card>
      )}

      {onLeave.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Palmtree className="h-10 w-10 text-muted-foreground" />
            <p className="mt-3 text-sm text-muted-foreground">
              Aucun collaborateur en congé pour le moment.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {onLeave.map((emp) => (
            <Card key={emp.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium">
                      {emp.firstName} {emp.lastName}
                    </p>
                    <p className="text-xs text-muted-foreground">{emp.position || emp.email}</p>
                  </div>
                  <Badge variant="muted">{emp.status}</Badge>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">{emp.department}</p>
                {canWrite && (
                  <Button
                    className="mt-3"
                    size="sm"
                    variant="outline"
                    disabled={statusMutation.isPending}
                    onClick={() => statusMutation.mutate({ id: emp.id, status: 'active' })}
                  >
                    {statusMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Retour'}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={leaveOpen} onOpenChange={setLeaveOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Mettre en congé</DialogTitle>
            <DialogDescription>Sélectionnez un employé actif.</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Employé</Label>
            <Select value={employeeId} onValueChange={setEmployeeId}>
              <SelectTrigger>
                <SelectValue placeholder="Choisir…" />
              </SelectTrigger>
              <SelectContent>
                {activeEmployees.map((e) => (
                  <SelectItem key={e.id} value={e.id}>
                    {e.firstName} {e.lastName} — {e.department}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setLeaveOpen(false)}>Annuler</Button>
            <Button
              disabled={!employeeId || statusMutation.isPending}
              onClick={() => statusMutation.mutate({ id: employeeId, status: 'on_leave' })}
            >
              {statusMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Confirmer'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
