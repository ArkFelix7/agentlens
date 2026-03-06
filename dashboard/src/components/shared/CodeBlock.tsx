/** Syntax-highlighted code display component. */

import React from 'react';
import clsx from 'clsx';

interface CodeBlockProps {
  code: string;
  language?: string;
  className?: string;
}

export function CodeBlock({ code, language = 'text', className }: CodeBlockProps) {
  return (
    <pre
      className={clsx(
        'bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded p-3 overflow-x-auto',
        'text-xs font-mono text-[var(--text-primary)] leading-relaxed',
        className,
      )}
    >
      <code>{code}</code>
    </pre>
  );
}
