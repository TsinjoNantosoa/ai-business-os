import { Loader2 } from 'lucide-react';

export function PageLoader() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center" role="status" aria-label="Chargement">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  );
}
