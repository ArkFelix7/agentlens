/** Empty state component with AgentLens setup instructions. */

import React from 'react';
import { motion } from 'framer-motion';

interface EmptyStateProps {
  title?: string;
  description?: string;
  showSetup?: boolean;
}

export function EmptyState({
  title = 'Waiting for agent connection...',
  description = 'Start your agent with AgentLens instrumentation to see traces here.',
  showSetup = true,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col items-center justify-center h-full p-8 text-center"
    >
      {/* Logo */}
      <div className="relative mb-6">
        <div className="w-16 h-16 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] flex items-center justify-center">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="8" stroke="#6366f1" strokeWidth="2" fill="none" />
            <circle cx="16" cy="16" r="3" fill="#6366f1" />
            <line x1="16" y1="4" x2="16" y2="10" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" />
            <line x1="16" y1="22" x2="16" y2="28" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" />
            <line x1="4" y1="16" x2="10" y2="16" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" />
            <line x1="22" y1="16" x2="28" y2="16" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
        {/* Pulsing ring */}
        <div className="absolute inset-0 rounded-2xl border border-[var(--accent-indigo)] opacity-30 live-pulse" />
      </div>

      <h2 className="text-lg font-mono font-semibold text-[var(--text-primary)] mb-2">{title}</h2>
      <p className="text-sm text-[var(--text-secondary)] max-w-md mb-6">{description}</p>

      {showSetup && (
        <div className="w-full max-w-md text-left">
          <p className="text-xs text-[var(--text-tertiary)] font-mono mb-2">QUICK START</p>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4 space-y-3">
            <div>
              <p className="text-xs text-[var(--text-tertiary)] mb-1">1. Install the SDK</p>
              <code className="block text-xs text-[var(--accent-emerald)] font-mono bg-[var(--bg-primary)] rounded px-3 py-2">
                pip install agentlens
              </code>
            </div>
            <div>
              <p className="text-xs text-[var(--text-tertiary)] mb-1">2. Add to your agent</p>
              <code className="block text-xs text-[var(--accent-indigo)] font-mono bg-[var(--bg-primary)] rounded px-3 py-2 whitespace-pre">{`from agentlens import auto_instrument
auto_instrument()  # That's it!`}</code>
            </div>
            <div>
              <p className="text-xs text-[var(--text-tertiary)] mb-1">3. Or use the demo</p>
              <code className="block text-xs text-[var(--accent-cyan)] font-mono bg-[var(--bg-primary)] rounded px-3 py-2">
                python examples/demo_multi_step.py
              </code>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
