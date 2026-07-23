import type { Edge, Node } from '@xyflow/react';
import type { WorkflowDefinition, WorkflowEdge, WorkflowGraphNode } from '@/lib/api/types';

export const ACTION_PALETTE = [
  'Envoyer email',
  'Créer tâche',
  'Notifier Slack',
  'Mettre à jour CRM',
  'Run AI agent',
  'Call API',
] as const;

export const TRIGGER_PALETTE = [
  'Manuel',
  'Lead créé',
  'Contact créé',
  'Facture créée',
  'Facture en retard',
  'Commande créée',
  'Employé créé',
  'Webhook entrant',
  'Planification hebdo',
  'Stock bas',
] as const;

export function toReactFlow(definition?: WorkflowDefinition | null): { nodes: Node[]; edges: Edge[] } {
  const nodes = (definition?.nodes || []).map((n) => ({
    id: n.id,
    type: n.type === 'trigger' ? 'trigger' : 'action',
    position: n.position || { x: 0, y: 0 },
    data: { label: n.data?.label || 'Étape', kind: n.data?.kind || n.type },
  }));
  const edges = (definition?.edges || []).map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
  }));
  return { nodes, edges };
}

export function fromReactFlow(nodes: Node[], edges: Edge[]): WorkflowDefinition {
  const graphNodes: WorkflowGraphNode[] = nodes.map((n) => ({
    id: n.id,
    type: (n.type === 'trigger' ? 'trigger' : 'action') as 'trigger' | 'action',
    position: { x: n.position.x, y: n.position.y },
    data: {
      label: String((n.data as { label?: string })?.label || 'Étape'),
      kind: String((n.data as { kind?: string })?.kind || n.type || 'action'),
    },
  }));
  const graphEdges: WorkflowEdge[] = edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
  }));
  return { nodes: graphNodes, edges: graphEdges };
}

export function defaultDefinition(): WorkflowDefinition {
  return {
    nodes: [
      {
        id: 'trigger-1',
        type: 'trigger',
        position: { x: 80, y: 140 },
        data: { label: 'Manuel', kind: 'trigger' },
      },
      {
        id: 'action-1',
        type: 'action',
        position: { x: 320, y: 140 },
        data: { label: 'Créer tâche', kind: 'action' },
      },
    ],
    edges: [{ id: 'e-trigger-1-action-1', source: 'trigger-1', target: 'action-1' }],
  };
}
