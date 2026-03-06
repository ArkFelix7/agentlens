/** Collapsible JSON tree viewer using react-json-view-lite. */

import React from 'react';
import { JsonView, allExpanded, defaultStyles } from 'react-json-view-lite';
import 'react-json-view-lite/dist/index.css';

interface JsonViewerProps {
  data: unknown;
  initialExpanded?: boolean;
  maxDepth?: number;
}

export function JsonViewer({ data, initialExpanded = false, maxDepth = 3 }: JsonViewerProps) {
  if (data === null || data === undefined) {
    return <span className="text-[var(--text-tertiary)] text-xs font-mono">null</span>;
  }

  if (typeof data === 'string') {
    try {
      const parsed = JSON.parse(data);
      return <JsonViewerInner data={parsed} initialExpanded={initialExpanded} />;
    } catch {
      return <span className="text-xs font-mono text-[var(--text-primary)] break-all">{data}</span>;
    }
  }

  return <JsonViewerInner data={data} initialExpanded={initialExpanded} />;
}

function JsonViewerInner({ data, initialExpanded }: { data: unknown; initialExpanded: boolean }) {
  return (
    <div className="json-viewer text-xs">
      <JsonView
        data={data as object}
        shouldExpandNode={initialExpanded ? allExpanded : () => false}
        style={{
          ...defaultStyles,
          container: 'bg-transparent font-mono text-xs',
          stringValue: 'text-[#10b981]',
          numberValue: 'text-[#f59e0b]',
          booleanValue: 'text-[#6366f1]',
          nullValue: 'text-[var(--text-tertiary)]',
          label: 'text-[var(--text-secondary)]',
          expandIcon: 'text-[var(--text-tertiary)] cursor-pointer',
          collapseIcon: 'text-[var(--text-tertiary)] cursor-pointer',
        }}
      />
    </div>
  );
}
