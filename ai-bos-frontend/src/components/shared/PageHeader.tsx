import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export function PageHeader({
  title,
  description,
  actions,
  className,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'mb-4 flex min-w-0 flex-col gap-3 sm:mb-6 sm:gap-4 sm:flex-row sm:items-start sm:justify-between lg:items-center',
        className
      )}
    >
      <div className="min-w-0 flex-1">
        <h1 className="page-title break-words text-[1.5rem] sm:text-2xl lg:text-[1.75rem]">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground sm:text-[0.9375rem]">{description}</p>
        )}
      </div>
      {actions && (
        <div className="flex w-full min-w-0 flex-wrap items-center gap-2 sm:w-auto sm:justify-end">
          {actions}
        </div>
      )}
    </div>
  );
}
