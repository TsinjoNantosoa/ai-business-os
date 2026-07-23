import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Plus, Users, MapPin, Calendar, Award, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { createJobOpening, getJobOpenings, getCandidates } from '@/lib/api/services';
import type { Candidate } from '@/lib/api/types';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { cn, initials, formatDate } from '@/lib/utils';
import { toast } from 'sonner';

const STAGES: { id: Candidate['stage']; label: string; bg: string }[] = [
  { id: 'applied', label: 'Candidatures', bg: 'bg-slate-100' },
  { id: 'screening', label: 'Pré-sélection', bg: 'bg-blue-100' },
  { id: 'interview', label: 'Entretien', bg: 'bg-amber-100' },
  { id: 'offer', label: 'Offre', bg: 'bg-violet-100' },
  { id: 'hired', label: 'Recruté', bg: 'bg-emerald-100' },
];

export function RecruitmentPage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('hr.recruitment.write');
  const queryClient = useQueryClient();
  const { data: jobs } = useQuery({ queryKey: ['jobs'], queryFn: getJobOpenings });
  const { data: candidates } = useQuery({ queryKey: ['candidates'], queryFn: getCandidates });

  const [createOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('');
  const [location, setLocation] = useState('');
  const [type, setType] = useState('full_time');

  const reset = () => {
    setTitle('');
    setDepartment('');
    setLocation('');
    setType('full_time');
  };

  const createMutation = useMutation({
    mutationFn: createJobOpening,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['jobs'] });
      setCreateOpen(false);
      reset();
      toast.success('Offre créée');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer l\'offre'),
  });

  const canSubmit = title.trim() && department.trim() && location.trim();

  return (
    <div>
      <PageHeader
        title={t('nav.recruitment')}
        description="Gérez vos offres d'emploi et candidats"
        actions={
          canWrite ? (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              Nouvelle offre
            </Button>
          ) : undefined
        }
      />

      <Tabs defaultValue="jobs">
        <TabsList>
          <TabsTrigger value="jobs">Offres d'emploi</TabsTrigger>
          <TabsTrigger value="pipeline">Candidats</TabsTrigger>
        </TabsList>

        <TabsContent value="jobs">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(jobs || []).map((job) => (
              <Card key={job.id} className="transition-all hover:shadow-elevated">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-sm font-semibold">{job.title}</h3>
                      <p className="text-xs text-muted-foreground">{job.department}</p>
                    </div>
                    <StatusBadge status={job.status} />
                  </div>
                  <div className="mt-4 space-y-1.5 text-xs text-muted-foreground">
                    <div className="flex items-center gap-2"><MapPin className="h-3.5 w-3.5" />{job.location}</div>
                    <div className="flex items-center gap-2"><Calendar className="h-3.5 w-3.5" />Publiée le {formatDate(job.postedDate)}</div>
                    <div className="flex items-center gap-2"><Users className="h-3.5 w-3.5" />{job.applicants} candidats</div>
                  </div>
                  <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
                    <StatusBadge status={job.type} />
                    <Button variant="outline" size="sm">Voir candidats</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="pipeline">
          <div className="flex gap-4 overflow-x-auto scrollbar-thin pb-4">
            {STAGES.map((stage) => {
              const stageCandidates = (candidates || []).filter((c) => c.stage === stage.id);
              return (
                <div key={stage.id} className="w-72 shrink-0">
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={cn('h-2.5 w-2.5 rounded-full', stage.bg)} />
                      <h3 className="text-sm font-semibold">{stage.label}</h3>
                      <span className="text-xs text-muted-foreground">{stageCandidates.length}</span>
                    </div>
                  </div>
                  <div className="space-y-2 rounded-xl border border-dashed border-border bg-muted/20 p-2 min-h-[150px]">
                    {stageCandidates.map((c) => (
                      <motion.div
                        key={c.id}
                        layout
                        className="rounded-lg border border-border bg-card p-3 shadow-soft"
                      >
                        <div className="flex items-center gap-2">
                          <Avatar className="h-8 w-8" style={{ backgroundColor: `${c.avatarColor}20` }}>
                            <AvatarFallback style={{ color: c.avatarColor, backgroundColor: 'transparent' }} className="text-2xs">
                              {initials(c.name)}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{c.name}</p>
                            <p className="text-xs text-muted-foreground truncate">{c.jobTitle}</p>
                          </div>
                        </div>
                        <div className="mt-2 flex items-center justify-between">
                          <Badge variant={c.score >= 80 ? 'success' : c.score >= 60 ? 'warning' : 'muted'} className="text-2xs gap-1">
                            <Award className="h-2.5 w-2.5" />
                            Score: {c.score}
                          </Badge>
                          <span className="text-2xs text-muted-foreground">{formatDate(c.appliedAt)}</span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Nouvelle offre</DialogTitle>
            <DialogDescription>Créer une offre d&apos;emploi.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="job-title">Titre</Label>
              <Input id="job-title" placeholder="Ex : Développeur Full Stack" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
            </div>
            <div className="space-y-2">
              <Label htmlFor="job-department">Département</Label>
              <Input id="job-department" placeholder="Ex : Engineering" value={department} onChange={(e) => setDepartment(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="job-location">Lieu</Label>
              <Input id="job-location" placeholder="Ex : Paris / Remote" value={location} onChange={(e) => setLocation(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={type} onValueChange={setType}>
                <SelectTrigger>
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="full_time">Temps plein</SelectItem>
                  <SelectItem value="part_time">Temps partiel</SelectItem>
                  <SelectItem value="contract">Contrat</SelectItem>
                  <SelectItem value="internship">Stage</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Annuler</Button>
            <Button
              disabled={!canSubmit || createMutation.isPending}
              onClick={() =>
                createMutation.mutate({
                  title: title.trim(),
                  department: department.trim(),
                  location: location.trim(),
                  type,
                })
              }
            >
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Créer l\'offre'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
