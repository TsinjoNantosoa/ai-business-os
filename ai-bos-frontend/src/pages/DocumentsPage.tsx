import { useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Folder, FileText, FileSpreadsheet, FileImage, Upload, Search,
  Star, MoreHorizontal, Sparkles, Download, Eye,
} from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { downloadDocument, getDocuments, uploadDocument } from '@/lib/api/services';
import { useI18n } from '@/lib/i18n/store';
import { cn, formatRelativeTime } from '@/lib/utils';

const FILE_ICONS: Record<string, React.ElementType> = {
  folder: Folder, pdf: FileText, docx: FileText, xlsx: FileSpreadsheet, image: FileImage,
};
const FILE_COLORS: Record<string, string> = {
  folder: 'text-primary', pdf: 'text-red-500', docx: 'text-blue-500', xlsx: 'text-emerald-500', image: 'text-violet-500',
};

export function DocumentsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFolder, setSelectedFolder] = useState<string | undefined>(undefined);
  const [search, setSearch] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: getDocuments });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(file, selectedFolder),
    onSuccess: () => {
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (error: Error) => setUploadError(error.message),
  });

  const folders = (documents || []).filter((d) => d.type === 'folder');
  const files = (documents || []).filter((d) => d.type !== 'folder' && (!selectedFolder || d.parentId === selectedFolder));
  const filteredFiles = files.filter((f) => !search || f.name.toLowerCase().includes(search.toLowerCase()));

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList?.length) return;
    uploadMutation.mutate(fileList[0]);
  };

  return (
    <div>
      <PageHeader
        title={t('nav.documents')}
        description="Gérez vos documents et fichiers"
        actions={
          <Button onClick={() => inputRef.current?.click()} disabled={uploadMutation.isPending}>
            <Upload className="h-4 w-4" />Téléverser
          </Button>
        }
      />

      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.webp"
        onChange={(e) => handleFiles(e.target.files)}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
        <Card className="lg:col-span-1">
          <CardContent className="p-3">
            <h3 className="mb-2 px-2 text-sm font-semibold">Dossiers</h3>
            <div className="space-y-0.5">
              <button
                onClick={() => setSelectedFolder(undefined)}
                className={cn('flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors hover:bg-muted', !selectedFolder && 'bg-primary-10 text-primary')}
              >
                <Folder className="h-4 w-4 text-primary" />
                Tous les fichiers
              </button>
              {folders.map((f) => (
                <button
                  key={f.id}
                  onClick={() => setSelectedFolder(f.id)}
                  className={cn('flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors hover:bg-muted', selectedFolder === f.id && 'bg-primary-10 text-primary')}
                >
                  <Folder className="h-4 w-4 text-primary" />
                  {f.name}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="lg:col-span-3">
          <div
            className="mb-4 flex items-center justify-center rounded-xl border-2 border-dashed border-border p-6 text-center transition-colors hover:border-primary/30 hover:bg-muted/30 cursor-pointer"
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              handleFiles(e.dataTransfer.files);
            }}
          >
            <div>
              <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm font-medium">
                {uploadMutation.isPending ? 'Téléversement en cours...' : 'Glissez vos fichiers ici ou cliquez pour téléverser'}
              </p>
              <p className="text-xs text-muted-foreground">PDF, DOCX, XLSX, images — 10MB max</p>
              {uploadError && <p className="mt-2 text-xs text-red-500">{uploadError}</p>}
            </div>
          </div>

          <div className="mb-4 relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Rechercher un fichier..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filteredFiles.map((file) => {
              const Icon = FILE_ICONS[file.type] || FileText;
              const color = FILE_COLORS[file.type] || 'text-muted-foreground';
              return (
                <Card key={file.id} className="group transition-all hover:shadow-elevated">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg bg-muted/50', color)}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                        {file.starred && <Star className="h-4 w-4 fill-amber-400 text-amber-400" />}
                        <Button variant="ghost" size="icon-sm"><MoreHorizontal className="h-4 w-4" /></Button>
                      </div>
                    </div>
                    <p className="mt-3 text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{formatRelativeTime(file.modifiedAt)} • {file.modifiedBy}</p>
                    <div className="mt-3 flex items-center gap-1 border-t border-border pt-2">
                      <Button variant="ghost" size="sm" className="text-xs"><Eye className="h-3.5 w-3.5" />Voir</Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-xs"
                        disabled={!file.hasFile}
                        onClick={() => downloadDocument(file.id, file.name)}
                      >
                        <Download className="h-3.5 w-3.5" />Télécharger
                      </Button>
                      <Button variant="ghost" size="sm" className="ml-auto text-xs text-primary"><Sparkles className="h-3.5 w-3.5" />Résumer</Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
