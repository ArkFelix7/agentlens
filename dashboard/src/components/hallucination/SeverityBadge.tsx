/** Severity badge for hallucination alerts. */

import React from 'react';
import { Severity } from '@/types';
import clsx from 'clsx';

const SEVERITY_CONFIG: Record<Severity, { label: string; className: string }> = {
  critical: {
    label: 'CRITICAL',
    className: 'bg-[rgba(239,68,68,0.15)] text-[#ef4444] border border-[rgba(239,68,68,0.3)]',
  },
  warning: {
    label: 'WARNING',
    className: 'bg-[rgba(245,158,11,0.15)] text-[#f59e0b] border border-[rgba(245,158,11,0.3)]',
  },
  info: {
    label: 'INFO',
    className: 'bg-[rgba(6,182,212,0.15)] text-[#06b6d4] border border-[rgba(6,182,212,0.3)]',
  },
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  const config = SEVERITY_CONFIG[severity];
  return (
    <span className={clsx('inline-flex items-center px-1.5 py-0.5 text-xs font-mono rounded', config.className)}>
      {config.label}
    </span>
  );
}
