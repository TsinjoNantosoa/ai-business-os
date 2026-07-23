import { Handle, Position, type NodeProps } from '@xyflow/react';
import { CheckSquare, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

type NodeData = { label?: string };

export function TriggerNode({ data, selected }: NodeProps) {
  const label = (data as NodeData)?.label || 'Déclencheur';
  return (
    <div
      className={cn(
        'min-w-[150px] rounded-xl border-2 bg-amber-50 px-3 py-2.5 shadow-sm',
        selected ? 'border-amber-500' : 'border-amber-200',
      )}
    >
      <div className="mb-1 flex items-center gap-1.5 text-2xs font-semibold uppercase tracking-wide text-amber-700">
        <Zap className="h-3.5 w-3.5" />
        Déclencheur
      </div>
      <p className="text-sm font-medium text-amber-950">{label}</p>
      <Handle type="source" position={Position.Right} className="!h-2.5 !w-2.5 !bg-amber-500" />
    </div>
  );
}

export function ActionNode({ data, selected }: NodeProps) {
  const label = (data as NodeData)?.label || 'Action';
  return (
    <div
      className={cn(
        'min-w-[150px] rounded-xl border-2 bg-sky-50 px-3 py-2.5 shadow-sm',
        selected ? 'border-sky-500' : 'border-sky-200',
      )}
    >
      <Handle type="target" position={Position.Left} className="!h-2.5 !w-2.5 !bg-sky-500" />
      <div className="mb-1 flex items-center gap-1.5 text-2xs font-semibold uppercase tracking-wide text-sky-700">
        <CheckSquare className="h-3.5 w-3.5" />
        Action
      </div>
      <p className="text-sm font-medium text-sky-950">{label}</p>
      <Handle type="source" position={Position.Right} className="!h-2.5 !w-2.5 !bg-sky-500" />
    </div>
  );
}

export const workflowNodeTypes = {
  trigger: TriggerNode,
  action: ActionNode,
};
