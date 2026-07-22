import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Video, MapPin, Clock, CheckCircle2, Circle, Sparkles, Mic, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { createMeeting, getMeetings } from '@/lib/api/services';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { cn, formatDate, initials } from '@/lib/utils';
import { toast } from 'sonner';

export function MeetingsPage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('meeting.write');
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [duration, setDuration] = useState('30');
  const [location, setLocation] = useState('');
  const [agendaText, setAgendaText] = useState('');
  const { data: meetings } = useQuery({ queryKey: ['meetings'], queryFn: getMeetings });

  const selected = (meetings || []).find((m) => m.id === selectedId) || (meetings || [])[0];

  const createMutation = useMutation({
    mutationFn: createMeeting,
    onSuccess: (meeting) => {
      void queryClient.invalidateQueries({ queryKey: ['meetings'] });
      setCreateOpen(false);
      setSelectedId(meeting.id);
      setTitle('');
      setLocation('');
      setAgendaText('');
      toast.success('Réunion créée');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer la réunion'),
  });

  const handleCreate = () => {
    const agenda = agendaText
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);
    createMutation.mutate({
      title: title.trim(),
      date,
      duration: Number(duration) || 30,
      location: location.trim() || undefined,
      agenda,
    });
  };

  return (
    <div>
      <PageHeader
        title={t('nav.meetings')}
        description="Vos réunions passées et à venir"
        actions={canWrite ? <Button onClick={() => setCreateOpen(true)}><Video className="h-4 w-4" />Nouvelle réunion</Button> : undefined}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Meeting list */}
        <div className="space-y-2">
          {(meetings || []).map((m) => (
            <Card
              key={m.id}
              className={cn('cursor-pointer transition-all hover:shadow-elevated', selected?.id === m.id && 'border-primary')}
              onClick={() => setSelectedId(m.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{m.title}</p>
                    <p className="text-xs text-muted-foreground">{formatDate(m.date)}</p>
                  </div>
                  <StatusBadge status={m.status} />
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <div className="flex -space-x-1.5">
                    {m.attendees.slice(0, 3).map((a, i) => (
                      <Avatar key={i} className="h-6 w-6 border-2 border-card" style={{ backgroundColor: `${a.avatarColor}20` }}>
                        <AvatarFallback style={{ color: a.avatarColor, backgroundColor: 'transparent' }} className="text-2xs">
                          {initials(a.name)}
                        </AvatarFallback>
                      </Avatar>
                    ))}
                  </div>
                  <span className="text-xs text-muted-foreground">{m.attendees.length} participants</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Meeting detail */}
        <div className="lg:col-span-2">
          {selected && (
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{selected.title}</CardTitle>
                    <div className="mt-2 flex items-center gap-3 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1"><Clock className="h-4 w-4" />{selected.duration} min</span>
                      <span className="flex items-center gap-1"><MapPin className="h-4 w-4" />{selected.location}</span>
                      <span>{formatDate(selected.date)}</span>
                    </div>
                  </div>
                  <Button variant="outline" size="sm"><Mic className="h-4 w-4" />Enregistrer</Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* Attendees */}
                <div>
                  <h4 className="mb-2 text-sm font-semibold">Participants</h4>
                  <div className="flex flex-wrap gap-2">
                    {selected.attendees.map((a, i) => (
                      <div key={i} className="flex items-center gap-2 rounded-lg border border-border p-2">
                        <Avatar className="h-7 w-7" style={{ backgroundColor: `${a.avatarColor}20` }}>
                          <AvatarFallback style={{ color: a.avatarColor, backgroundColor: 'transparent' }} className="text-2xs">
                            {initials(a.name)}
                          </AvatarFallback>
                        </Avatar>
                        <span className="text-sm">{a.name}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Agenda */}
                <div>
                  <h4 className="mb-2 text-sm font-semibold">Ordre du jour</h4>
                  <ul className="space-y-1.5">
                    {selected.agenda.map((item, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* AI Summary */}
                {selected.summary && (
                  <div className="rounded-xl border border-primary/20 bg-gradient-to-br from-primary-50/50 to-violet-50/30 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="flex h-7 w-7 items-center justify-center rounded-lg gradient-ai">
                        <Sparkles className="h-3.5 w-3.5 text-white" />
                      </div>
                      <h4 className="text-sm font-semibold">Résumé IA</h4>
                      <Badge variant="default" className="text-2xs">Auto-généré</Badge>
                    </div>
                    <p className="text-sm text-foreground leading-relaxed">{selected.summary}</p>
                  </div>
                )}

                {/* Action items */}
                {selected.actionItems.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-sm font-semibold">Actions à suivre</h4>
                    <div className="space-y-2">
                      {selected.actionItems.map((item) => (
                        <div key={item.id} className="flex items-center gap-2 rounded-lg border border-border p-2.5">
                          {item.done ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <Circle className="h-4 w-4 text-muted-foreground" />}
                          <span className={cn('text-sm flex-1', item.done && 'line-through text-muted-foreground')}>{item.text}</span>
                          <Badge variant="muted" className="text-2xs">{item.assignee}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Nouvelle réunion</DialogTitle>
            <DialogDescription>Vous serez ajouté comme participant.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="meeting-title">Titre</Label>
              <Input id="meeting-title" placeholder="Ex : Sync produit hebdo" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="meeting-date">Date</Label>
                <Input id="meeting-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="meeting-duration">Durée (min)</Label>
                <Input id="meeting-duration" type="number" min="5" max="600" step="5" value={duration} onChange={(e) => setDuration(e.target.value)} />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="meeting-location">Lieu (optionnel)</Label>
              <Input id="meeting-location" placeholder="Zoom, salle A…" value={location} onChange={(e) => setLocation(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="meeting-agenda">Ordre du jour (une ligne par point)</Label>
              <Textarea id="meeting-agenda" rows={3} placeholder={'Point 1\nPoint 2'} value={agendaText} onChange={(e) => setAgendaText(e.target.value)} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Annuler</Button>
            <Button onClick={handleCreate} disabled={!title.trim() || createMutation.isPending}>
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Créer la réunion'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
