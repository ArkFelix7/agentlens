/** Event type badge with color coding for each event type. */

import React from 'react';
import { EventType, EventStatus } from '@/types';
import clsx from 'clsx';

const EVENT_COLORS: Record<EventType, string> = {
  llm_call: 'bg-[rgba(168,85,247,0.15)] text-[#a855f7] border-[rgba(168,85,247,0.3)]',
  tool_call: 'bg-[rgba(6,182,212,0.15)] text-[#06b6d4] border-[rgba(6,182,212,0.3)]',
  decision: 'bg-[rgba(245,158,11,0.15)] text-[#f59e0b] border-[rgba(245,158,11,0.3)]',
  memory_read: 'bg-[rgba(99,102,241,0.15)] text-[#6366f1] border-[rgba(99,102,241,0.3)]',
  memory_write: 'bg-[rgba(99,102,241,0.15)] text-[#6366f1] border-[rgba(99,102,241,0.3)]',
  user_input: 'bg-[rgba(16,185,129,0.15)] text-[#10b981] border-[rgba(16,185,129,0.3)]',
  error: 'bg-[rgba(239,68,68,0.15)] text-[#ef4444] border-[rgba(239,68,68,0.3)]',
};

interface EventBadgeProps {
  eventType: EventType;
  status?: EventStatus;
  className?: string;
}

export function EventBadge({ eventType, status, className }: EventBadgeProps) {
  const label = eventType.replace(/_/g, ' ');
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-mono rounded border',
        EVENT_COLORS[eventType],
        className,
      )}
    >
      {label}
      {status === 'error' && <span className="text-[var(--accent-red)]">✗</span>}
      {status === 'success' && <span className="opacity-60">✓</span>}
    </span>
  );
}
