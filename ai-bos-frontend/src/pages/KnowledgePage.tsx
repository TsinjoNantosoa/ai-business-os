import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, BookMarked, Sparkles, Eye, ThumbsUp, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { getArticles, getKnowledgeStats, searchKnowledge } from '@/lib/api/services';
import type { KnowledgeSearchHit } from '@/lib/api/types';
import { useI18n } from '@/lib/i18n/store';
import { formatRelativeTime } from '@/lib/utils';

export function KnowledgePage() {
  const { t } = useI18n();
  const [search, setSearch] = useState('');
  const [ragQuery, setRagQuery] = useState('');
  const [ragHits, setRagHits] = useState<KnowledgeSearchHit[]>([]);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: articles } = useQuery({ queryKey: ['articles'], queryFn: getArticles });
  const { data: stats } = useQuery({ queryKey: ['knowledge-stats'], queryFn: getKnowledgeStats });

  const filtered = (articles || []).filter(
    (a) =>
      !search ||
      a.title.toLowerCase().includes(search.toLowerCase()) ||
      a.category.toLowerCase().includes(search.toLowerCase()),
  );
  const selected = (articles || []).find((a) => a.id === selectedId);

  const runRagSearch = async () => {
    const q = ragQuery.trim();
    if (q.length < 2) return;
    setRagLoading(true);
    setRagError(null);
    try {
      const res = await searchKnowledge(q, 6);
      setRagHits(res.items);
    } catch (err) {
      setRagError(err instanceof Error ? err.message : 'Recherche impossible');
      setRagHits([]);
    } finally {
      setRagLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title={t('nav.knowledge')}
        description={
          stats
            ? `Base de connaissances RAG — ${stats.documentCount} docs / ${stats.chunkCount} chunks indexés`
            : 'Base de connaissances et documentation produit'
        }
      />
      <Card className="mb-6 border-primary/20 bg-gradient-to-br from-primary-50/50 to-violet-50/30">
        <CardContent className="p-5">
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-ai">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <h3 className="text-sm font-semibold">Recherche RAG (Document/*.md)</h3>
          </div>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Ex: isolation multi-tenant, JWT, pipeline RAG..."
                className="pl-9"
                value={ragQuery}
                onChange={(e) => setRagQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void runRagSearch();
                }}
              />
            </div>
            <Button onClick={() => void runRagSearch()} disabled={ragLoading || ragQuery.trim().length < 2}>
              {ragLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Rechercher'}
            </Button>
          </div>
          {ragError && <p className="mt-2 text-sm text-destructive">{ragError}</p>}
          {ragHits.length > 0 && (
            <div className="mt-4 space-y-2">
              {ragHits.map((hit) => (
                <div key={hit.chunkId} className="rounded-md border border-border bg-background/80 p-3">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">{hit.documentTitle}</p>
                    <Badge variant="muted" className="text-2xs">
                      score {hit.relevanceScore}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{hit.excerpt}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-2 lg:col-span-1">
          <div className="relative mb-2">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Filtrer les FAQ..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          {filtered.map((a) => (
            <Card
              key={a.id}
              className={`cursor-pointer transition-all hover:shadow-elevated ${selected?.id === a.id ? 'border-primary' : ''}`}
              onClick={() => setSelectedId(a.id)}
            >
              <CardContent className="p-3">
                <Badge variant="muted" className="mb-1 text-2xs">
                  {a.category}
                </Badge>
                <p className="text-sm font-medium">{a.title}</p>
                <p className="line-clamp-1 text-xs text-muted-foreground">{a.excerpt}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="lg:col-span-2">
          {selected ? (
            <Card>
              <CardContent className="p-6">
                <Badge variant="muted" className="mb-2">
                  {selected.category}
                </Badge>
                <h1 className="text-xl font-bold">{selected.title}</h1>
                <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                  <span>Par {selected.author}</span>
                  <span>•</span>
                  <span>{formatRelativeTime(selected.updatedAt)}</span>
                  <span className="flex items-center gap-1">
                    <Eye className="h-3 w-3" />
                    {selected.views}
                  </span>
                  <span className="flex items-center gap-1">
                    <ThumbsUp className="h-3 w-3" />
                    {selected.helpful}
                  </span>
                </div>
                <div className="prose prose-sm mt-4 max-w-none">
                  <p className="text-sm leading-relaxed text-foreground">{selected.content}</p>
                  <p className="mt-3 text-sm text-muted-foreground">{selected.excerpt}</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-20">
                <BookMarked className="h-12 w-12 text-muted-foreground" />
                <p className="mt-3 text-sm text-muted-foreground">Sélectionnez un article ou lancez une recherche RAG</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
