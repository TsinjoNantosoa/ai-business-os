import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Palmtree, Search } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { getEmployees } from '@/lib/api/services';
import { useI18n } from '@/lib/i18n/store';
import { PageLoader } from '@/components/shared/PageLoader';

/**
 * Leaves view — Phase 1 access page backed by existing GET /hr/employees.
 * Filters employees currently on leave; mutations come in a later phase.
 */
export function HRLeavesPage() {
  const { t } = useI18n();
  const [search, setSearch] = useState('');
  const { data: employees, isLoading, isError, refetch } = useQuery({
    queryKey: ['employees'],
    queryFn: getEmployees,
  });

  const onLeave = useMemo(() => {
    const list = employees || [];
    return list.filter((e) => {
      const status = (e.status || '').toLowerCase();
      const matchesLeave = status === 'on_leave' || status === 'leave' || status.includes('leave');
      if (!matchesLeave) return false;
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      const name = `${e.firstName || ''} ${e.lastName || ''}`.toLowerCase();
      return name.includes(q) || (e.department || '').toLowerCase().includes(q) || (e.email || '').toLowerCase().includes(q);
    });
  }, [employees, search]);

  if (isLoading) return <PageLoader />;

  return (
    <div>
      <PageHeader
        title={t('nav.leaves')}
        description="Employés actuellement en congé (données RH live)"
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
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
