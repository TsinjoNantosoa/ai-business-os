import { useState, useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Plus, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { createEvent, getEvents } from '@/lib/api/services';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

const WEEKDAYS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
const MONTHS = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];

const EVENT_TYPES = [
  { value: 'meeting', label: 'Réunion', color: '#4f46e5' },
  { value: 'call', label: 'Appel', color: '#0d9488' },
  { value: 'deadline', label: 'Deadline', color: '#ef4444' },
  { value: 'reminder', label: 'Rappel', color: '#f59e0b' },
  { value: 'task', label: 'Tâche', color: '#8b5cf6' },
];

export function CalendarPage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('calendar.write');
  const queryClient = useQueryClient();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<'month' | 'week' | 'day'>('month');
  const [createOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [type, setType] = useState('meeting');
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('10:00');
  const [location, setLocation] = useState('');
  const { data: events } = useQuery({ queryKey: ['events'], queryFn: getEvents });

  const createMutation = useMutation({
    mutationFn: createEvent,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['events'] });
      setCreateOpen(false);
      setTitle('');
      setLocation('');
      toast.success('Événement créé');
    },
    onError: (err: Error) => toast.error(err.message || "Impossible de créer l'événement"),
  });

  const handleCreate = () => {
    const color = EVENT_TYPES.find((option) => option.value === type)?.color || '#4f46e5';
    createMutation.mutate({
      title: title.trim(),
      type,
      startDate: `${date}T${startTime}:00Z`,
      endDate: `${date}T${endTime}:00Z`,
      color,
      location: location.trim() || undefined,
    });
  };

  const days = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startOffset = (firstDay.getDay() + 6) % 7;
    const totalDays = lastDay.getDate();
    const daysArray: (Date | null)[] = [];
    for (let i = 0; i < startOffset; i++) daysArray.push(null);
    for (let i = 1; i <= totalDays; i++) daysArray.push(new Date(year, month, i));
    while (daysArray.length % 7 !== 0) daysArray.push(null);
    return daysArray;
  }, [currentDate]);

  const getEventsForDay = (date: Date) => {
    if (!events) return [];
    return events.filter((e) => {
      const eventDate = new Date(e.startDate);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  const prevMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  const nextMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  const today = new Date();

  const monthEvents = useMemo(() => {
    if (!events) return [];
    const y = currentDate.getFullYear();
    const m = currentDate.getMonth();
    return [...events]
      .filter((e) => {
        const d = new Date(e.startDate);
        return d.getFullYear() === y && d.getMonth() === m;
      })
      .sort((a, b) => new Date(a.startDate).getTime() - new Date(b.startDate).getTime());
  }, [events, currentDate]);

  return (
    <div className="min-w-0">
      <PageHeader
        title={t('nav.calendar')}
        description="Planifiez vos événements et réunions"
        actions={
          <>
            <div className="flex w-full items-center overflow-x-auto rounded-lg border border-border bg-card p-0.5 sm:w-auto">
              {(['month', 'week', 'day'] as const).map((v) => (
                <Button key={v} variant={view === v ? 'default' : 'ghost'} size="sm" onClick={() => setView(v)} className="shrink-0">
                  {v === 'month' ? 'Mois' : v === 'week' ? 'Semaine' : 'Jour'}
                </Button>
              ))}
            </div>
            {canWrite && (
              <Button onClick={() => setCreateOpen(true)} className="w-full sm:w-auto">
                <Plus className="h-4 w-4" />
                <span className="sm:inline">Nouvel événement</span>
              </Button>
            )}
          </>
        }
      />

      <Card>
        <CardContent className="p-3 sm:p-4">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-base font-semibold sm:text-lg">
              {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
            </h2>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setCurrentDate(new Date())}>
                Aujourd'hui
              </Button>
              <Button variant="outline" size="icon" onClick={prevMonth} aria-label="Mois précédent">
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" onClick={nextMonth} aria-label="Mois suivant">
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Mobile agenda */}
          <div className="space-y-2 md:hidden">
            {monthEvents.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">Aucun événement ce mois-ci</p>
            ) : (
              monthEvents.map((e) => {
                const start = new Date(e.startDate);
                return (
                  <div
                    key={e.id}
                    className="flex gap-3 rounded-xl border border-border bg-card p-3"
                  >
                    <div
                      className="w-1 shrink-0 rounded-full"
                      style={{ backgroundColor: e.color }}
                      aria-hidden
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{e.title}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {start.toLocaleDateString('fr-FR', {
                          weekday: 'short',
                          day: 'numeric',
                          month: 'short',
                        })}{' '}
                        ·{' '}
                        {start.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                        {e.location ? ` · ${e.location}` : ''}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Desktop / tablet month grid */}
          <div className="hidden overflow-x-auto md:block">
            <div className="grid min-w-[40rem] grid-cols-7 gap-1">
              {WEEKDAYS.map((d) => (
                <div key={d} className="pb-2 text-center text-xs font-medium text-muted-foreground">
                  {d}
                </div>
              ))}
              {days.map((date, i) => {
                if (!date) return <div key={i} className="min-h-[64px] rounded-lg lg:min-h-[80px]" />;
                const dayEvents = getEventsForDay(date);
                const isToday = date.toDateString() === today.toDateString();
                return (
                  <div
                    key={i}
                    className={cn(
                      'min-h-[64px] rounded-lg border p-1 transition-colors hover:bg-muted/30 lg:min-h-[80px] lg:p-1.5',
                      isToday ? 'border-primary bg-primary-50/30' : 'border-border',
                    )}
                  >
                    <span
                      className={cn(
                        'text-xs font-medium',
                        isToday ? 'text-primary' : 'text-muted-foreground',
                      )}
                    >
                      {date.getDate()}
                    </span>
                    <div className="mt-1 space-y-0.5">
                      {dayEvents.slice(0, 3).map((e) => (
                        <div
                          key={e.id}
                          className="flex items-center gap-1 truncate rounded px-1 py-0.5 text-2xs font-medium"
                          style={{ backgroundColor: `${e.color}15`, color: e.color }}
                        >
                          <div
                            className="h-1.5 w-1.5 shrink-0 rounded-full"
                            style={{ backgroundColor: e.color }}
                          />
                          {e.title}
                        </div>
                      ))}
                      {dayEvents.length > 3 && (
                        <p className="pl-1 text-2xs text-muted-foreground">
                          +{dayEvents.length - 3} autres
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Nouvel événement</DialogTitle>
            <DialogDescription>Ajoutez un événement au calendrier.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="event-title">Titre</Label>
              <Input
                id="event-title"
                placeholder="Ex : Réunion équipe produit"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                autoFocus
              />
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Type</Label>
                <Select value={type} onValueChange={setType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {EVENT_TYPES.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="event-date">Date</Label>
                <Input
                  id="event-date"
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </div>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="event-start">Début</Label>
                <Input
                  id="event-start"
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="event-end">Fin</Label>
                <Input
                  id="event-end"
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="event-location">Lieu (optionnel)</Label>
              <Input
                id="event-location"
                placeholder="Zoom, salle A…"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Annuler
            </Button>
            <Button onClick={handleCreate} disabled={!title.trim() || createMutation.isPending}>
              {createMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Créer l'événement"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
