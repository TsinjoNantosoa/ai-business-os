import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { CopilotWidget } from '@/components/copilot/CopilotWidget';
import { TooltipProvider } from '@/components/ui/tooltip';

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="min-h-screen min-w-0 overflow-x-hidden bg-background">
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed(!collapsed)}
          mobileOpen={mobileOpen}
          onMobileClose={() => setMobileOpen(false)}
        />
        <div
          className={`min-w-0 transition-all duration-300 ${collapsed ? 'lg:pl-[72px]' : 'lg:pl-[260px]'}`}
        >
          <Topbar onMobileMenuClick={() => setMobileOpen(true)} />
          <main className="mx-auto w-full max-w-[1400px] px-3 py-4 pb-24 sm:px-4 sm:py-5 lg:p-6 lg:pb-6">
            <Outlet />
          </main>
        </div>
        <CopilotWidget />
      </div>
    </TooltipProvider>
  );
}
