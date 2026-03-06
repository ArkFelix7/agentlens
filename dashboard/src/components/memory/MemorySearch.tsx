/** Search/filter input for memories. */

import React from 'react';
import { Search } from 'lucide-react';

interface MemorySearchProps {
  value: string;
  onChange: (v: string) => void;
}

export function MemorySearch({ value, onChange }: MemorySearchProps) {
  return (
    <div className="relative">
      <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
      <input
        type="text"
        placeholder="Search memories..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded px-3 py-2 pl-8
          text-sm font-mono text-[var(--text-primary)] placeholder-[var(--text-tertiary)]
          focus:outline-none focus:border-[var(--border-focus)]"
      />
    </div>
  );
}
