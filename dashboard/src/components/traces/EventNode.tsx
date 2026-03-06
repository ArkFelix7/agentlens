/** Individual event node component for use in graph and timeline views. */

import React from 'react';
import { TraceEvent, EventType } from '@/types';
import clsx from 'clsx';

const EVENT_COLORS: Record<EventType, string> = {
  llm_call: '#a855f7',
  tool_call: '#06b6d4',
  decision: '#f59e0b',
  memory_read: '#6366f1',
  memory_write: '#6366f1',
  user_input: '#10b981',
  error: '#ef4444',
};

interface EventNodeProps {
  event: TraceEvent;
  isSelected?: boolean;
  onClick?: () => void;
  size?: 'sm' | 'md' | 'lg';
}

export function EventNode({ event, isSelected, onClick, size = 'md' }: EventNodeProps) {
  const color = EVENT_COLORS[event.event_type] || '#6b6b80';
  const sizeClasses = { sm: 'w-8 h-8 text-xs', md: 'w-10 h-10 text-xs', lg: 'w-12 h-12 text-sm' };

  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex items-center justify-center rounded-full border-2 font-mono font-medium transition-all duration-150',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        sizeClasses[size],
        isSelected ? 'scale-110' : 'hover:scale-105',
      )}
      style={{
        backgroundColor: `${color}20`,
        borderColor: color,
        color,
        boxShadow: isSelected ? `0 0 12px ${color}60` : undefined,
      }}
      aria-label={`${event.event_type}: ${event.event_name}`}
      title={event.event_name}
    >
      {event.event_name.slice(0, 2).toUpperCase()}
    </button>
  );
}
