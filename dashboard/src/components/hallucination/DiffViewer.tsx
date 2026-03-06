/** Side-by-side diff viewer for tool output vs agent output. */

import React from 'react';

interface DiffViewerProps {
  expected: string;
  actual: string;
}

export function DiffViewer({ expected, actual }: DiffViewerProps) {
  return (
    <div className="grid grid-cols-2 gap-3 text-xs font-mono">
      <div>
        <p className="text-[var(--text-tertiary)] mb-2 text-xs uppercase tracking-wider">Tool Output (Source of Truth)</p>
        <div className="bg-[rgba(16,185,129,0.05)] border border-[rgba(16,185,129,0.2)] rounded p-3 whitespace-pre-wrap break-all text-[var(--text-primary)]">
          {expected}
        </div>
      </div>
      <div>
        <p className="text-[var(--text-tertiary)] mb-2 text-xs uppercase tracking-wider">Agent Output</p>
        <div className="bg-[rgba(239,68,68,0.05)] border border-[rgba(239,68,68,0.2)] rounded p-3 whitespace-pre-wrap break-all text-[var(--text-primary)]">
          {actual}
        </div>
      </div>
    </div>
  );
}
