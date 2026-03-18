/** Real-time budget alert banner — appears at top of screen when a rule is triggered. */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface BudgetAlertMessage {
  rule_id: string;
  rule_name: string;
  rule_type: string;
  session_id: string;
  alert_type: 'threshold_breached' | 'loop_detected';
  current_value: number;
  threshold: number;
  message: string;
  triggered_at: string;
}

interface Props {
  alerts: BudgetAlertMessage[];
  onDismiss: (ruleId: string) => void;
}

export function BudgetAlertBanner({ alerts, onDismiss }: Props) {
  return (
    <div className="fixed top-0 left-0 right-0 z-[9999] flex flex-col gap-1 p-2 pointer-events-none">
      <AnimatePresence>
        {alerts.map(alert => (
          <motion.div
            key={alert.rule_id + alert.triggered_at}
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            className="pointer-events-auto flex items-start gap-3 bg-red-950 border border-red-500/40 rounded-lg px-4 py-3 shadow-xl"
          >
            <AlertTriangle size={16} className="text-red-400 mt-0.5 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-red-300">
                Budget Alert: {alert.rule_name}
              </div>
              <div className="text-xs text-red-400/80 mt-0.5">{alert.message}</div>
              <div className="text-xs text-red-500/60 mt-0.5">
                Session: {alert.session_id.slice(0, 16)}…
              </div>
            </div>
            <button
              onClick={() => onDismiss(alert.rule_id)}
              className="text-red-400/60 hover:text-red-300 transition-colors shrink-0"
            >
              <X size={14} />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

/** Hook to manage budget alerts from WebSocket messages. */
export function useBudgetAlerts() {
  const [alerts, setAlerts] = useState<BudgetAlertMessage[]>([]);

  const addAlert = (alert: BudgetAlertMessage) => {
    setAlerts(prev => [alert, ...prev].slice(0, 5)); // max 5 visible at once
    // Auto-dismiss after 30s
    setTimeout(() => {
      setAlerts(prev => prev.filter(a => a.rule_id !== alert.rule_id));
    }, 30_000);
  };

  const dismiss = (ruleId: string) => {
    setAlerts(prev => prev.filter(a => a.rule_id !== ruleId));
  };

  return { alerts, addAlert, dismiss };
}
