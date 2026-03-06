/** Table of most expensive steps with optimization tips. */

import React from 'react';
import { CostHotspot, CostSuggestion } from '@/types';
import clsx from 'clsx';

interface CostHotspotsProps {
  hotspots: CostHotspot[];
  suggestions: CostSuggestion[];
}

export function CostHotspots({ hotspots, suggestions }: CostHotspotsProps) {
  const suggestionMap = new Map(suggestions.map((s) => [s.event_id, s]));

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-[var(--border-subtle)]">
            <th className="text-left py-2 pr-4 text-[var(--text-tertiary)]">Step</th>
            <th className="text-left py-2 pr-4 text-[var(--text-tertiary)]">Model</th>
            <th className="text-right py-2 pr-4 text-[var(--text-tertiary)]">Tokens</th>
            <th className="text-right py-2 pr-4 text-[var(--text-tertiary)]">Cost</th>
            <th className="text-right py-2 pr-4 text-[var(--text-tertiary)]">%</th>
            <th className="text-left py-2 text-[var(--text-tertiary)]">Tip</th>
          </tr>
        </thead>
        <tbody>
          {hotspots.map((h, i) => {
            const suggestion = suggestionMap.get(h.event_id);
            return (
              <tr
                key={h.event_id}
                className={clsx(
                  'border-b border-[var(--border-subtle)] hover:bg-[var(--bg-tertiary)]',
                  i < 3 && 'bg-[rgba(245,158,11,0.04)]',
                )}
              >
                <td className="py-2 pr-4 text-[var(--text-primary)] max-w-32 truncate">{h.event_name}</td>
                <td className="py-2 pr-4 text-[var(--text-secondary)]">{h.model || '—'}</td>
                <td className="py-2 pr-4 text-right text-[var(--text-secondary)]">
                  {(h.tokens_input + h.tokens_output).toLocaleString()}
                </td>
                <td className="py-2 pr-4 text-right text-[var(--accent-emerald)]">${h.cost_usd.toFixed(6)}</td>
                <td className="py-2 pr-4 text-right text-[var(--text-tertiary)]">{h.percentage_of_total.toFixed(1)}%</td>
                <td className="py-2 text-[var(--accent-amber)] max-w-48">
                  {suggestion ? (
                    <span title={suggestion.reason}>
                      → {suggestion.suggested_model}
                    </span>
                  ) : '—'}
                </td>
              </tr>
            );
          })}
          {hotspots.length === 0 && (
            <tr>
              <td colSpan={6} className="py-4 text-center text-[var(--text-tertiary)]">No cost data</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
