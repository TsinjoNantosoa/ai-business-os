import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Crown, TrendingUp, Wallet, Megaphone, Scale, Users, BarChart3,
  KanbanSquare, LifeBuoy, Video, ShieldCheck, Plus, Activity, Clock, Bot,
} from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  getAgentDocs,
  getAgentDocsGuide,
  getAgents,
  getAiTraces,
  getAiUsageSummary,
} from '@/lib/api/services';
import { useI18n } from '@/lib/i18n/store';
import { formatRelativeTime } from '@/lib/utils';

const AGENT_ICONS: Record<string, React.ElementType> = {
  Crown, TrendingUp, Wallet, Megaphone, Scale, Users, BarChart3,
  KanbanSquare, LifeBuoy, Video, ShieldCheck,
};

export function AgentsPage() {
  const { t } = useI18n();
  const [tab, setTab] = useState('gallery');
  const { data: agents } = useQuery({ queryKey: ['agents'], queryFn: getAgents });
  const { data: usage } = useQuery({ queryKey: ['ai-usage'], queryFn: () => getAiUsageSummary(30) });
  const { data: traces } = useQuery({ queryKey: ['ai-traces'], queryFn: () => getAiTraces(20) });
  const { data: docs } = useQuery({
    queryKey: ['agent-docs'],
    queryFn: getAgentDocs,
    enabled: tab === 'docs',
  });
  const { data: guide } = useQuery({
    queryKey: ['agent-docs-guide'],
    queryFn: getAgentDocsGuide,
    enabled: tab === 'docs',
  });

  return (
    <div>
      <PageHeader
        title={t('nav.agents')}
        description="Galerie, observabilité S34 et documentation client S36"
        actions={<Button><Plus className="h-4 w-4" />Créer un agent</Button>}
      />

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="gallery">Galerie</TabsTrigger>
          <TabsTrigger value="docs">Documentation</TabsTrigger>
        </TabsList>

        <TabsContent value="gallery">
          {usage && (
            <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
              <Card>
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">Traces (30j)</p>
                  <p className="mt-1 text-xl font-semibold">{usage.traceCount}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">Tokens</p>
                  <p className="mt-1 text-xl font-semibold">{usage.totalTokens.toLocaleString('fr-FR')}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">Coût estimé</p>
                  <p className="mt-1 text-xl font-semibold">${usage.totalCostUsd.toFixed(4)}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">In / Out</p>
                  <p className="mt-1 text-sm font-semibold">
                    {usage.totalInputTokens.toLocaleString('fr-FR')} / {usage.totalOutputTokens.toLocaleString('fr-FR')}
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {(agents || []).map((agent) => {
              const Icon = AGENT_ICONS[agent.icon] || Bot;
              const agentUsage = usage?.byAgent?.find((a) => a.agentId === agent.id);
              return (
                <Card key={agent.id} className="group cursor-pointer border-primary/15 transition-[border-color,box-shadow] hover:border-primary/35 hover:shadow-ai">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between">
                      <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/10 text-primary ring-1 ring-inset ring-primary/20">
                        <Icon className="h-6 w-6" />
                      </div>
                      <StatusBadge status={agent.status} />
                    </div>
                    <h3 className="mt-3 text-sm font-semibold">{agent.name}</h3>
                    <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{agent.description}</p>
                    <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1"><Activity className="h-3 w-3" />{agent.toolsCount} outils</span>
                        <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{agent.lastUsed ? formatRelativeTime(agent.lastUsed) : 'Jamais'}</span>
                      </div>
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <Badge variant="muted" className="text-2xs">
                        {agentUsage
                          ? `${agentUsage.traces} traces · $${agentUsage.costUsd.toFixed(4)}`
                          : `${agent.conversations} conversations`}
                      </Badge>
                      <Button variant="outline" size="sm" className="text-xs">Configurer</Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <Card className="mt-6">
            <CardContent className="p-0">
              <div className="border-b border-border px-5 py-3">
                <h3 className="text-sm font-semibold">Traces récentes</h3>
                <p className="text-xs text-muted-foreground">Appels Copilot / agents — tokens & latence</p>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Agent</TableHead>
                    <TableHead>Statut</TableHead>
                    <TableHead>Provider</TableHead>
                    <TableHead>Tokens</TableHead>
                    <TableHead>Coût</TableHead>
                    <TableHead>Latence</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(traces || []).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center text-muted-foreground">
                        Aucune trace — utilisez le Copilot pour en générer.
                      </TableCell>
                    </TableRow>
                  ) : (
                    (traces || []).map((tr) => (
                      <TableRow key={tr.id}>
                        <TableCell className="font-mono text-xs">{tr.id}</TableCell>
                        <TableCell className="text-xs">{tr.agentId || '—'}</TableCell>
                        <TableCell><StatusBadge status={tr.status} /></TableCell>
                        <TableCell className="text-xs">{tr.provider}/{tr.model || '—'}</TableCell>
                        <TableCell className="text-xs">{tr.inputTokens + tr.outputTokens}</TableCell>
                        <TableCell className="text-xs">${tr.costUsd.toFixed(5)}</TableCell>
                        <TableCell className="text-xs">{tr.latencyMs} ms</TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {tr.createdAt ? formatRelativeTime(tr.createdAt) : '—'}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="docs" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {(docs?.sections || []).map((section) => (
              <Card key={section.id}>
                <CardContent className="p-5">
                  <h3 className="text-sm font-semibold">{section.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{section.body}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardContent className="p-0">
              <div className="border-b border-border px-5 py-3">
                <h3 className="text-sm font-semibold">Outils Copilot</h3>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nom</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>HITL</TableHead>
                    <TableHead>Permissions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(docs?.tools || []).map((tool) => (
                    <TableRow key={tool.name}>
                      <TableCell className="font-mono text-xs">{tool.name}</TableCell>
                      <TableCell className="text-xs">{tool.description}</TableCell>
                      <TableCell className="text-xs">{tool.requiresApproval ? 'Oui' : 'Non'}</TableCell>
                      <TableCell className="text-xs">{tool.permissions.join(', ')}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-0">
              <div className="border-b border-border px-5 py-3">
                <h3 className="text-sm font-semibold">Templates workflows</h3>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nom</TableHead>
                    <TableHead>Trigger</TableHead>
                    <TableHead>Actions</TableHead>
                    <TableHead>Description</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(docs?.workflowTemplates || []).map((tpl) => (
                    <TableRow key={tpl.id}>
                      <TableCell className="font-medium text-sm">{tpl.name}</TableCell>
                      <TableCell className="text-xs">{tpl.trigger}</TableCell>
                      <TableCell className="text-xs">{tpl.actions.join(' → ')}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{tpl.description}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <h3 className="text-sm font-semibold">{guide?.title || 'Guide client'}</h3>
              <pre className="mt-3 max-h-[28rem] overflow-auto whitespace-pre-wrap rounded-lg bg-muted/40 p-4 text-xs leading-relaxed text-foreground">
                {guide?.content || 'Chargement du guide…'}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
