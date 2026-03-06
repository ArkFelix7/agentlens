/** Generic badge component with configurable color variants. */

import React from 'react';
import clsx from 'clsx';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'indigo' | 'emerald' | 'amber' | 'red' | 'cyan' | 'purple' | 'default';
  size?: 'sm' | 'md';
  className?: string;
}

const variantClasses: Record<string, string> = {
  indigo: 'bg-[rgba(99,102,241,0.15)] text-[#6366f1] border border-[rgba(99,102,241,0.3)]',
  emerald: 'bg-[rgba(16,185,129,0.15)] text-[#10b981] border border-[rgba(16,185,129,0.3)]',
  amber: 'bg-[rgba(245,158,11,0.15)] text-[#f59e0b] border border-[rgba(245,158,11,0.3)]',
  red: 'bg-[rgba(239,68,68,0.15)] text-[#ef4444] border border-[rgba(239,68,68,0.3)]',
  cyan: 'bg-[rgba(6,182,212,0.15)] text-[#06b6d4] border border-[rgba(6,182,212,0.3)]',
  purple: 'bg-[rgba(168,85,247,0.15)] text-[#a855f7] border border-[rgba(168,85,247,0.3)]',
  default: 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border-subtle)]',
};

export function Badge({ children, variant = 'default', size = 'sm', className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center font-mono rounded',
        size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-sm px-2 py-1',
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
