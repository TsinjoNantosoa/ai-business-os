import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Clock, Send, Sparkles } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { createTicket, getTickets, replyToTicket } from '@/lib/api/services';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { cn, initials, formatRelativeTime } from '@/lib/utils';
import { toast } from 'sonner';

const PRIORITY_COLORS: Record<string, string> = {
  urgent: 'bg-red-500',
  high: 'bg-amber-500',
  medium: 'bg-blue-500',
  low: 'bg-slate-400',
};

export function SupportTicketsPage() {
  const { t } = useI18n();
  const { user, hasPermission } = useAuth();
  const canWrite = hasPermission('support.ticket.write');
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [reply, setReply] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [subject, setSubject] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [priority, setPriority] = useState('medium');
  const [category, setCategory] = useState('Support');
  const [message, setMessage] = useState('');
  const { data: tickets } = useQuery({ queryKey: ['tickets'], queryFn: getTickets });

  const replyMutation = useMutation({
    mutationFn: ({ ticketId, content, internal }: { ticketId: string; content: string; internal: boolean }) =>
      replyToTicket(ticketId, {
        content,
        isInternal: internal,
        author: user ? `${user.firstName} ${user.lastName}` : 'Support Agent',
      }),
    onSuccess: (ticket) => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      setSelectedId(ticket.id);
      setReply('');
      setIsInternal(false);
    },
  });

  const createMutation = useMutation({
    mutationFn: createTicket,
    onSuccess: (ticket) => {
      void queryClient.invalidateQueries({ queryKey: ['tickets'] });
      setCreateOpen(false);
      setSubject('');
      setCustomerName('');
      setCustomerEmail('');
      setPriority('medium');
      setCategory('Support');
      setMessage('');
      setSelectedId(ticket.id);
      toast.success(`Ticket ${ticket.ticketNumber} créé`);
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer le ticket'),
  });

  const filtered = (tickets || []).filter(
    (ticket) =>
      !search ||
      ticket.subject.toLowerCase().includes(search.toLowerCase()) ||
      ticket.ticketNumber.toLowerCase().includes(search.toLowerCase()) ||
      ticket.customerName.toLowerCase().includes(search.toLowerCase()),
  );

  const selected = (tickets || []).find((ticket) => ticket.id === selectedId) || filtered[0];
  const aiSuggestedReply =
    "Bonjour,\n\nMerci pour votre message. J'ai bien pris connaissance de votre problème et je travaille sur une résolution. Je vous tiendrai informé(e) des avancements.\n\nCordialement,\nL'équipe support AI BOS";

  const handleSend = () => {
    if (!selected || !reply.trim() || replyMutation.isPending) return;
    replyMutation.mutate({ ticketId: selected.id, content: reply.trim(), internal: isInternal });
  };

  return (
    <div>
      <PageHeader
        title={t('nav.tickets')}
        description="Gérez les tickets de support client"
        actions={
          canWrite ? (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              Nouveau ticket
            </Button>
          ) : undefined
        }
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <div className="relative mb-3">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Rechercher..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="space-y-2">
            {filtered.map((ticket) => (
              <Card
                key={ticket.id}
                className={cn(
                  'cursor-pointer transition-all hover:shadow-elevated',
                  selected?.id === ticket.id && 'border-primary',
                )}
                onClick={() => setSelectedId(ticket.id)}
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-2xs text-muted-foreground">{ticket.ticketNumber}</span>
                        <div className={cn('h-2 w-2 rounded-full', PRIORITY_COLORS[ticket.priority])} />
                      </div>
                      <p className="mt-0.5 truncate text-sm font-medium">{ticket.subject}</p>
                      <p className="truncate text-xs text-muted-foreground">{ticket.customerName}</p>
                    </div>
                    <StatusBadge status={ticket.status} />
                  </div>
                  <div className="mt-2 flex items-center justify-between text-2xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      SLA: {formatRelativeTime(ticket.slaDeadline)}
                    </span>
                    <span>{ticket.category}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <div className="lg:col-span-3">
          {selected && (
            <Card className="flex h-[calc(100vh-14rem)] flex-col">
              <CardContent className="flex h-full flex-col p-5">
                <div className="border-b border-border pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold">{selected.subject}</h3>
                      <p className="text-sm text-muted-foreground">
                        {selected.ticketNumber} • {selected.customerName}
                      </p>
                    </div>
                    <StatusBadge status={selected.status} />
                  </div>
                </div>

                <div className="flex-1 space-y-3 overflow-y-auto py-4 scrollbar-thin">
                  {selected.messages.map((msg) => (
                    <div key={msg.id} className={cn('flex gap-3', msg.author === 'Customer' && 'flex-row-reverse')}>
                      <Avatar className="h-8 w-8 shrink-0">
                        <AvatarFallback
                          className={cn(
                            'text-2xs',
                            msg.author === 'Customer' ? 'bg-muted' : 'bg-primary-100 text-primary-700',
                          )}
                        >
                          {initials(msg.author === 'Customer' ? selected.customerName : msg.author)}
                        </AvatarFallback>
                      </Avatar>
                      <div
                        className={cn(
                          'max-w-[70%] rounded-2xl px-4 py-2 text-sm',
                          msg.isInternal
                            ? 'border border-amber-200 bg-amber-50 text-amber-900'
                            : msg.author === 'Customer'
                              ? 'bg-muted'
                              : 'bg-primary text-primary-foreground',
                        )}
                      >
                        {msg.isInternal && (
                          <p className="mb-1 text-2xs font-semibold uppercase">Note interne</p>
                        )}
                        {msg.content}
                        <p
                          className={cn(
                            'mt-1 text-2xs',
                            msg.author === 'Customer' || msg.isInternal
                              ? 'text-muted-foreground'
                              : 'text-primary-foreground/70',
                          )}
                        >
                          {formatRelativeTime(msg.createdAt)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 rounded-xl border border-primary/20 bg-gradient-to-br from-primary-50/50 to-violet-50/30 p-3">
                  <div className="mb-1 flex items-center gap-2">
                    <div className="flex h-6 w-6 items-center justify-center rounded-lg gradient-ai">
                      <Sparkles className="h-3 w-3 text-white" />
                    </div>
                    <span className="text-xs font-semibold">Suggestion IA</span>
                  </div>
                  <p className="whitespace-pre-wrap text-xs text-muted-foreground">{aiSuggestedReply}</p>
                  <Button variant="outline" size="sm" className="mt-2 text-xs" onClick={() => setReply(aiSuggestedReply)}>
                    Utiliser cette suggestion
                  </Button>
                </div>

                <div className="border-t border-border pt-3">
                  <Textarea
                    placeholder="Écrivez votre réponse..."
                    value={reply}
                    onChange={(e) => setReply(e.target.value)}
                    rows={3}
                    className="mb-2"
                  />
                  <div className="flex justify-end gap-2">
                    <Button variant={isInternal ? 'default' : 'outline'} onClick={() => setIsInternal((v) => !v)}>
                      Note interne
                    </Button>
                    <Button disabled={!canWrite || !reply.trim() || replyMutation.isPending} onClick={handleSend}>
                      <Send className="h-4 w-4" />
                      Répondre
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nouveau ticket</DialogTitle>
            <DialogDescription>Ouvrir un ticket support pour un client</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label>Sujet</Label>
              <Input value={subject} onChange={(e) => setSubject(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Client</Label>
                <Input value={customerName} onChange={(e) => setCustomerName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input type="email" value={customerEmail} onChange={(e) => setCustomerEmail(e.target.value)} />
              </div>
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
                <Label>Catégorie</Label>
                <Input value={category} onChange={(e) => setCategory(e.target.value)} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Message initial</Label>
              <Textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={3} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              disabled={
                createMutation.isPending || !subject.trim() || !customerName.trim() || !customerEmail.trim()
              }
              onClick={() =>
                createMutation.mutate({
                  subject: subject.trim(),
                  customerName: customerName.trim(),
                  customerEmail: customerEmail.trim(),
                  priority,
                  category: category.trim() || 'Support',
                  message: message.trim() || undefined,
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
