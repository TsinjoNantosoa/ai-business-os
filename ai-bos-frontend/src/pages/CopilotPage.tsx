import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Send, Mic, Volume2, Plus, MessageSquare,
  TrendingUp, Wallet, Calendar, Zap, Bot, BookOpen, History, CheckCircle2, XCircle,
} from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { streamCopilotResponse, type CopilotApprovalEvent, type CopilotSource, type CopilotToolEvent } from '@/lib/api/services';
import { cn, initials } from '@/lib/utils';
import { ApprovalCard } from '@/components/copilot/ApprovalCard';
import { MarkdownContent } from '@/components/shared/MarkdownContent';
import { BrandLogo } from '@/components/brand/BrandLogo';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
  sources?: CopilotSource[];
  toolEvents?: CopilotToolEvent[];
  approval?: CopilotApprovalEvent;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
}

const AGENTS = [
  { id: 'ceo', name: 'CEO Agent', icon: Bot, color: 'bg-primary' },
  { id: 'sales', name: 'Sales Agent', icon: TrendingUp, color: 'bg-emerald-500' },
  { id: 'finance', name: 'Finance Agent', icon: Wallet, color: 'bg-amber-500' },
  { id: 'hr', name: 'HR Agent', icon: Bot, color: 'bg-pink-500' },
  { id: 'analyst', name: 'Data Analyst', icon: Zap, color: 'bg-violet-500' },
];

const SUGGESTED_PROMPTS = [
  { key: 'ai.daySummary', icon: Calendar, text: "Que dois-je surveiller aujourd'hui ?" },
  { key: 'ai.unpaidClients', icon: Wallet, text: 'Pourquoi ma trésorerie risque de baisser ?' },
  { key: 'ai.revenueForecast', icon: TrendingUp, text: 'Quels deals risquent de ne pas fermer ce mois-ci ?' },
];

export function CopilotPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [conversations] = useState<Conversation[]>([
    { id: '1', title: 'Analyse Q3 2024', messages: [], createdAt: new Date().toISOString() },
    { id: '2', title: 'Stratégie commerciale', messages: [], createdAt: new Date().toISOString() },
  ]);
  const [activeConvId, setActiveConvId] = useState('new');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(AGENTS[0]);
  const [isRecording, setIsRecording] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (promptText?: string) => {
    const text = promptText || input.trim();
    if (!text || isStreaming) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: text };
    const assistantId = crypto.randomUUID();
    const assistantMsg: Message = { id: assistantId, role: 'assistant', content: '', streaming: true, toolEvents: [] };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput('');
    setIsStreaming(true);

    try {
      for await (const event of streamCopilotResponse(text, selectedAgent.id, 'Copilot')) {
        if (event.type === 'chunk') {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + event.content } : m)),
          );
        } else if (event.type === 'tool_call' || event.type === 'tool_result') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, toolEvents: [...(m.toolEvents || []), event] }
                : m,
            ),
          );
        } else if (event.type === 'approval_required') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    approval: event,
                    content:
                      m.content ||
                      event.message ||
                      `Action « ${event.name} » en attente d'approbation.`,
                  }
                : m,
            ),
          );
        } else if (event.type === 'done') {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, sources: event.sources } : m)),
          );
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur Copilot';
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: m.content || `Désolé, une erreur est survenue : ${message}` }
            : m,
        ),
      );
    } finally {
      setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, streaming: false } : m)));
      setIsStreaming(false);
    }
  };

  const newChat = () => {
    setMessages([]);
    setActiveConvId('new');
  };

  return (
    <div className="flex h-[calc(100dvh-7.5rem)] min-h-[24rem] min-w-0 flex-col sm:h-[calc(100vh-8rem)]">
      <PageHeader
        title={t('ai.copilot')}
        description="Conversation complète avec votre assistant IA"
        actions={
          <div className="flex w-full gap-2 sm:w-auto">
            <Button variant="outline" className="flex-1 lg:hidden" onClick={() => setHistoryOpen(true)}>
              <History className="h-4 w-4" />
              Historique
            </Button>
            <Button className="flex-1 lg:hidden" onClick={newChat}>
              <Plus className="h-4 w-4" />
              {t('ai.newChat')}
            </Button>
          </div>
        }
      />

      <div className="flex min-h-0 flex-1 gap-4">
        {/* History sidebar — desktop */}
        <Card className="hidden w-64 shrink-0 flex-col lg:flex">
          <CardContent className="flex h-full flex-col p-3">
            <Button onClick={newChat} className="mb-3 w-full">
              <Plus className="h-4 w-4" />
              {t('ai.newChat')}
            </Button>
            <div className="flex-1 space-y-1 overflow-y-auto scrollbar-thin">
              <p className="px-2 py-1 text-2xs font-medium uppercase text-muted-foreground">Aujourd&apos;hui</p>
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  type="button"
                  onClick={() => setActiveConvId(conv.id)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm transition-colors',
                    activeConvId === conv.id ? 'bg-primary-10 text-primary' : 'hover:bg-muted',
                  )}
                >
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate">{conv.title}</span>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* History sheet — mobile */}
        <Sheet open={historyOpen} onOpenChange={setHistoryOpen}>
          <SheetContent side="left" className="flex w-[min(100vw,20rem)] flex-col p-0 sm:max-w-sm">
            <SheetHeader>
              <SheetTitle>Conversations</SheetTitle>
            </SheetHeader>
            <div className="flex flex-1 flex-col gap-2 overflow-y-auto p-4">
              <Button
                onClick={() => {
                  newChat();
                  setHistoryOpen(false);
                }}
                className="w-full"
              >
                <Plus className="h-4 w-4" />
                {t('ai.newChat')}
              </Button>
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  type="button"
                  onClick={() => {
                    setActiveConvId(conv.id);
                    setHistoryOpen(false);
                  }}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-lg px-2 py-2.5 text-left text-sm transition-colors',
                    activeConvId === conv.id ? 'bg-primary-10 text-primary' : 'hover:bg-muted',
                  )}
                >
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate">{conv.title}</span>
                </button>
              ))}
            </div>
          </SheetContent>
        </Sheet>

        {/* Chat area */}
        <Card className="flex min-h-0 min-w-0 flex-1 flex-col">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border p-3">
            <div className="flex min-w-0 items-center gap-2">
              <div className={cn('flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white', selectedAgent.color)}>
                <selectedAgent.icon className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">{selectedAgent.name}</p>
                <p className="text-2xs text-muted-foreground">En ligne</p>
              </div>
            </div>
            <select
              value={selectedAgent.id}
              onChange={(e) => setSelectedAgent(AGENTS.find((a) => a.id === e.target.value) || AGENTS[0])}
              className="max-w-full rounded-lg border border-border bg-card px-2 py-1.5 text-xs outline-none"
            >
              {AGENTS.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
            {messages.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border border-primary/20 bg-primary/[.07] shadow-ai">
                  <BrandLogo variant="icon" size="lg" theme="auto" decorative />
                </div>
                <h3 className="text-lg font-semibold">{t('ai.copilot')}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{t('ai.askAnything')}</p>
                <div className="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-3 max-w-lg">
                  {SUGGESTED_PROMPTS.map((prompt) => {
                    const Icon = prompt.icon;
                    return (
                      <button
                        key={prompt.key}
                        onClick={() => handleSend(prompt.text || t(prompt.key))}
                        className="flex flex-col items-center gap-2 rounded-xl border border-border p-4 transition-all hover:border-primary/30 hover:shadow-soft"
                      >
                        <Icon className="h-5 w-5 text-primary" />
                        <span className="text-xs font-medium text-center">{prompt.text || t(prompt.key)}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn('flex gap-3', msg.role === 'user' && 'flex-row-reverse')}
              >
                {msg.role === 'assistant' ? (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/[.07]">
                    <BrandLogo variant="icon" size="sm" theme="auto" decorative />
                  </div>
                ) : (
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback className="bg-primary-100 text-2xs text-primary-700">
                      {user ? initials(`${user.firstName} ${user.lastName}`) : '?'}
                    </AvatarFallback>
                  </Avatar>
                )}
                <div className={cn(
                  'max-w-[85%] rounded-2xl px-3 py-2.5 text-sm sm:max-w-[70%] sm:px-4',
                  msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
                )}>
                  <MarkdownContent
                    content={msg.content}
                    streaming={msg.streaming}
                    className={cn(msg.role === 'user' && 'text-primary-foreground')}
                  />
                  {msg.role === 'assistant' && msg.toolEvents && msg.toolEvents.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {msg.toolEvents.map((tool, index) => (
                        <Badge
                          key={`${tool.type}-${tool.name}-${tool.callId || index}`}
                          variant="outline"
                          className={cn(
                            'gap-1 text-2xs font-normal',
                            tool.type === 'tool_result' && tool.ok === false && 'border-red-300 text-red-700',
                            tool.type === 'tool_result' && tool.ok && 'border-emerald-300 text-emerald-700',
                          )}
                          title={
                            tool.type === 'tool_call'
                              ? JSON.stringify(tool.arguments || {})
                              : tool.ok
                                ? 'OK'
                                : tool.error || 'Erreur'
                          }
                        >
                          <Zap className="h-3 w-3 shrink-0" />
                          <span className="truncate">{tool.type === 'tool_call' ? `outil · ${tool.name}` : tool.name}</span>
                          {tool.type === 'tool_result' && (tool.ok ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />)}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {msg.role === 'assistant' && msg.approval && (
                    <ApprovalCard event={msg.approval} />
                  )}
                  {msg.role === 'assistant' && !msg.streaming && msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {msg.sources.map((s) => (
                        <Badge
                          key={`${s.documentId}-${s.chunkId || s.documentTitle}`}
                          variant="outline"
                          className="max-w-full gap-1 text-2xs font-normal"
                          title={s.excerpt}
                        >
                          <BookOpen className="h-3 w-3 shrink-0" />
                          <span className="truncate">{s.documentTitle}</span>
                        </Badge>
                      ))}
                    </div>
                  )}
                  {msg.role === 'assistant' && !msg.streaming && msg.content && (
                    <button className="mt-1.5 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
                      <Volume2 className="h-3 w-3" /> Écouter
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-border p-3">
            <div className="flex items-end gap-2">
              <div className="flex flex-1 items-end rounded-xl border border-input bg-card px-3 py-2 focus-within:ring-2 focus-within:ring-ring">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                  placeholder={t('ai.askAnything')}
                  rows={1}
                  className="max-h-24 flex-1 resize-none bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                />
              </div>
              <Button variant="outline" size="icon" onClick={() => setIsRecording(!isRecording)} className={cn(isRecording && 'bg-red-50 border-red-200')} aria-label={isRecording ? 'Arrêter l\'enregistrement' : 'Dicter un message'}>
                <Mic className={cn('h-4 w-4', isRecording && 'text-red-500 animate-pulse')} aria-hidden />
              </Button>
              <Button size="icon" onClick={() => handleSend()} disabled={!input.trim() || isStreaming} aria-label="Envoyer le message">
                <Send className="h-4 w-4" aria-hidden />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
