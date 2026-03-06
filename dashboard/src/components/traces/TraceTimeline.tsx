/** Horizontal timeline view of trace events (alternate to graph view). */

import React from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { TraceEvent, EventType } from '@/types';
import { EventBadge } from './EventBadge';
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

interface TraceTimelineProps {
  events: TraceEvent[];
  selectedEventId: string | null;
  onSelectEvent: (id: string) => void;
}

export function TraceTimeline({ events, selectedEventId, onSelectEvent }: TraceTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--text-tertiary)] text-sm font-mono">
        No events yet
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-5 top-0 bottom-0 w-px bg-[var(--border-subtle)]" />

        <div className="space-y-3">
          {events.map((event, i) => {
            const color = EVENT_COLORS[event.event_type] || '#6b6b80';
            const isSelected = event.id === selectedEventId;

            return (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03, duration: 0.15 }}
                className={clsx(
                  'relative pl-12 cursor-pointer group',
                )}
                onClick={() => onSelectEvent(event.id)}
              >
                {/* Node dot */}
                <div
                  className="absolute left-3.5 top-3 w-3 h-3 rounded-full border-2 transition-all duration-150"
                  style={{
                    backgroundColor: `${color}30`,
                    borderColor: color,
                    boxShadow: isSelected ? `0 0 8px ${color}60` : undefined,
                    transform: isSelected ? 'scale(1.3)' : undefined,
                  }}
                />

                {/* Event card */}
                <div
                  className={clsx(
                    'bg-[var(--bg-secondary)] border rounded-lg p-3 transition-all duration-150',
                    isSelected
                      ? 'border-[var(--accent-indigo)] shadow-[var(--shadow-sm)]'
                      : 'border-[var(--border-subtle)] group-hover:border-[var(--border-default)]',
                  )}
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <EventBadge eventType={event.event_type} status={event.status} />
                    <span className="text-xs text-[var(--text-tertiary)] font-mono">
                      {format(new Date(event.timestamp), 'HH:mm:ss.SSS')}
                    </span>
                  </div>
                  <p className="text-sm text-[var(--text-primary)] font-mono truncate">{event.event_name}</p>
                  {(event.model || event.cost_usd > 0) && (
                    <div className="flex gap-3 mt-1 text-xs text-[var(--text-tertiary)] font-mono">
                      {event.model && <span>{event.model}</span>}
                      {event.cost_usd > 0 && (
                        <span className="text-[var(--accent-emerald)]">${event.cost_usd.toFixed(6)}</span>
                      )}
                      {event.duration_ms > 0 && <span>{event.duration_ms.toFixed(0)}ms</span>}
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
