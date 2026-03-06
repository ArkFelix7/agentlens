/** Shows which memories influenced a decision. */

import React from 'react';
import { MemoryEntry } from '@/types';

interface MemoryInfluenceProps {
  entry: MemoryEntry;
}

export function MemoryInfluence({ entry }: MemoryInfluenceProps) {
  if (!entry.influenced_events || entry.influenced_events.length === 0) {
    return <p className="text-xs text-[var(--text-tertiary)] font-mono">No influenced events recorded.</p>;
  }

  return (
    <div className="space-y-1">
      {entry.influenced_events.map((id) => (
        <div key={id} className="text-xs font-mono text-[var(--accent-indigo)] flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-indigo)]" />
          {id}
        </div>
      ))}
    </div>
  );
}
