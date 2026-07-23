import { Download, FileSpreadsheet, FileText, Table2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { exportTable, type ExportColumn, type ExportFormat } from '@/lib/export';
import { toast } from 'sonner';

type Props<T> = {
  filename: string;
  title: string;
  columns: ExportColumn<T>[];
  rows: T[];
  sheetName?: string;
  label?: string;
  variant?: 'default' | 'outline' | 'ghost' | 'secondary';
  size?: 'default' | 'sm' | 'lg' | 'icon' | 'icon-sm';
  disabled?: boolean;
  className?: string;
};

export function ExportMenu<T>({
  filename,
  title,
  columns,
  rows,
  sheetName,
  label = 'Exporter',
  variant = 'outline',
  size = 'default',
  disabled,
  className,
}: Props<T>) {
  const run = (format: ExportFormat) => {
    try {
      if (!rows.length) {
        toast.error('Aucune donnée à exporter');
        return;
      }
      exportTable({ filename, title, sheetName, columns, rows, format });
      const ext = format === 'xls' ? 'Excel' : format.toUpperCase();
      toast.success(`Export ${ext} téléchargé (${rows.length})`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Export impossible');
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant={variant} size={size} disabled={disabled} className={className}>
          <Download className="h-4 w-4" />
          {label}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => run('csv')}>
          <Table2 className="h-4 w-4" />
          CSV
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => run('xls')}>
          <FileSpreadsheet className="h-4 w-4" />
          Excel (.xls)
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => run('pdf')}>
          <FileText className="h-4 w-4" />
          PDF
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
