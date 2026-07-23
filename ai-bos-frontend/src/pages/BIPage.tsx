import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart3, LineChart, PieChart, AreaChart, Sparkles, Send, Clock, Play, BookOpen,
} from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { getBIReports, streamCopilotResponse, type CopilotSource } from '@/lib/api/services';
import { useI18n } from '@/lib/i18n/store';
import { formatRelativeTime } from '@/lib/utils';
import { toast } from 'sonner';

const CHART_ICONS: Record<string, React.ElementType> = {
  bar: BarChart3,
  line: LineChart,
  pie: PieChart,
  area: AreaChart,
};

export function BIPage() {
  const { t } = useI18n();
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<CopilotSource[]>([]);
  const [activeReportId, setActiveReportId] = useState<string | null>(null);
  const [querying, setQuerying] = useState(false);
  const [answerOpen, setAnswerOpen] = useState(false);
  const { data: reports } = useQuery({ queryKey: ['bi-reports'], queryFn: getBIReports });

  const runNlQuery = async (prompt: string) => {
    if (!prompt.trim() || querying) return;
    setQuerying(true);
    setAnswer('');
    setSources([]);
    setAnswerOpen(true);
    try {
      let text = '';
      for await (const event of streamCopilotResponse(prompt, 'analyst', 'BI')) {
        if (event.type === 'chunk') {
          text += event.content;
          setAnswer(text);
        } else if (event.type === 'done') {
          setSources(event.sources || []);
        }
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Interrogation impossible');
      setAnswerOpen(false);
    } finally {
      setQuerying(false);
    }
  };

  const handleQuery = () => void runNlQuery(query);

  const runReport = (report: { id: string; name: string; description: string }) => {
    setActiveReportId(report.id);
    setQuery(report.name);
    void runNlQuery(
      `Génère une synthèse BI du rapport « ${report.name} » : ${report.description}. Donne les points clés et recommandations.`,
    );
  };

  return (
    <div>
      <PageHeader title={t('nav.bi')} description="Business Intelligence et rapports" />

      <Card className="mb-6 border-primary/20 bg-gradient-to-br from-primary-50/50 to-violet-50/30">
        <CardContent className="p-5">
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-ai">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <h3 className="text-sm font-semibold">Posez une question en langage naturel</h3>
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Ex: Quel est le revenu par mois pour 2024 ?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
            />
            <Button onClick={handleQuery} disabled={querying || !query.trim()}>
              {querying ? <Clock className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              Interroger
            </Button>
          </div>
          {answer && !answerOpen && (
            <Button variant="outline" size="sm" className="mt-3 gap-1.5" onClick={() => setAnswerOpen(true)}>
              <Sparkles className="h-3.5 w-3.5" />
              Rouvrir la dernière réponse IA
            </Button>
          )}
        </CardContent>
      </Card>

      <h3 className="mb-3 text-sm font-semibold">Rapports pré-construits</h3>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {(reports || []).map((report) => {
          const Icon = CHART_ICONS[report.chartType] || BarChart3;
          const running = querying && activeReportId === report.id;
          return (
            <Card key={report.id} className="flex flex-col transition-all hover:shadow-elevated">
              <CardContent className="flex flex-1 flex-col p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-50 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    disabled={querying}
                    onClick={() => runReport(report)}
                    title="Exécuter via IA"
                  >
                    {running ? <Clock className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  </Button>
                </div>
                <h4 className="mt-3 text-sm font-semibold">{report.name}</h4>
                <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{report.description}</p>
                <div className="mt-auto flex items-center justify-between gap-2 border-t border-border pt-3">
                  <Badge variant="muted" className="shrink-0 text-2xs">
                    {report.category}
                  </Badge>
                  <span className="truncate text-2xs text-muted-foreground" title={formatRelativeTime(report.lastRun)}>
                    Dernier run: {formatRelativeTime(report.lastRun)}
                  </span>
                </div>
                {report.schedule && (
                  <div className="mt-2 flex items-center gap-1 text-2xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    Planifié: {report.schedule}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Dialog open={answerOpen} onOpenChange={setAnswerOpen}>
        <DialogContent className="flex max-h-[85vh] max-w-2xl flex-col gap-0 overflow-hidden p-0">
          <DialogHeader className="shrink-0 border-b border-border px-6 py-4">
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Réponse IA
            </DialogTitle>
            <DialogDescription>
              {querying ? 'Analyse en cours…' : 'Synthèse générée — les rapports restent accessibles derrière.'}
            </DialogDescription>
          </DialogHeader>
          <div className="min-h-0 flex-1 overflow-y-auto px-6 py-4 scrollbar-thin">
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {answer || (querying ? '…' : 'Aucune réponse.')}
              {querying && <span className="ml-0.5 inline-block h-3 w-1 animate-pulse bg-current" />}
            </div>
            {sources.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-1.5 border-t border-border pt-3">
                {sources.map((s) => (
                  <Badge
                    key={`${s.documentId}-${s.chunkId || s.documentTitle}`}
                    variant="muted"
                    className="gap-1 text-2xs font-normal"
                    title={s.excerpt}
                  >
                    <BookOpen className="h-3 w-3" />
                    {s.documentTitle}
                  </Badge>
                ))}
              </div>
            )}
          </div>
          <DialogFooter className="shrink-0 border-t border-border px-6 py-3">
            <Button onClick={() => setAnswerOpen(false)} disabled={querying && !answer}>
              Fermer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
