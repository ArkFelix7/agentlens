/** Modal dialog component. */

import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  maxWidth?: string;
}

export function Modal({ isOpen, onClose, title, children, maxWidth = 'max-w-lg' }: ModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-40"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className={`fixed z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full ${maxWidth}
              bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-lg shadow-[var(--shadow-lg)] p-6`}
          >
            {title && (
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono font-semibold text-[var(--text-primary)]">{title}</h3>
                <button
                  onClick={onClose}
                  className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                  aria-label="Close modal"
                >
                  <X size={16} />
                </button>
              </div>
            )}
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
