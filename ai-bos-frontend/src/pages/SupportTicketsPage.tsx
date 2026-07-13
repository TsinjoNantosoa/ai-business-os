import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Search, Clock, Send, Sparkles,
} from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Textarea } from '@/components/ui/textarea';
import { getTickets, replyToTicket } from '@/lib/api/services';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { cn, initials, formatRelativeTime } from '@/lib/utils';

const PRIORITY_COLORS: Record<string, string> = {
  urgent: 'bg-red-500', high: 'bg-amber-500', medium: 'bg-blue-500', low: 'bg-slate-400',
};

export function SupportTicketsPage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [reply, setReply] = useState('');
  const [isInternal, setIsInternal] = useState(false);
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

  const filtered = (tickets || []).filter((ticket) =>
    !search || ticket.subject.toLowerCase().includes(search.toLowerCase()) ||
    ticket.ticketNumber.toLowerCase().includes(search.toLowerCase()) ||
    ticket.customerName.toLowerCase().includes(search.toLowerCase())
  );

  const selected = (tickets || []).find((ticket) => ticket.id === selectedId) || filtered[0];
  const aiSuggestedReply = 'Bonjour,\n\nMerci pour votre message. J\'ai bien pris connaissance de votre problème et je travaille sur une résolution. Je vous tiendrai informé(e) des avancements.\n\nCordialement,\nL\'équipe support AI BOS';

  const handleSend = () => {
    if (!selected || !reply.trim() || replyMutation.isPending) return;
    replyMutation.mutate({ ticketId: selected.id, content: reply.trim(), internal: isInternal });
  };

  return (
    <div>
      <PageHeader
        title={t('nav.tickets')}
        description="Gérez les tickets de support client"
        actions={<Button><Plus className="h-4 w-4" />Nouveau ticket</Button>}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <div className="mb-3 relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Rechercher..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>
          <div className="space-y-2">
            {filtered.map((ticket) => (
              <Card
                key={ticket.id}
                className={cn('cursor-pointer transition-all hover:shadow-elevated', selected?.id === ticket.id && 'border-primary')}
                onClick={() => setSelectedId(ticket.id)}
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-2xs text-muted-foreground">{ticket.ticketNumber}</span>
                        <div className={cn('h-2 w-2 rounded-full', PRIORITY_COLORS[ticket.priority])} />
                      </div>
                      <p className="mt-0.5 text-sm font-medium truncate">{ticket.subject}</p>
                      <p className="text-xs text-muted-foreground truncate">{ticket.customerName}</p>
                    </div>
                    <StatusBadge status={ticket.status} />
                  </div>
                  <div className="mt-2 flex items-center justify-between text-2xs text-muted-foreground">
                    <span className="flex items-center gap-1"><Clock className="h-3 w-3" />SLA: {formatRelativeTime(ticket.slaDeadline)}</span>
                    <span>{ticket.category}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <div className="lg:col-span-3">
          {selected && (
            <Card className="flex flex-col h-[calc(100vh-14rem)]">
              <CardContent className="p-5 flex flex-col h-full">
                <div className="border-b border-border pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold">{selected.subject}</h3>
                      <p className="text-sm text-muted-foreground">{selected.ticketNumber} • {selected.customerName}</p>
                    </div>
                    <StatusBadge status={selected.status} />
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto scrollbar-thin py-4 space-y-3">
                  {selected.messages.map((msg) => (
                    <div key={msg.id} className={cn('flex gap-3', msg.author === 'Customer' && 'flex-row-reverse')}>
                      <Avatar className="h-8 w-8 shrink-0">
                        <AvatarFallback className={cn('text-2xs', msg.author === 'Customer' ? 'bg-muted' : 'bg-primary-100 text-primary-700')}>
                          {initials(msg.author === 'Customer' ? selected.customerName : msg.author)}
                        </AvatarFallback>
                      </Avatar>
                      <div className={cn(
                        'max-w-[70%] rounded-2xl px-4 py-2 text-sm',
                        msg.isInternal
                          ? 'bg-amber-50 border border-amber-200 text-amber-900'
                          : msg.author === 'Customer'
                            ? 'bg-muted'
                            : 'bg-primary text-primary-foreground'
                      )}>
                        {msg.isInternal && <p className="mb-1 text-2xs font-semibold uppercase">Note interne</p>}
                        {msg.content}
                        <p className={cn('mt-1 text-2xs', msg.author === 'Customer' || msg.isInternal ? 'text-muted-foreground' : 'text-primary-foreground/70')}>
                          {formatRelativeTime(msg.createdAt)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 rounded-xl border border-primary/20 bg-gradient-to-br from-primary-50/50 to-violet-50/30 p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="flex h-6 w-6 items-center justify-center rounded-lg gradient-ai">
                      <Sparkles className="h-3 w-3 text-white" />
                    </div>
                    <span className="text-xs font-semibold">Suggestion IA</span>
                  </div>
                  <p className="text-xs text-muted-foreground whitespace-pre-wrap">{aiSuggestedReply}</p>
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
                    <Button
                      variant={isInternal ? 'default' : 'outline'}
                      onClick={() => setIsInternal((value) => !value)}
                    >
                      Note interne
                    </Button>
                    <Button disabled={!reply.trim() || replyMutation.isPending} onClick={handleSend}>
                      <Send className="h-4 w-4" />Répondre
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
