/** Side-by-side diff viewer for tool output vs agent output. Uses react-diff-viewer-continued. */

import React from 'react';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';

interface DiffViewerProps {
  expected: string;
  actual: string;
}

const diffStyles = {
  variables: {
    dark: {
      diffViewerBackground: 'transparent',
      diffViewerColor: 'var(--text-primary)',
      addedBackground: 'rgba(16,185,129,0.08)',
      addedColor: 'var(--text-primary)',
      removedBackground: 'rgba(239,68,68,0.08)',
      removedColor: 'var(--text-primary)',
      wordAddedBackground: 'rgba(16,185,129,0.25)',
      wordRemovedBackground: 'rgba(239,68,68,0.25)',
      addedGutterBackground: 'rgba(16,185,129,0.12)',
      removedGutterBackground: 'rgba(239,68,68,0.12)',
      gutterBackground: 'var(--bg-secondary)',
      gutterColor: 'var(--text-tertiary)',
      codeFoldBackground: 'var(--bg-tertiary)',
      emptyLineBackground: 'var(--bg-secondary)',
    },
  },
};

export function DiffViewer({ expected, actual }: DiffViewerProps) {
  return (
    <div className="text-xs font-mono rounded overflow-hidden border border-[var(--border-subtle)]">
      <div className="grid grid-cols-2 text-[10px] font-mono text-[var(--text-tertiary)] uppercase tracking-wider px-3 py-1.5 bg-[var(--bg-tertiary)] border-b border-[var(--border-subtle)]">
        <span>Tool Output (Source of Truth)</span>
        <span>Agent Output</span>
      </div>
      <ReactDiffViewer
        oldValue={expected}
        newValue={actual}
        splitView={true}
        useDarkTheme={true}
        compareMethod={DiffMethod.WORDS}
        styles={diffStyles}
        hideLineNumbers={false}
        showDiffOnly={false}
        leftTitle=""
        rightTitle=""
      />
    </div>
  );
}
