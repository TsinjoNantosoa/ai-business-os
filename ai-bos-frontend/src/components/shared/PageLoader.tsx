import { BrandLogo } from '@/components/brand/BrandLogo';

export function PageLoader() {
  return (
    <div
      className="flex min-h-[40vh] items-center justify-center"
      role="status"
      aria-label="Chargement"
    >
      <BrandLogo variant="icon" size="lg" theme="auto" decorative className="animate-pulse-soft" />
    </div>
  );
}
