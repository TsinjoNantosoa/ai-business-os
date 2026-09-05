import { cn } from '@/lib/utils';

type BrandLogoVariant = 'icon' | 'wordmark' | 'full' | 'hero';
type BrandLogoSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
type BrandLogoTheme = 'dark' | 'light' | 'auto';

interface BrandLogoProps {
  variant?: BrandLogoVariant;
  size?: BrandLogoSize;
  theme?: BrandLogoTheme;
  className?: string;
  decorative?: boolean;
  loading?: 'eager' | 'lazy';
}

const HEIGHTS: Record<BrandLogoVariant, Record<BrandLogoSize, string>> = {
  icon: { xs: 'h-5', sm: 'h-6', md: 'h-8', lg: 'h-10', xl: 'h-14' },
  wordmark: { xs: 'h-5', sm: 'h-6', md: 'h-8', lg: 'h-10', xl: 'h-14' },
  full: { xs: 'h-7', sm: 'h-9', md: 'h-12', lg: 'h-16', xl: 'h-20' },
  hero: { xs: 'h-10', sm: 'h-14', md: 'h-20', lg: 'h-24', xl: 'h-28' },
};

const LIGHT_TEXT: Record<BrandLogoSize, string> = {
  xs: 'text-sm',
  sm: 'text-base',
  md: 'text-xl',
  lg: 'text-2xl',
  xl: 'text-4xl',
};

const DIMENSIONS: Record<BrandLogoVariant, { width: number; height: number }> = {
  icon: { width: 434, height: 371 },
  wordmark: { width: 1421, height: 371 },
  full: { width: 1421, height: 371 },
  hero: { width: 1421, height: 371 },
};

function Artwork({ variant, className, loading }: Pick<Required<BrandLogoProps>, 'variant' | 'loading'> & { className?: string }) {
  const dimensions = DIMENSIONS[variant];
  return (
    <picture className={cn('block shrink-0', className)} aria-hidden="true">
      <source srcSet={`/brand/ai-bos-${variant}.webp`} type="image/webp" />
      <img
        src={`/brand/ai-bos-${variant}.png`}
        alt=""
        width={dimensions.width}
        height={dimensions.height}
        loading={loading}
        decoding="async"
        className="block h-full w-auto max-w-full object-contain"
      />
    </picture>
  );
}

function LightBrand({ variant, className, loading }: Pick<Required<BrandLogoProps>, 'variant' | 'loading'> & { className?: string }) {
  if (variant === 'icon') return <Artwork variant="icon" loading={loading} className={className} />;

  return (
    <span className={cn('inline-flex items-center gap-[0.45em]', className)} aria-hidden="true">
      <Artwork variant="icon" loading={loading} className="h-full" />
      <span className="flex min-w-0 flex-col leading-none">
        <span className="whitespace-nowrap font-bold tracking-[-0.04em] text-slate-950">AI <span className="brand-gradient-text">BOS</span></span>
        {(variant === 'full' || variant === 'hero') && (
          <span className="mt-[0.42em] whitespace-nowrap text-[0.24em] font-semibold tracking-[0.2em] text-slate-500">
            BUSINESS OPERATING SYSTEM
          </span>
        )}
      </span>
    </span>
  );
}

export function BrandLogo({
  variant = 'wordmark',
  size = 'md',
  theme = 'auto',
  className,
  decorative = false,
  loading = 'eager',
}: BrandLogoProps) {
  const sizeClass = HEIGHTS[variant][size];
  const accessibility = decorative ? { 'aria-hidden': true } : { role: 'img', 'aria-label': 'AI BOS' };

  return (
    <span className={cn('inline-flex max-w-full shrink-0 items-center', sizeClass, className)} {...accessibility}>
      {theme === 'dark' && <Artwork variant={variant} loading={loading} className="h-full" />}
      {theme === 'light' && <LightBrand variant={variant} loading={loading} className={cn('h-full', LIGHT_TEXT[size])} />}
      {theme === 'auto' && (
        <>
          <LightBrand variant={variant} loading={loading} className={cn('h-full dark:hidden', LIGHT_TEXT[size])} />
          <Artwork variant={variant} loading={loading} className="hidden h-full dark:block" />
        </>
      )}
    </span>
  );
}
