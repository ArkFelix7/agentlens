/** Overall application layout wrapper with sidebar and top bar. */

import React, { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { BudgetAlertBanner, useBudgetAlerts, BudgetAlertMessage } from '@/components/budget/BudgetAlert';
import { onBudgetAlert } from '@/hooks/useWebSocket';

export function MainLayout() {
  const location = useLocation();
  const { alerts, addAlert, dismiss } = useBudgetAlerts();

  useEffect(() => {
    const unsubscribe = onBudgetAlert((alert) => addAlert(alert as BudgetAlertMessage));
    return () => void unsubscribe();
  }, [addAlert]);

  return (
    <div className="flex h-full bg-[var(--bg-primary)]">
      <BudgetAlertBanner alerts={alerts} onDismiss={dismiss} />
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />
        <main className="flex-1 overflow-hidden pb-7">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="h-full"
          >
            <Outlet />
          </motion.div>
        </main>
      </div>
      {/* Air-Gap Privacy Banner */}
      <div className="fixed bottom-0 left-0 right-0 h-7 bg-[#0a0a0f] border-t border-[#22c55e33] flex items-center justify-center gap-2 z-50">
        <span className="text-[#22c55e] text-xs font-mono">
          🔒 Air-Gap Mode — All trace data stored locally · Nothing leaves this machine
        </span>
      </div>
    </div>
  );
}
