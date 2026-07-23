import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Mail, Phone, MapPin, Briefcase, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { createEmployee, getEmployees } from '@/lib/api/services';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { initials, formatDate } from '@/lib/utils';
import { toast } from 'sonner';
import type { Employee } from '@/lib/api/types';

export function HREmployeesPage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('hr.employee.write');
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [position, setPosition] = useState('');
  const [department, setDepartment] = useState('');
  const [location, setLocation] = useState('');
  const [salary, setSalary] = useState('');
  const { data: employees } = useQuery({ queryKey: ['employees'], queryFn: getEmployees });

  const filtered = (employees || []).filter(
    (e) =>
      !search ||
      `${e.firstName} ${e.lastName}`.toLowerCase().includes(search.toLowerCase()) ||
      e.department.toLowerCase().includes(search.toLowerCase()) ||
      e.position.toLowerCase().includes(search.toLowerCase()),
  );

  const resetForm = () => {
    setFirstName('');
    setLastName('');
    setEmail('');
    setPosition('');
    setDepartment('');
    setLocation('');
    setSalary('');
  };

  const createMutation = useMutation({
    mutationFn: createEmployee,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['employees'] });
      setCreateOpen(false);
      resetForm();
      toast.success('Employé créé');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer l’employé'),
  });

  const handleCreate = () => {
    createMutation.mutate({
      firstName: firstName.trim(),
      lastName: lastName.trim(),
      email: email.trim(),
      position: position.trim(),
      department: department.trim(),
      location: location.trim() || undefined,
      salary: salary ? Number(salary) : undefined,
    });
  };

  const canSubmit =
    firstName.trim() && lastName.trim() && email.trim() && position.trim() && department.trim();

  return (
    <div>
      <PageHeader
        title={t('nav.employees')}
        description="Annuaire des employés et organigramme"
        actions={
          canWrite ? (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              Nouvel employé
            </Button>
          ) : undefined
        }
      />

      <Tabs defaultValue="directory">
        <TabsList>
          <TabsTrigger value="directory">Annuaire</TabsTrigger>
          <TabsTrigger value="orgchart">Organigramme</TabsTrigger>
        </TabsList>

        <TabsContent value="directory">
          <div className="mb-4 relative max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Rechercher un employé..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filtered.map((emp) => (
              <Card key={emp.id} className="transition-all hover:shadow-elevated">
                <CardContent className="p-5">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-12 w-12" style={{ backgroundColor: `${emp.avatarColor}20` }}>
                      <AvatarFallback
                        style={{ color: emp.avatarColor, backgroundColor: 'transparent' }}
                        className="text-sm font-medium"
                      >
                        {initials(`${emp.firstName} ${emp.lastName}`)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold truncate">
                        {emp.firstName} {emp.lastName}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">{emp.position}</p>
                    </div>
                    <StatusBadge status={emp.status} />
                  </div>
                  <div className="mt-4 space-y-1.5 text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Briefcase className="h-3.5 w-3.5" />
                      {emp.department}
                    </div>
                    <div className="flex items-center gap-2">
                      <Mail className="h-3.5 w-3.5" />
                      {emp.email}
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="h-3.5 w-3.5" />
                      {emp.location}
                    </div>
                    <div className="flex items-center gap-2">
                      <Phone className="h-3.5 w-3.5" />
                      {emp.phone}
                    </div>
                  </div>
                  <div className="mt-3 border-t border-border pt-2 text-xs text-muted-foreground">
                    Entré le {formatDate(emp.startDate)}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="orgchart">
          <Card>
            <CardContent className="p-6">
              <OrgChart employees={employees || []} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nouvel employé</DialogTitle>
            <DialogDescription>Créer une fiche RH dans l’annuaire.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-3 py-2 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Prénom</Label>
              <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Nom</Label>
              <Input value={lastName} onChange={(e) => setLastName(e.target.value)} />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label>Email</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Poste</Label>
              <Input value={position} onChange={(e) => setPosition(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Département</Label>
              <Input value={department} onChange={(e) => setDepartment(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Lieu</Label>
              <Input value={location} onChange={(e) => setLocation(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Salaire brut</Label>
              <Input type="number" min={0} value={salary} onChange={(e) => setSalary(e.target.value)} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Annuler
            </Button>
            <Button disabled={!canSubmit || createMutation.isPending} onClick={handleCreate}>
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Créer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function OrgChart({ employees }: { employees: Employee[] }) {
  const ceo = employees.find((e) => !e.managerId);
  if (!ceo) return <p className="text-sm text-muted-foreground">Aucune donnée d&apos;organigramme</p>;

  const getReports = (managerId: string) => employees.filter((e) => e.managerId === managerId);

  const renderNode = (emp: Employee, level = 0) => {
    const reports = getReports(emp.id);
    return (
      <div key={emp.id} className="flex flex-col items-center">
        <div className="rounded-lg border border-border bg-card px-4 py-2 text-center shadow-sm">
          <p className="text-sm font-semibold">
            {emp.firstName} {emp.lastName}
          </p>
          <p className="text-xs text-muted-foreground">{emp.position}</p>
        </div>
        {reports.length > 0 && (
          <div className="mt-4 flex flex-wrap justify-center gap-6" style={{ marginLeft: level * 8 }}>
            {reports.map((r) => renderNode(r, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return <div className="overflow-x-auto py-4">{renderNode(ceo)}</div>;
}
