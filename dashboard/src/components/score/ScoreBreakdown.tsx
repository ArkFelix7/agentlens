/** Penalty bar chart showing what reduced the reliability score. */

import React from 'react';
import { ScoreResult } from '@/types';

interface ScoreBreakdownProps {
  score: ScoreResult;
}

const PENALTY_LABELS: Record<string, string> = {
  hallucination_penalty: 'Hallucinations',
  error_penalty: 'Errors',
  latency_penalty: 'High Latency',
  cost_penalty: 'High Cost',
};

export function ScoreBreakdown({ score }: ScoreBreakdownProps) {
  const penalties = Object.entries(score.penalty_breakdown)
    .filter(([, v]) => v > 0)
    .sort(([, a], [, b]) => b - a);

  if (penalties.length === 0) {
    return (
      <p className="text-xs text-[var(--text-tertiary)] font-mono py-2">
        No penalties — perfect score!
      </p>
    );
  }

  const maxPenalty = Math.max(...penalties.map(([, v]) => v));

  return (
    <div className="space-y-2">
      {penalties.map(([key, value]) => (
        <div key={key} className="flex items-center gap-2">
          <span className="text-xs text-[var(--text-secondary)] font-mono w-36 shrink-0">
            {PENALTY_LABELS[key] ?? key.replace(/_/g, ' ')}
          </span>
          <div className="flex-1 bg-[var(--bg-tertiary)] rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full rounded-full bg-[#ef4444] transition-all duration-500"
              style={{ width: `${(value / maxPenalty) * 100}%` }}
            />
          </div>
          <span className="text-xs text-[#ef4444] font-mono w-10 text-right shrink-0">
            -{value}
          </span>
        </div>
      ))}
      <div className="flex items-center gap-2 pt-1 border-t border-[var(--border-subtle)]">
        <span className="text-xs text-[var(--text-secondary)] font-mono w-36 shrink-0">Base score</span>
        <div className="flex-1" />
        <span className="text-xs text-[var(--text-primary)] font-mono w-10 text-right shrink-0">100</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-[var(--text-primary)] font-mono w-36 shrink-0">Final score</span>
        <div className="flex-1" />
        <span
          className="text-xs font-bold font-mono w-10 text-right shrink-0"
          style={{ color: score.color }}
        >
          {score.score}
        </span>
      </div>
    </div>
  );
}
