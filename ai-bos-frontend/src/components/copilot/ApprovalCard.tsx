import { useState } from 'react';
import { Check, X, ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  decideCopilotApproval,
  type CopilotApprovalEvent,
  type CopilotPendingAction,
} from '@/lib/api/services';
import { cn } from '@/lib/utils';

type Props = {
  event: CopilotApprovalEvent
  onResolved?: (action: CopilotPendingAction) => void
  className?: string
}

export function ApprovalCard({ event, onResolved, className }: Props) {
  const [busy, setBusy] = useState(false);
  const [resolved, setResolved] = useState<CopilotPendingAction | null>(null);
  const [error, setError] = useState<string | null>(null);

  const decide = async (decision: 'approve' | 'reject') => {
    setBusy(true);
    setError(null);
    try {
      const action = await decideCopilotApproval(event.approvalId, decision);
      setResolved(action);
      onResolved?.(action);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Décision impossible');
    } finally {
      setBusy(false);
    }
  };

  const status = resolved?.status;
  const argsPreview = JSON.stringify(event.arguments || {}, null, 0);

  return (
    <div
      className={cn(
        'mt-2 rounded-xl border border-amber-300/80 bg-amber-50/80 p-3 text-xs text-amber-950',
        className,
      )}
    >
      <div className="flex items-start gap-2">
        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />
        <div className="min-w-0 flex-1 space-y-1.5">
          <p className="font-medium">
            Approbation requise · <span className="font-mono">{event.name}</span>
          </p>
          <p className="text-amber-900/80">{event.message || 'Validez cette action sensible avant exécution.'}</p>
          <pre className="max-h-24 overflow-auto rounded-md bg-white/70 p-2 font-mono text-2xs text-muted-foreground">
            {argsPreview}
          </pre>

          {status === 'executed' && (
            <p className="text-emerald-700">Approuvé et exécuté.</p>
          )}
          {status === 'rejected' && <p className="text-red-700">Refusé — aucune modification.</p>}
          {status === 'failed' && (
            <p className="text-red-700">Échec à l&apos;exécution : {resolved?.error || 'erreur'}</p>
          )}
          {error && <p className="text-red-700">{error}</p>}

          {!resolved && (
            <div className="flex flex-wrap gap-2 pt-1">
              <Button size="sm" className="h-7 gap-1 text-xs" disabled={busy} onClick={() => void decide('approve')}>
                <Check className="h-3.5 w-3.5" />
                Approuver
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 gap-1 text-xs"
                disabled={busy}
                onClick={() => void decide('reject')}
              >
                <X className="h-3.5 w-3.5" />
                Refuser
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
