/** State snapshot at the current replay step — shows cumulative stats. */

import React from 'react';
import { TraceEvent } from '@/types';
import { TraceDetail } from '@/components/traces/TraceDetail';

interface ReplayStateProps {
  currentEvent: TraceEvent | null;
  visibleEvents: TraceEvent[];
}

export function ReplayState({ currentEvent, visibleEvents }: ReplayStateProps) {
  const totalCost = visibleEvents.reduce((s, e) => s + (e.cost_usd || 0), 0);
  const totalTokens = visibleEvents.reduce((s, e) => s + e.tokens_input + e.tokens_output, 0);
  const errorCount = visibleEvents.filter((e) => e.status === 'error').length;

  return (
    <div className="h-full flex flex-col">
      {/* Cumulative stats */}
      <div className="flex gap-3 p-3 bg-[var(--bg-secondary)] border-b border-[var(--border-subtle)] text-xs font-mono">
        <span className="text-[var(--text-tertiary)]">Cost so far: <span className="text-[var(--accent-emerald)]">${totalCost.toFixed(6)}</span></span>
        <span className="text-[var(--text-tertiary)]">Tokens: <span className="text-[var(--text-primary)]">{totalTokens.toLocaleString()}</span></span>
        {errorCount > 0 && (
          <span className="text-[var(--text-tertiary)]">Errors: <span className="text-[var(--accent-red)]">{errorCount}</span></span>
        )}
      </div>

      {/* Current event detail */}
      <div className="flex-1 overflow-hidden">
        <TraceDetail event={currentEvent} />
      </div>
    </div>
  );
}
