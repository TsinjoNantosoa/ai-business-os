import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Plus, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { Workflow, WorkflowDefinition, WorkflowStatus } from '@/lib/api/types';
import { workflowNodeTypes } from '@/components/workflows/workflow-nodes';
import {
  ACTION_PALETTE,
  TRIGGER_PALETTE,
  defaultDefinition,
  fromReactFlow,
  toReactFlow,
} from '@/components/workflows/workflow-graph';

type Props = {
  workflow?: Workflow | null
  onSave: (payload: {
    name: string
    description: string
    status: WorkflowStatus
    definition: WorkflowDefinition
  }) => Promise<void> | void
  saving?: boolean
}

export function WorkflowCanvas({ workflow, onSave, saving }: Props) {
  const initial = useMemo(
    () => toReactFlow(workflow?.definition || defaultDefinition()),
    [workflow?.id, workflow?.definition],
  );
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);
  const [name, setName] = useState(workflow?.name || 'Nouveau workflow');
  const [description, setDescription] = useState(workflow?.description || '');
  const [status, setStatus] = useState<WorkflowStatus>(workflow?.status || 'draft');

  useEffect(() => {
    const next = toReactFlow(workflow?.definition || defaultDefinition());
    setNodes(next.nodes);
    setEdges(next.edges);
    setName(workflow?.name || 'Nouveau workflow');
    setDescription(workflow?.description || '');
    setStatus(workflow?.status || 'draft');
  }, [workflow?.id, workflow?.definition, workflow?.name, workflow?.description, workflow?.status, setNodes, setEdges]);

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge({ ...connection, id: `e-${connection.source}-${connection.target}` }, eds)),
    [setEdges],
  );

  const addTrigger = (label: string) => {
    const id = `trigger-${crypto.randomUUID().slice(0, 8)}`;
    const node: Node = {
      id,
      type: 'trigger',
      position: { x: 60, y: 80 + nodes.length * 20 },
      data: { label, kind: 'trigger' },
    };
    setNodes((prev) => [...prev.filter((n) => n.type !== 'trigger'), node]);
  };

  const addAction = (label: string) => {
    const id = `action-${crypto.randomUUID().slice(0, 8)}`;
    const node: Node = {
      id,
      type: 'action',
      position: { x: 280 + nodes.length * 40, y: 140 },
      data: { label, kind: 'action' },
    };
    setNodes((prev) => [...prev, node]);
    const triggers = nodes.filter((n) => n.type === 'trigger');
    const actions = nodes.filter((n) => n.type === 'action');
    const source = (actions.length ? actions[actions.length - 1]?.id : undefined) || triggers[0]?.id;
    if (source) {
      const edge: Edge = { id: `e-${source}-${id}`, source, target: id };
      setEdges((prev) => [...prev, edge]);
    }
  };

  const handleSave = async () => {
    await onSave({
      name: name.trim() || 'Nouveau workflow',
      description: description.trim(),
      status,
      definition: fromReactFlow(nodes, edges),
    });
  };

  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-[1fr_1fr_160px_auto]">
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom du workflow" />
        <Input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description"
        />
        <select
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value as WorkflowStatus)}
        >
          <option value="draft">Brouillon</option>
          <option value="active">Actif</option>
          <option value="inactive">Inactif</option>
        </select>
        <Button onClick={() => void handleSave()} disabled={saving}>
          <Save className="h-4 w-4" />
          {saving ? 'Enregistrement…' : 'Enregistrer'}
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        <span className="self-center text-xs font-medium text-muted-foreground">Déclencheurs</span>
        {TRIGGER_PALETTE.map((label) => (
          <Button key={label} type="button" size="sm" variant="outline" onClick={() => addTrigger(label)}>
            <Plus className="h-3.5 w-3.5" />
            {label}
          </Button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        <span className="self-center text-xs font-medium text-muted-foreground">Actions</span>
        {ACTION_PALETTE.map((label) => (
          <Button key={label} type="button" size="sm" variant="secondary" onClick={() => addAction(label)}>
            <Plus className="h-3.5 w-3.5" />
            {label}
          </Button>
        ))}
      </div>

      <div className="h-[420px] overflow-hidden rounded-xl border border-border bg-muted/20">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={workflowNodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={18} size={1} />
          <MiniMap pannable zoomable />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}
