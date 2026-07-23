import { describe, expect, it } from 'vitest';
import { buildCsv, buildExcelXml, exportTable } from '@/lib/export'

type Row = { name: string; amount: number }

const columns = [
  { header: 'Nom', value: (r: Row) => r.name },
  { header: 'Montant', value: (r: Row) => r.amount },
]

const rows: Row[] = [
  { name: 'Acme', amount: 1200 },
  { name: 'Beta, "SAS"', amount: 340 },
]

describe('export helpers', () => {
  it('builds CSV with BOM and escaping', () => {
    const csv = buildCsv(columns, rows)
    expect(csv.startsWith('\uFEFF')).toBe(true)
    expect(csv).toContain('Nom,Montant')
    expect(csv).toContain('"Beta, ""SAS"""')
  })

  it('builds Excel XML spreadsheet', () => {
    const xml = buildExcelXml(columns, rows, 'Test')
    expect(xml).toContain('Excel.Sheet')
    expect(xml).toContain('Acme')
    expect(xml).toContain('ss:Type="Number">1200')
  })

  it('exportTable throws on empty rows', () => {
    expect(() =>
      exportTable({
        filename: 'empty',
        columns,
        rows: [],
        format: 'csv',
      }),
    ).toThrow(/Aucune donnée/)
  })
})
