import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, AlertTriangle, Bell, Building2, Check, CheckCircle2, ChevronDown, Globe, Info, LogOut, Menu, Moon, Search, Settings, Sparkles, Sun, User } from 'lucide-react';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { useTheme } from '@/lib/theme/store';
import { getNotifications, markAllNotificationsRead, markNotificationRead, subscribeNotifications } from '@/lib/api/services';
import type { AppNotification } from '@/lib/api/types';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { CommandDialog, CommandInput, CommandList, CommandGroup, CommandItem, CommandEmpty } from '@/components/ui/command';
import { NAV_GROUPS } from '@/lib/navigation';
import { cn, initials, formatRelativeTime } from '@/lib/utils';

export function Topbar({ onMobileMenuClick }: { onMobileMenuClick: () => void }) {
  const { user, organizations, orgId, setOrg, logout, token } = useAuth();
  const { t, locale, setLocale } = useI18n();
  const isDark = useTheme((state) => state.resolved) === 'dark';
  const toggleTheme = useTheme((state) => state.toggle);
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const apiHealthy = true;

  useEffect(() => { getNotifications().then(setNotifications).catch(() => undefined); }, []);
  useEffect(() => {
    if (!token) return;
    return subscribeNotifications((payload) => {
      if (payload.type === 'notification' && payload.notification) {
        const incoming = payload.notification;
        setNotifications((current) => [incoming, ...current.filter((item) => item.id !== incoming.id)]);
      }
    });
  }, [token]);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const unreadCount = notifications.filter((item) => !item.read).length;
  const currentOrg = organizations.find((organization) => organization.id === orgId) || organizations[0];
  const iconFor = (type: AppNotification['type']) => {
    if (type === 'success') return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
    if (type === 'warning') return <AlertTriangle className="h-4 w-4 text-amber-500" />;
    if (type === 'error') return <AlertCircle className="h-4 w-4 text-red-500" />;
    return <Info className="h-4 w-4 text-blue-500" />;
  };
  const markAllRead = async () => {
    try { await markAllNotificationsRead(); setNotifications((items) => items.map((item) => ({ ...item, read: true }))); } catch { /* keep current state */ }
  };
  const openNotification = async (notification: AppNotification) => {
    if (!notification.read) {
      try { await markNotificationRead(notification.id); setNotifications((items) => items.map((item) => item.id === notification.id ? { ...item, read: true } : item)); } catch { /* keep current state */ }
    }
    if (notification.link) navigate(notification.link);
  };

  return (
    <>
      <header className="sticky top-0 z-30 flex h-14 min-w-0 items-center gap-2 border-b border-border/75 bg-background/90 px-3 backdrop-blur-md sm:h-16 sm:gap-3 sm:px-4 lg:px-6">
        <Button variant="ghost" size="icon" onClick={onMobileMenuClick} className="shrink-0 lg:hidden" aria-label="Ouvrir le menu"><Menu className="h-5 w-5" /></Button>
        <button type="button" onClick={() => setSearchOpen(true)} aria-label={t('common.search')} className="group flex h-10 min-w-0 flex-1 max-w-md items-center gap-2 rounded-md border border-border bg-card/70 px-3 text-sm text-muted-foreground transition-colors hover:border-primary/30 hover:bg-card">
          <Search className="h-4 w-4 shrink-0" /><span className="hidden truncate sm:inline">{t('common.search')}...</span>
          <kbd className="ml-auto hidden rounded-sm border border-border bg-muted px-1.5 py-0.5 text-[10px] font-semibold sm:block">Ctrl K</kbd>
        </button>
        <div className="ml-auto flex shrink-0 items-center gap-1 sm:gap-2">
          {currentOrg && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild><Button variant="ghost" size="sm" className="hidden gap-2 md:inline-flex"><Building2 /><span className="max-w-36 truncate">{currentOrg.name}</span><ChevronDown /></Button></DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56"><DropdownMenuLabel>Organisations</DropdownMenuLabel><DropdownMenuSeparator />{organizations.map((organization) => <DropdownMenuItem key={organization.id} onClick={() => setOrg(organization.id)}><span className="truncate">{organization.name}</span>{organization.id === orgId && <Check className="ml-auto text-primary" />}</DropdownMenuItem>)}</DropdownMenuContent>
            </DropdownMenu>
          )}
          <Button size="sm" className="hidden gap-2 sm:inline-flex" onClick={() => navigate('/app/copilot')}><Sparkles />Ask AI</Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" className="relative" aria-label={`Notifications${unreadCount ? `, ${unreadCount} non lues` : ''}`}><Bell />{unreadCount > 0 && <span className="absolute right-1 top-1 h-2 w-2 rounded-full border-2 border-background bg-primary" />}</Button></DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[min(22rem,calc(100vw-1rem))] p-0">
              <div className="flex items-center justify-between border-b border-border p-3"><span className="text-sm font-semibold">Notifications</span><div className="flex items-center gap-2">{unreadCount > 0 && <Badge>{unreadCount}</Badge>}{unreadCount > 0 && <Button variant="ghost" size="sm" onClick={() => void markAllRead()}>Tout lire</Button>}</div></div>
              <div className="max-h-80 overflow-y-auto scrollbar-thin">
                {notifications.slice(0, 6).map((notification) => <button key={notification.id} type="button" onClick={() => void openNotification(notification)} className={cn('flex w-full gap-3 border-b border-border/70 p-3 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring', !notification.read && 'border-l-2 border-l-primary bg-primary/[.045]')}><div className="mt-0.5">{iconFor(notification.type)}</div><div className="min-w-0 flex-1"><p className="text-sm font-medium">{notification.title}</p><p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{notification.message}</p><p className="mt-1 text-[11px] text-muted-foreground">{formatRelativeTime(notification.createdAt, locale)}</p></div></button>)}
              </div>
              <button type="button" onClick={() => navigate('/app/inbox')} className="w-full p-3 text-center text-xs font-semibold text-primary hover:bg-muted">Voir toutes les notifications</button>
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger asChild><button type="button" className="flex items-center gap-2 rounded-md p-1 hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" aria-label="Menu du compte"><Avatar className="h-8 w-8"><AvatarFallback className="bg-primary/15 text-xs font-semibold text-primary">{user ? initials(`${user.firstName} ${user.lastName}`) : '?'}</AvatarFallback></Avatar><div className="hidden text-left leading-tight lg:block"><p className="text-xs font-semibold">{user ? `${user.firstName} ${user.lastName}` : ''}</p><p className="text-[11px] text-muted-foreground">{user?.jobTitle}</p></div><ChevronDown className="hidden h-3.5 w-3.5 text-muted-foreground lg:block" /></button></DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-60">
              <div className="px-2 py-1.5"><p className="text-sm font-semibold">{user?.firstName} {user?.lastName}</p><p className="truncate text-xs text-muted-foreground">{user?.email}</p></div><DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/app/settings/profile')}><User />{t('common.profile')}</DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate('/app/settings/profile')}><Settings />{t('common.settings')}</DropdownMenuItem>
              <DropdownMenuItem onClick={toggleTheme}>{isDark ? <Sun /> : <Moon />}{isDark ? 'Mode clair' : 'Mode sombre'}</DropdownMenuItem>
              <DropdownMenuItem onClick={() => setLocale(locale === 'fr' ? 'en' : locale === 'en' ? 'ar' : 'fr')}><Globe />Langue · {locale.toUpperCase()}</DropdownMenuItem>
              <DropdownMenuItem disabled><span className={cn('h-2 w-2 rounded-full', apiHealthy ? 'bg-emerald-500' : 'bg-red-500')} />API {apiHealthy ? 'opérationnelle' : 'indisponible'}</DropdownMenuItem>
              <DropdownMenuSeparator /><DropdownMenuItem onClick={logout} className="text-destructive"><LogOut />{t('common.logout')}</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>
      <CommandDialog open={searchOpen} onOpenChange={setSearchOpen}>
        <CommandInput placeholder={`${t('common.search')} ou demander à l’IA...`} />
        <CommandList><CommandEmpty>{t('common.noResults')}</CommandEmpty>{NAV_GROUPS.map((group) => { const items = group.items.filter((item) => (!item.permission || useAuth.getState().hasPermission(item.permission)) && (!item.permissions || useAuth.getState().hasAnyPermission(item.permissions))); if (!items.length) return null; return <CommandGroup key={group.label} heading={t(group.label)}>{items.map((item) => { const Icon = item.icon; return <CommandItem key={item.path} onSelect={() => { navigate(item.path); setSearchOpen(false); }}><Icon className="text-muted-foreground" /><span>{t(item.label)}</span></CommandItem>; })}</CommandGroup>; })}<CommandGroup heading="Intelligence"><CommandItem onSelect={() => { navigate('/app/copilot'); setSearchOpen(false); }}><Sparkles className="text-primary" /><span>Demander à l’IA</span></CommandItem></CommandGroup></CommandList>
      </CommandDialog>
    </>
  );
}
