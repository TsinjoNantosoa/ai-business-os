import { describe, expect, it } from 'vitest';
import { buildCsv, buildExcelXml, buildPdfTable, exportTable, pdfEscape } from '@/lib/export'

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

  it('encodes French accents as WinAnsi octal escapes for PDF', () => {
    expect(pdfEscape('Trésorerie')).toBe('Tr\\351sorerie')
    expect(pdfEscape('Catégorie')).toBe('Cat\\351gorie')
    expect(pdfEscape('Décaissement')).toBe('D\\351caissement')
    expect(pdfEscape('Intérêts')).toBe('Int\\351r\\352ts')
    expect(pdfEscape('matériel')).toBe('mat\\351riel')
    expect(pdfEscape('àêôùç')).toBe('\\340\\352\\364\\371\\347')
  })

  it('builds PDF with WinAnsiEncoding and accent escapes', () => {
    const pdf = buildPdfTable(
      'Paiements & Trésorerie',
      [
        { header: 'Catégorie', value: (r: Row) => r.name },
        { header: 'Montant', value: (r: Row) => r.amount },
      ],
      [{ name: 'Dépense SaaS', amount: 42 }],
    )
    const text = new TextDecoder('latin1').decode(pdf)
    expect(text).toContain('/Encoding /WinAnsiEncoding')
    expect(text).toContain('Tr\\351sorerie')
    expect(text).toContain('Cat\\351gorie')
    expect(text).toContain('D\\351pense SaaS')
    // Must not embed raw UTF-8 multi-byte for é (C3 A9)
    expect(text.includes('\u00c3\u00a9')).toBe(false)
  })
})
