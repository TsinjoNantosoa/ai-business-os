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
          className={`min-w-0 transition-[padding] duration-200 ${collapsed ? 'lg:pl-[72px]' : 'lg:pl-[260px]'}`}
        >
          <Topbar onMobileMenuClick={() => setMobileOpen(true)} />
          <main id="main-content" className="mx-auto w-full max-w-[1520px] px-4 py-5 pb-24 sm:px-5 lg:p-6 lg:pb-8 xl:px-8">
            <Outlet />
          </main>
        </div>
        <CopilotWidget />
      </div>
    </TooltipProvider>
  );
}
