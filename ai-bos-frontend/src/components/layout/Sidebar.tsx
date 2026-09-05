import { useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { ChevronDown, PanelLeftClose, PanelLeft, Sparkles } from 'lucide-react';
import { NAV_GROUPS } from '@/lib/navigation';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { BrandLogo } from '@/components/brand/BrandLogo';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

export function Sidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onMobileClose,
}: {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}) {
  const { hasPermission, hasAnyPermission } = useAuth();
  const { t } = useI18n();
  const location = useLocation();
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(() => {
    const active = NAV_GROUPS.find((group) => group.items.some((item) => location.pathname.startsWith(item.path)));
    return new Set(['nav.overview', ...(active ? [active.label] : [])]);
  });

  const toggleGroup = (label: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  };

  const canSeeItem = (item: { permission?: string; permissions?: string[] }) => {
    if (item.permission) return hasPermission(item.permission);
    if (item.permissions) return hasAnyPermission(item.permissions);
    return true;
  };

  // On mobile drawer, always show labels even if desktop sidebar is collapsed.
  const iconMode = collapsed && !mobileOpen;

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-slate-950/70 backdrop-blur-sm lg:hidden"
          onClick={onMobileClose}
          aria-label="Fermer la navigation"
        />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground shadow-floating transition-all duration-200 ease-out lg:shadow-none',
          'w-[min(100vw,280px)] lg:w-[260px]',
          iconMode && 'lg:w-[72px]',
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Header */}
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-sidebar-border px-3 sm:h-16 sm:px-4">
          <Link to="/app/dashboard" aria-label="AI BOS — Tableau de bord" className="flex min-w-0 items-center">
            <BrandLogo variant={iconMode ? 'icon' : 'wordmark'} size={iconMode ? 'md' : 'sm'} theme="dark" />
          </Link>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onToggle}
            className="hidden lg:flex text-slate-400 hover:text-white hover:bg-sidebar-accent"
            aria-label={collapsed ? 'Développer la barre latérale' : 'Réduire la barre latérale'}
          >
            {collapsed ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto overscroll-contain scrollbar-thin py-3 px-2">
          {NAV_GROUPS.map((group) => {
            const visibleItems = group.items.filter(canSeeItem);
            if (visibleItems.length === 0) return null;
            const isExpanded = expandedGroups.has(group.label) || iconMode;

            return (
              <div key={group.label} className="mb-1">
                {!iconMode && (
                  <button
                    type="button"
                    onClick={() => toggleGroup(group.label)}
                    className="flex min-h-9 w-full items-center justify-between px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-sidebar-muted hover:text-sidebar-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary"
                    aria-expanded={isExpanded}
                  >
                    <span>{t(group.label)}</span>
                    <ChevronDown
                      className={cn('h-3 w-3 transition-transform', isExpanded ? '' : '-rotate-90')}
                    />
                  </button>
                )}
                {isExpanded && (
                  <div className="mt-0.5 space-y-1">
                    {visibleItems.map((item) => {
                      const isActive = location.pathname === item.path;
                      const Icon = item.icon;

                      if (iconMode) {
                        return (
                          <Tooltip key={item.path}>
                            <TooltipTrigger asChild>
                              <NavLink
                                to={item.path}
                                onClick={onMobileClose}
                                className={cn(
                                  'flex h-10 w-10 items-center justify-center rounded-lg transition-all',
                                  isActive
                                    ? 'bg-primary/15 text-primary-300 shadow-soft ring-1 ring-inset ring-primary/20'
                                    : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-white'
                                )}
                              >
                                <Icon className="h-[18px] w-[18px]" />
                              </NavLink>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="bg-slate-900">
                              {t(item.label)}
                            </TooltipContent>
                          </Tooltip>
                        );
                      }

                      return (
                        <NavLink
                          key={item.path}
                          to={item.path}
                          onClick={onMobileClose}
                          className={cn(
                            'group flex min-h-11 items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all lg:min-h-0 lg:py-2',
                            isActive
                              ? 'bg-primary/15 text-primary-200 shadow-soft ring-1 ring-inset ring-primary/20'
                              : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-white'
                          )}
                        >
                          <Icon className="h-[18px] w-[18px] shrink-0" />
                          <span className="truncate">{t(item.label)}</span>
                          {item.badge && (
                            <span className="ml-auto rounded-full bg-primary-500/20 px-1.5 py-0.5 text-2xs text-primary-300">
                              {item.badge}
                            </span>
                          )}
                        </NavLink>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        {/* Footer */}
        {!iconMode && (
          <div className="border-t border-sidebar-border p-3">
            <div className="flex items-center gap-2 rounded-lg bg-sidebar-accent p-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/15 text-primary-300 ring-1 ring-inset ring-primary/25">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-white">AI BOS Pro</p>
                <p className="text-2xs text-slate-500">Plan Enterprise</p>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
