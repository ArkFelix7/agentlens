/** Toast notification system. */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react';
import clsx from 'clsx';

type ToastType = 'success' | 'warning' | 'error' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  addToast: (type: ToastType, message: string) => void;
}

const ToastContext = createContext<ToastContextValue>({ addToast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((t) => [...t, { id, type, message }]);
    setTimeout(() => {
      setToasts((t) => t.filter((toast) => toast.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => setToasts((t) => t.filter((toast) => toast.id !== id));

  const icons = {
    success: <CheckCircle size={14} className="text-[var(--accent-emerald)]" />,
    warning: <AlertTriangle size={14} className="text-[var(--accent-amber)]" />,
    error: <XCircle size={14} className="text-[var(--accent-red)]" />,
    info: <Info size={14} className="text-[var(--accent-cyan)]" />,
  };

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 40 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2 px-3 py-2 bg-[var(--bg-elevated)] border border-[var(--border-default)]
                rounded-lg shadow-[var(--shadow-md)] text-sm text-[var(--text-primary)] min-w-64 max-w-sm"
            >
              {icons[toast.type]}
              <span className="flex-1 text-xs">{toast.message}</span>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
              >
                <X size={12} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}
