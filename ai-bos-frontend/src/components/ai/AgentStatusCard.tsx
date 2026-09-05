import { Bot, CheckCircle2, Clock3 } from 'lucide-react';
import { cn } from '@/lib/utils';

export function AgentStatusCard({ name, role, status, activity, tools = [], className }: {
  name: string;
  role: string;
  status: 'online' | 'busy' | 'offline';
  activity?: string;
  tools?: string[];
  className?: string;
}) {
  return (
    <article className={cn('rounded-lg border border-border bg-card p-4 shadow-card transition-colors hover:border-primary/25', className)}>
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary"><Bot className="h-5 w-5" /></div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <div><h3 className="text-sm font-semibold">{name}</h3><p className="text-xs text-muted-foreground">{role}</p></div>
            <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className={cn('h-1.5 w-1.5 rounded-full', status === 'online' && 'bg-emerald-500', status === 'busy' && 'bg-amber-500', status === 'offline' && 'bg-slate-500')} />
              {status}
            </span>
          </div>
          {tools.length > 0 && <div className="mt-3 flex flex-wrap gap-1.5">{tools.map((tool) => <span key={tool} className="rounded-sm bg-muted px-2 py-1 text-[11px] text-muted-foreground">{tool}</span>)}</div>}
          {activity && <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">{status === 'online' ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> : <Clock3 className="h-3.5 w-3.5" />}{activity}</p>}
        </div>
      </div>
    </article>
  );
}
