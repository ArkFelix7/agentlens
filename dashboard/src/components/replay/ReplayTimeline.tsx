/** Scrubber timeline bar showing all steps in a replay. */

import React from 'react';
import { TraceEvent, EventType } from '@/types';

const EVENT_COLORS: Record<EventType, string> = {
  llm_call: '#a855f7',
  tool_call: '#06b6d4',
  decision: '#f59e0b',
  memory_read: '#6366f1',
  memory_write: '#6366f1',
  user_input: '#10b981',
  error: '#ef4444',
};

interface ReplayTimelineProps {
  events: TraceEvent[];
  currentStep: number;
  onSeek: (step: number) => void;
}

export function ReplayTimeline({ events, currentStep, onSeek }: ReplayTimelineProps) {
  return (
    <div className="flex items-center gap-1 px-4 py-2 overflow-x-auto">
      {events.map((event, i) => {
        const color = EVENT_COLORS[event.event_type] || '#6b6b80';
        const isPast = i < currentStep;
        const isCurrent = i === currentStep - 1;

        return (
          <button
            key={event.id}
            onClick={() => onSeek(i + 1)}
            className="w-3 h-3 rounded-sm shrink-0 transition-all"
            style={{
              backgroundColor: isPast ? color : `${color}30`,
              borderColor: isCurrent ? color : 'transparent',
              border: isCurrent ? `2px solid ${color}` : undefined,
              transform: isCurrent ? 'scale(1.5)' : undefined,
            }}
            title={event.event_name}
          />
        );
      })}
    </div>
  );
}
