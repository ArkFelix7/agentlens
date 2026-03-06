/** Expanded view of a selected memory entry with version history. */

import React from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { MemoryEntry } from '@/types';

interface MemoryDetailProps {
  entry: MemoryEntry | null;
  history?: MemoryEntry[];
}

export function MemoryDetail({ entry, history = [] }: MemoryDetailProps) {
  if (!entry) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--text-tertiary)] text-sm font-mono">
        Select a memory entry to see details
      </div>
    );
  }

  return (
    <motion.div
      key={entry.id}
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2 }}
      className="h-full overflow-y-auto p-4 space-y-4"
    >
      <div>
        <p className="text-xs text-[var(--text-tertiary)] font-mono mb-1">Memory Key</p>
        <p className="text-sm font-mono font-semibold text-[var(--text-primary)]">{entry.memory_key}</p>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-[var(--bg-tertiary)] rounded p-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Created / Updated</p>
          <p className="text-[var(--text-primary)] font-mono">{format(new Date(entry.timestamp), 'MMM d, HH:mm:ss')}</p>
        </div>
        <div className="bg-[var(--bg-tertiary)] rounded p-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Version</p>
          <p className="text-[var(--text-primary)] font-mono">v{entry.version}</p>
        </div>
        <div className="bg-[var(--bg-tertiary)] rounded p-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Action</p>
          <p className="text-[var(--accent-cyan)] font-mono">{entry.action}</p>
        </div>
        <div className="bg-[var(--bg-tertiary)] rounded p-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Agent</p>
          <p className="text-[var(--text-primary)] font-mono">{entry.agent_id}</p>
        </div>
      </div>

      <div>
        <p className="text-xs text-[var(--text-tertiary)] font-mono mb-2">CONTENT</p>
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded p-3 text-sm text-[var(--text-primary)]">
          {entry.content}
        </div>
      </div>

      {entry.influenced_events && entry.influenced_events.length > 0 && (
        <div>
          <p className="text-xs text-[var(--text-tertiary)] font-mono mb-2">INFLUENCE MAP</p>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded p-3 space-y-1">
            <p className="text-xs text-[var(--text-secondary)]">
              This memory influenced {entry.influenced_events.length} event(s):
            </p>
            {entry.influenced_events.map((id) => (
              <p key={id} className="text-xs font-mono text-[var(--accent-indigo)]">• {id.slice(-12)}</p>
            ))}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div>
          <p className="text-xs text-[var(--text-tertiary)] font-mono mb-2">VERSION HISTORY</p>
          <div className="space-y-2">
            {history.map((h) => (
              <div key={h.id} className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded p-2 text-xs">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-mono text-[var(--text-tertiary)]">v{h.version}</span>
                  <span className="font-mono text-[var(--text-tertiary)]">{format(new Date(h.timestamp), 'HH:mm:ss')}</span>
                </div>
                <p className="text-[var(--text-secondary)] line-clamp-2">{h.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
