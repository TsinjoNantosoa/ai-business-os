import { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles, Send, Bot, User as UserIcon, TrendingUp, Wallet, Zap,
  BookOpen, Shield, RotateCcw, ChevronDown,
} from 'lucide-react';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import {
  streamCopilotResponse,
  type CopilotApprovalEvent,
  type CopilotSource,
  type CopilotToolEvent,
} from '@/lib/api/services';
import { ApprovalCard } from '@/components/copilot/ApprovalCard';
import { MarkdownContent } from '@/components/shared/MarkdownContent';
import { cn } from '@/lib/utils';
import './copilot-widget.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
  sources?: CopilotSource[];
  toolEvents?: CopilotToolEvent[];
  approval?: CopilotApprovalEvent;
  time: string;
}

const AGENTS = [
  { id: 'ceo', name: 'CEO', icon: Bot },
  { id: 'sales', name: 'Sales', icon: TrendingUp },
  { id: 'finance', name: 'Finance', icon: Wallet },
  { id: 'hr', name: 'HR', icon: UserIcon },
  { id: 'analyst', name: 'Data', icon: Zap },
];

const QUICK_REPLIES = [
  { icon: '👥', label: 'Contacts CRM', prompt: 'montre-moi les contacts CRM' },
  { icon: '💶', label: 'Factures en retard', prompt: 'quelles factures sont en retard ?' },
  { icon: '✅', label: 'Créer une tâche', prompt: 'crée une tâche Relancer client VIP' },
  { icon: '📁', label: 'Liste des projets', prompt: 'liste les projets' },
];

const MAX_CHARS = 200;
const GREETING_ID = 'b-init';

function nowTime(): string {
  return new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

function getContextFromPath(pathname: string): string {
  if (pathname.includes('crm')) return 'CRM';
  if (pathname.includes('finance')) return 'Finance';
  if (pathname.includes('hr')) return 'HR';
  if (pathname.includes('project')) return 'Projects';
  if (pathname.includes('analytics') || pathname.includes('bi') || pathname.includes('forecast')) return 'Analytics';
  if (pathname.includes('support')) return 'Support';
  if (pathname.includes('marketing')) return 'Marketing';
  if (pathname.includes('dashboard')) return 'Dashboard';
  return 'Global';
}

function greetingMessage(): Message {
  return {
    id: GREETING_ID,
    role: 'assistant',
    content: 'Bonjour ! Je suis AI BOS, votre compagnon IA. Comment puis-je vous aider ?',
    time: nowTime(),
  };
}

function SourceChips({ sources }: { sources: CopilotSource[] }) {
  if (!sources.length) return null;
  return (
    <div className="bos-chips">
      {sources.map((s) => (
        <span
          key={`${s.documentId}-${s.chunkId || s.documentTitle}`}
          className="bos-chip"
          title={s.excerpt}
        >
          <BookOpen className="h-3 w-3 shrink-0" />
          <span className="truncate">{s.documentTitle}</span>
        </span>
      ))}
    </div>
  );
}

function ToolChips({ events }: { events: CopilotToolEvent[] }) {
  if (!events.length) return null;
  return (
    <div className="bos-chips">
      {events.map((tool, index) => (
        <span
          key={`${tool.type}-${tool.name}-${tool.callId || index}`}
          className={cn(
            'bos-chip',
            tool.type === 'tool_result' && tool.ok && 'ok',
            tool.type === 'tool_result' && tool.ok === false && 'err',
          )}
        >
          <Zap className="h-3 w-3 shrink-0" />
          <span className="truncate">
            {tool.type === 'tool_call' ? `outil · ${tool.name}` : tool.ok ? `✓ ${tool.name}` : `✗ ${tool.name}`}
          </span>
        </span>
      ))}
    </div>
  );
}

export function CopilotWidget() {
  const { user } = useAuth();
  const { locale, setLocale } = useI18n();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([greetingMessage()]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(AGENTS[0]);
  const [showQuickReplies, setShowQuickReplies] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const context = getContextFromPath(location.pathname);
  const langLabel = (locale || 'fr').toUpperCase().slice(0, 2);

  useEffect(() => {
    if (!open) return;
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open, isStreaming]);

  const clearConversation = () => {
    setMessages([greetingMessage()]);
    setShowQuickReplies(true);
    setInput('');
  };

  const toggleLanguage = () => {
    const next = locale === 'fr' ? 'en' : locale === 'en' ? 'ar' : 'fr';
    setLocale(next);
  };

  const handleSend = async (promptText?: string) => {
    const text = (promptText || input).trim().slice(0, MAX_CHARS);
    if (!text || isStreaming) return;

    setShowQuickReplies(false);
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      time: nowTime(),
    };
    const assistantId = crypto.randomUUID();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      streaming: true,
      toolEvents: [],
      time: nowTime(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput('');
    setIsStreaming(true);
    if (inputRef.current) inputRef.current.style.height = '46px';

    try {
      for await (const event of streamCopilotResponse(text, selectedAgent.id, context)) {
        if (event.type === 'chunk') {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + event.content } : m)),
          );
        } else if (event.type === 'tool_call' || event.type === 'tool_result') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, toolEvents: [...(m.toolEvents || []), event] } : m,
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

  if (!user) return null;

  return (
    <div className="aibos-chat-root">
      <AnimatePresence>
        {!open && (
          <motion.div
            key="fab"
            className="bos-fab-wrap"
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.85 }}
          >
            <button type="button" className="bos-fab" onClick={() => setOpen(true)} aria-label="Ouvrir le Copilot">
              <span className="bos-fab-pulse" />
              <Sparkles className="h-7 w-7" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {open && (
          <motion.div
            key="widget"
            className="bos-widget"
            initial={{ opacity: 0, y: 40, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 40, scale: 0.96 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
          >
            <header className="bos-header">
              <svg className="bos-header-curve" viewBox="0 0 400 40" preserveAspectRatio="none" aria-hidden>
                <defs>
                  <linearGradient id="bosCurveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#132251" />
                    <stop offset="100%" stopColor="#0f1b42" />
                  </linearGradient>
                </defs>
                <path d="M 0 18 Q 100 0, 200 18 T 400 18 L 400 0 L 0 0 Z" fill="url(#bosCurveGrad)" />
                <path
                  d="M 0 18 Q 100 6, 200 18 T 400 18"
                  stroke="#ffffff"
                  strokeWidth="1"
                  fill="none"
                  opacity="0.15"
                />
              </svg>

              <div className="bos-header-left">
                <div className="bos-avatar-square">
                  <Sparkles className="h-5 w-5 text-amber-300" />
                </div>
                <div className="bos-header-info">
                  <span className="bos-title">Chat with</span>
                  <span className="bos-name">AI BOS</span>
                  <span className="bos-status">
                    <span className="bos-online-dot" />
                    En ligne · {context}
                  </span>
                </div>
              </div>

              <div className="bos-header-right">
                <select
                  className="bos-agent-select"
                  value={selectedAgent.id}
                  onChange={(e) => setSelectedAgent(AGENTS.find((a) => a.id === e.target.value) || AGENTS[0])}
                  aria-label="Agent"
                  title="Choisir un agent"
                >
                  {AGENTS.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </select>
                <button type="button" className="bos-header-btn" onClick={toggleLanguage} title="Langue">
                  {langLabel}
                </button>
                <button
                  type="button"
                  className="bos-header-btn"
                  onClick={clearConversation}
                  title="Réinitialiser"
                  aria-label="Réinitialiser"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  className="bos-header-btn"
                  onClick={() => setOpen(false)}
                  title="Réduire"
                  aria-label="Réduire"
                >
                  <ChevronDown className="h-4 w-4" />
                </button>
              </div>
            </header>

            <div className="bos-body">
              <div className="bos-messages" ref={listRef}>
                {messages.map((msg) => (
                  <div key={msg.id}>
                    <div className={cn('bos-msg-row', msg.role === 'user' ? 'user' : 'bot')}>
                      {msg.role === 'assistant' && (
                        <div className="bos-bot-avatar">
                          <Sparkles className="h-3.5 w-3.5" />
                        </div>
                      )}
                      <div className={cn('bos-bubble', msg.role === 'user' ? 'user' : 'bot')}>
                        {msg.streaming && !msg.content ? (
                          <p className="bos-bubble-text">
                            <span className="bos-typing" style={{ padding: 0, border: 'none', boxShadow: 'none' }}>
                              <span className="bos-typing-dots">
                                <span />
                                <span />
                                <span />
                              </span>
                            </span>
                          </p>
                        ) : (
                          <MarkdownContent
                            content={msg.content}
                            streaming={msg.streaming}
                            className="bos-bubble-text"
                          />
                        )}
                        {msg.role === 'assistant' && msg.toolEvents && <ToolChips events={msg.toolEvents} />}
                        {msg.role === 'assistant' && msg.approval && <ApprovalCard event={msg.approval} />}
                        {msg.role === 'assistant' && !msg.streaming && msg.sources && (
                          <SourceChips sources={msg.sources} />
                        )}
                        <span className="bos-msg-time">{msg.time}</span>
                      </div>
                    </div>

                    {msg.id === GREETING_ID && showQuickReplies && !isStreaming && (
                      <div className="bos-quick-choice">
                        <div className="bos-quick-title">Faites votre choix :</div>
                        <div className="bos-quick-list">
                          {QUICK_REPLIES.map((item) => (
                            <button
                              key={item.label}
                              type="button"
                              className="bos-quick-pill"
                              onClick={() => void handleSend(item.prompt)}
                            >
                              <span className="bos-quick-icon">{item.icon}</span>
                              <span className="bos-quick-label">{item.label}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                <div ref={messagesEndRef} />
              </div>

              <div className="bos-composer">
                <div className="bos-composer-wrap">
                  <textarea
                    ref={inputRef}
                    className="bos-composer-input"
                    value={input}
                    maxLength={MAX_CHARS}
                    rows={1}
                    placeholder="Ecrivez votre message..."
                    onChange={(e) => {
                      const next = e.target.value.slice(0, MAX_CHARS);
                      setInput(next);
                      const el = e.target;
                      el.style.height = '46px';
                      el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        void handleSend();
                      }
                    }}
                    disabled={isStreaming}
                  />
                  <span className="bos-char-count">
                    {input.length}/{MAX_CHARS}
                  </span>
                  <button
                    type="button"
                    className="bos-send-btn"
                    disabled={!input.trim() || isStreaming}
                    onClick={() => void handleSend()}
                    aria-label="Envoyer"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="bos-disclaimer">
                <Shield className="bos-disclaimer-icon h-4 w-4" />
                <span>IA officielle AI BOS. Évitez de partager des infos personnelles.</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
