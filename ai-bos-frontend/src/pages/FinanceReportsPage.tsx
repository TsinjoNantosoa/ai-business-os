import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Download,
  FileText,
  Filter,
  BarChart3,
  LineChart,
  PieChart,
  AreaChart,
  Clock,
  Play,
} from 'lucide-react'
import { PageHeader } from '@/components/shared/PageHeader'
import { ExportMenu } from '@/components/shared/ExportMenu'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useI18n } from '@/lib/i18n/store'
import { cn, formatRelativeTime, formatDate } from '@/lib/utils'
import { getBIReports } from '@/lib/api/services'
import type { BIReport } from '@/lib/api/types'
import { exportTable, type ExportColumn } from '@/lib/export'
import { toast } from 'sonner'

const CHART_ICONS: Record<string, React.ElementType> = {
  bar: BarChart3,
  line: LineChart,
  pie: PieChart,
  area: AreaChart,
}

const REPORT_COLUMNS: ExportColumn<BIReport>[] = [
  { header: 'Nom', value: (r) => r.name },
  { header: 'Catégorie', value: (r) => r.category },
  { header: 'Type', value: (r) => r.chartType },
  { header: 'Dernière exécution', value: (r) => r.lastRun },
  { header: 'Planning', value: (r) => r.schedule || '' },
  { header: 'Description', value: (r) => r.description },
]

export function FinanceReportsPage() {
  const { t } = useI18n()
  const { data: reports } = useQuery({ queryKey: ['bi-reports'], queryFn: getBIReports })

  const allReports = reports || []
  const categories = useMemo(() => {
    const set = new Set<string>()
    allReports.forEach((r) => set.add(r.category))
    return ['all', ...Array.from(set)]
  }, [allReports])

  const [category, setCategory] = useState<string>('all')
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<BIReport | null>(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return allReports.filter((r) => {
      const matchCat = category === 'all' ? true : r.category === category
      const matchQ = !q ? true : (r.name + ' ' + r.description).toLowerCase().includes(q)
      return matchCat && matchQ
    })
  }, [allReports, category, query])

  const exportOne = (report: BIReport) => {
    try {
      exportTable({
        filename: `rapport-${report.name}`,
        title: report.name,
        sheetName: 'Rapport',
        columns: REPORT_COLUMNS,
        rows: [report],
        format: 'pdf',
      })
      toast.success('PDF téléchargé')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Export impossible')
    }
  }

  return (
    <div>
      <PageHeader
        title={t('nav.reports')}
        description="Galerie de rapports finance et exports"
        actions={
          <ExportMenu
            filename="rapports-finance"
            title="Rapports finance AI BOS"
            sheetName="Rapports"
            columns={REPORT_COLUMNS}
            rows={filtered}
          />
        }
      />

      <Card className="mb-6">
        <CardContent className="p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative flex-1 sm:max-w-md">
            <Filter className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Rechercher un rapport..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="w-full sm:w-56">
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Catégorie" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c === 'all' ? 'Toutes' : c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((report) => {
          const Icon = CHART_ICONS[report.chartType] || BarChart3
          return (
            <Card key={report.id} className="transition-shadow hover:shadow-elevated">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-50 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{report.name}</CardTitle>
                      <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{report.description}</p>
                    </div>
                  </div>
                  <Badge variant="muted">{report.category}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {formatRelativeTime(report.lastRun)}
                  </span>
                  <span>{report.schedule || 'Manuel'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Button size="sm" className="flex-1" onClick={() => setSelected(report)}>
                    <Play className="h-4 w-4" />
                    Ouvrir
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => exportOne(report)} title="Exporter PDF">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent className="max-w-2xl">
          {selected && (
            <>
              <DialogHeader>
                <DialogTitle>{selected.name}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">{selected.description}</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">Catégorie</p>
                    <p className="font-medium">{selected.category}</p>
                  </div>
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">Type</p>
                    <p className="font-medium">{selected.chartType}</p>
                  </div>
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">Dernière exécution</p>
                    <p className="font-medium">{formatDate(selected.lastRun)}</p>
                  </div>
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">Planning</p>
                    <p className="font-medium">{selected.schedule || 'Manuel'}</p>
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => exportOne(selected)}>
                    <FileText className="h-4 w-4" />
                    PDF
                  </Button>
                  <ExportMenu
                    filename={`rapport-${selected.name}`}
                    title={selected.name}
                    columns={REPORT_COLUMNS}
                    rows={[selected]}
                    size="sm"
                  />
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
