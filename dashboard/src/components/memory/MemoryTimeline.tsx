/** Vertical timeline of memory events. */

import React from 'react';
import { format } from 'date-fns';
import { MemoryEntry, MemoryAction } from '@/types';
import clsx from 'clsx';

const ACTION_COLORS: Record<MemoryAction, string> = {
  created: '#10b981',
  updated: '#f59e0b',
  accessed: '#6366f1',
  deleted: '#ef4444',
};

interface MemoryTimelineProps {
  entries: MemoryEntry[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  searchQuery: string;
}

export function MemoryTimeline({ entries, selectedId, onSelect, searchQuery }: MemoryTimelineProps) {
  const filtered = entries.filter((e) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return e.memory_key.toLowerCase().includes(q) || e.content.toLowerCase().includes(q);
  });

  return (
    <div className="relative h-full overflow-y-auto p-4">
      <div className="absolute left-6 top-4 bottom-4 w-px bg-[var(--border-subtle)]" />
      <div className="space-y-3">
        {filtered.map((entry) => {
          const color = ACTION_COLORS[entry.action];
          const isSelected = entry.id === selectedId;
          return (
            <div
              key={entry.id}
              className={clsx(
                'relative pl-10 cursor-pointer group',
              )}
              onClick={() => onSelect(entry.id)}
            >
              <div
                className="absolute left-4 top-2 w-3 h-3 rounded-full border-2 transition-all"
                style={{ backgroundColor: `${color}30`, borderColor: color, transform: isSelected ? 'scale(1.3)' : undefined }}
              />
              <div
                className={clsx(
                  'bg-[var(--bg-secondary)] border rounded-lg p-3 transition-colors',
                  isSelected ? 'border-[var(--accent-indigo)]' : 'border-[var(--border-subtle)] group-hover:border-[var(--border-default)]',
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span
                    className="text-xs font-mono px-1.5 py-0.5 rounded border"
                    style={{ color, backgroundColor: `${color}15`, borderColor: `${color}40` }}
                  >
                    {entry.action}
                  </span>
                  <span className="text-xs text-[var(--text-tertiary)] font-mono">
                    {format(new Date(entry.timestamp), 'HH:mm:ss')}
                  </span>
                </div>
                <p className="text-sm font-mono text-[var(--text-primary)] mt-1 truncate">{entry.memory_key}</p>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5 line-clamp-2">{entry.content}</p>
              </div>
            </div>
          );
        })}
        {filtered.length === 0 && (
          <div className="pl-10 text-[var(--text-tertiary)] text-sm font-mono">
            {searchQuery ? 'No matching memories' : 'No memory entries yet'}
          </div>
        )}
      </div>
    </div>
  );
}
