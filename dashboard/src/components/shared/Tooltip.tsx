/** Simple tooltip component. */

import React, { useState } from 'react';
import clsx from 'clsx';

interface TooltipProps {
  content: string;
  children: React.ReactElement;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function Tooltip({ content, children, position = 'top' }: TooltipProps) {
  const [visible, setVisible] = useState(false);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-1',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-1',
    left: 'right-full top-1/2 -translate-y-1/2 mr-1',
    right: 'left-full top-1/2 -translate-y-1/2 ml-1',
  };

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          className={clsx(
            'absolute z-50 px-2 py-1 text-xs font-mono whitespace-nowrap pointer-events-none',
            'bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-[var(--text-primary)]',
            'shadow-[var(--shadow-md)]',
            positionClasses[position],
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
}
