import { BrandLogo } from '@/components/brand/BrandLogo';

export function Logo({ className, collapsed = false }: { className?: string; collapsed?: boolean }) {
  return <BrandLogo variant={collapsed ? 'icon' : 'wordmark'} size="md" theme="auto" className={className} />;
}
