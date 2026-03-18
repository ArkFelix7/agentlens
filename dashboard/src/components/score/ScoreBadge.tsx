/** Inline reliability score badge — shows grade letter + numeric score. */

import React from 'react';
import { ScoreResult } from '@/types';

interface ScoreBadgeProps {
  score: ScoreResult;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const SIZE_CLASSES = {
  sm: { outer: 'w-8 h-8 text-xs', label: 'text-xs' },
  md: { outer: 'w-12 h-12 text-sm', label: 'text-sm' },
  lg: { outer: 'w-16 h-16 text-lg', label: 'text-base' },
};

export function ScoreBadge({ score, size = 'md', showLabel = true }: ScoreBadgeProps) {
  const cls = SIZE_CLASSES[size];
  const gradeColors: Record<string, string> = {
    A: '#22c55e',
    B: '#84cc16',
    C: '#f59e0b',
    D: '#ef4444',
  };
  const color = gradeColors[score.grade] ?? score.color ?? '#6366f1';

  return (
    <div className="flex items-center gap-2">
      <div
        className={`${cls.outer} rounded-full flex items-center justify-center font-mono font-bold border-2`}
        style={{ borderColor: color, color }}
        title={`Score: ${score.score}/100`}
      >
        {score.grade}
      </div>
      {showLabel && (
        <div className="flex flex-col">
          <span className={`${cls.label} font-mono font-semibold`} style={{ color }}>
            {score.score}/100
          </span>
          <span className="text-[10px] text-[var(--text-tertiary)] font-mono">reliability</span>
        </div>
      )}
    </div>
  );
}
