/** Shared table export: CSV, Excel (.xls), PDF — zero external deps. */

export type ExportColumn<T> = {
  header: string;
  value: (row: T) => string | number | null | undefined;
};

export type ExportFormat = 'csv' | 'xls' | 'pdf';

function stamp(base: string, ext: string): string {
  const safe = base.replace(/[^\w\-àâäéèêëïîôùûüç]+/gi, '_').replace(/_+/g, '_');
  return `${safe}-${new Date().toISOString().slice(0, 10)}.${ext}`;
}

function cellText(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '';
  return String(value);
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function escapeCsv(value: string): string {
  if (/[",\n\r]/.test(value)) return `"${value.replace(/"/g, '""')}"`;
  return value;
}

export function buildCsv<T>(columns: ExportColumn<T>[], rows: T[]): string {
  const header = columns.map((c) => escapeCsv(c.header)).join(',');
  const body = rows.map((row) =>
    columns.map((c) => escapeCsv(cellText(c.value(row)))).join(','),
  );
  return `\uFEFF${[header, ...body].join('\r\n')}`;
}

function escapeXml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** SpreadsheetML — opens natively in Excel / LibreOffice as .xls */
export function buildExcelXml<T>(
  columns: ExportColumn<T>[],
  rows: T[],
  sheetName = 'Export',
): string {
  const headerCells = columns
    .map(
      (c) =>
        `<Cell ss:StyleID="Header"><Data ss:Type="String">${escapeXml(c.header)}</Data></Cell>`,
    )
    .join('');
  const dataRows = rows
    .map((row) => {
      const cells = columns
        .map((c) => {
          const raw = c.value(row);
          if (typeof raw === 'number' && Number.isFinite(raw)) {
            return `<Cell><Data ss:Type="Number">${raw}</Data></Cell>`;
          }
          return `<Cell><Data ss:Type="String">${escapeXml(cellText(raw))}</Data></Cell>`;
        })
        .join('');
      return `<Row>${cells}</Row>`;
    })
    .join('\n');

  return `<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
 <Styles>
  <Style ss:ID="Header">
   <Font ss:Bold="1"/>
   <Interior ss:Color="#EEF2FF" ss:Pattern="Solid"/>
  </Style>
 </Styles>
 <Worksheet ss:Name="${escapeXml(sheetName.slice(0, 31))}">
  <Table>
   <Row>${headerCells}</Row>
   ${dataRows}
  </Table>
 </Worksheet>
</Workbook>`;
}

/**
 * Map Unicode → WinAnsi (CP1252) byte. Helvetica Type1 only paints these glyphs
 * when /Encoding /WinAnsiEncoding is set; UTF-8 multi-byte sequences must not
 * appear in PDF literal strings.
 */
function unicodeToWinAnsi(code: number): number | null {
  if (code >= 0x20 && code <= 0x7e) return code;
  if (code >= 0xa0 && code <= 0xff) return code;
  // CP1252 C1 range (0x80–0x9F) — common FR / typography
  const map: Record<number, number> = {
    0x20ac: 0x80, // €
    0x201a: 0x82, // ‚
    0x0192: 0x83, // ƒ
    0x201e: 0x84, // „
    0x2026: 0x85, // …
    0x2020: 0x86, // †
    0x2021: 0x87, // ‡
    0x02c6: 0x88, // ˆ
    0x2030: 0x89, // ‰
    0x0160: 0x8a, // Š
    0x2039: 0x8b, // ‹
    0x0152: 0x8c, // Œ
    0x017d: 0x8e, // Ž
    0x2018: 0x91, // ‘
    0x2019: 0x92, // ’
    0x201c: 0x93, // “
    0x201d: 0x94, // ”
    0x2022: 0x95, // •
    0x2013: 0x96, // –
    0x2014: 0x97, // —
    0x02dc: 0x98, // ˜
    0x2122: 0x99, // ™
    0x0161: 0x9a, // š
    0x203a: 0x9b, // ›
    0x0153: 0x9c, // œ
    0x017e: 0x9e, // ž
    0x0178: 0x9f, // Ÿ
  };
  return map[code] ?? null;
}

/** PDF literal string: ASCII + octal escapes for WinAnsi bytes (stays ASCII-safe). */
export function pdfEscape(text: string): string {
  let out = '';
  for (const char of text) {
    if (char === '\\' || char === '(' || char === ')') {
      out += `\\${char}`;
      continue;
    }
    const cp = char.codePointAt(0)!;
    if (cp === 0x09) {
      out += '\\t';
      continue;
    }
    if (cp === 0x0a) {
      out += '\\n';
      continue;
    }
    if (cp === 0x0d) {
      out += '\\r';
      continue;
    }
    if (cp >= 0x20 && cp <= 0x7e) {
      out += char;
      continue;
    }
    const win = unicodeToWinAnsi(cp);
    if (win != null) {
      out += `\\${win.toString(8).padStart(3, '0')}`;
      continue;
    }
    // Fallback: strip combining marks (é → e) so layout stays readable
    const folded = char.normalize('NFD').replace(/\p{M}/gu, '');
    if (folded && folded !== char) {
      out += pdfEscape(folded);
    } else {
      out += '?';
    }
  }
  return out;
}

/** @internal exported for tests */
export function buildPdfTable<T>(title: string, columns: ExportColumn<T>[], rows: T[]): Uint8Array {
  const pageWidth = 842;
  const pageHeight = 595;
  const margin = 36;
  const fontSize = 9;
  const titleSize = 14;
  const rowH = 16;
  const colW = (pageWidth - margin * 2) / Math.max(columns.length, 1);

  type PageOps = string[];
  const pages: PageOps[] = [];
  let ops: string[] = [];
  let y = 0;

  const newPage = (withTitle: boolean) => {
    ops = [];
    y = pageHeight - margin - (withTitle ? 28 : 20);
    if (withTitle) {
      ops.push(`BT /F1 ${titleSize} Tf ${margin} ${pageHeight - margin - 8} Td (${pdfEscape(title)}) Tj ET`);
    }
    let x = margin;
    columns.forEach((col) => {
      ops.push(`BT /F1 ${fontSize} Tf ${x + 2} ${y} Td (${pdfEscape(col.header.slice(0, 28))}) Tj ET`);
      x += colW;
    });
    y -= 4;
    ops.push(`${margin} ${y} m ${pageWidth - margin} ${y} l S`);
    y -= rowH;
    pages.push(ops);
  };

  newPage(true);

  rows.forEach((row) => {
    if (y < margin + rowH) newPage(false);
    let x = margin;
    columns.forEach((col) => {
      const text = cellText(col.value(row)).slice(0, 36);
      ops.push(`BT /F1 ${fontSize} Tf ${x + 2} ${y} Td (${pdfEscape(text)}) Tj ET`);
      x += colW;
    });
    y -= rowH;
  });

  const encoder = new TextEncoder();
  const parts: Uint8Array[] = [];
  const offsets: number[] = [0];
  let offset = 0;

  const push = (s: string) => {
    const bytes = encoder.encode(s);
    parts.push(bytes);
    offset += bytes.length;
  };

  push('%PDF-1.4\n');

  const obj = (id: number, body: string) => {
    offsets[id] = offset;
    push(`${id} 0 obj\n${body}\nendobj\n`);
  };

  const catalogId = 1;
  const pagesId = 2;
  const fontId = 3;
  const contentStart = 4;
  const pageStart = contentStart + pages.length;

  obj(catalogId, `<< /Type /Catalog /Pages ${pagesId} 0 R >>`);
  const kids = pages.map((_, i) => `${pageStart + i} 0 R`).join(' ');
  obj(pagesId, `<< /Type /Pages /Kids [${kids}] /Count ${pages.length} >>`);
  obj(fontId, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>');

  pages.forEach((pageOps, i) => {
    const stream = `0.25 w\n${pageOps.join('\n')}\n`;
    const streamBytes = encoder.encode(stream);
    obj(contentStart + i, `<< /Length ${streamBytes.length} >>\nstream\n${stream}endstream`);
  });

  pages.forEach((_, i) => {
    obj(
      pageStart + i,
      `<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Contents ${contentStart + i} 0 R /Resources << /Font << /F1 ${fontId} 0 R >> >> >>`,
    );
  });

  const xrefStart = offset;
  const maxId = pageStart + pages.length - 1;
  push(`xref\n0 ${maxId + 1}\n`);
  push('0000000000 65535 f \n');
  for (let i = 1; i <= maxId; i++) {
    push(`${String(offsets[i]).padStart(10, '0')} 00000 n \n`);
  }
  push(`trailer\n<< /Size ${maxId + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xrefStart}\n%%EOF`);

  const total = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(total);
  let pos = 0;
  parts.forEach((p) => {
    out.set(p, pos);
    pos += p.length;
  });
  return out;
}

export function exportTable<T>(options: {
  filename: string;
  title?: string;
  sheetName?: string;
  columns: ExportColumn<T>[];
  rows: T[];
  format: ExportFormat;
}): void {
  const { filename, title, sheetName, columns, rows, format } = options;
  if (!rows.length) {
    throw new Error('Aucune donnée à exporter');
  }

  if (format === 'csv') {
    downloadBlob(new Blob([buildCsv(columns, rows)], { type: 'text/csv;charset=utf-8' }), stamp(filename, 'csv'));
    return;
  }

  if (format === 'xls') {
    downloadBlob(
      new Blob([buildExcelXml(columns, rows, sheetName || title || 'Export')], {
        type: 'application/vnd.ms-excel;charset=utf-8',
      }),
      stamp(filename, 'xls'),
    );
    return;
  }

  downloadBlob(
    new Blob([buildPdfTable(title || filename, columns, rows)], { type: 'application/pdf' }),
    stamp(filename, 'pdf'),
  );
}

export function exportTextPdf(filename: string, title: string, lines: string[]): void {
  const columns: ExportColumn<{ line: string }>[] = [{ header: 'Détail', value: (r) => r.line }];
  exportTable({
    filename,
    title,
    columns,
    rows: lines.map((line) => ({ line })),
    format: 'pdf',
  });
}
