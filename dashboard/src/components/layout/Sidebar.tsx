/** Left sidebar navigation with keyboard shortcut support. */

import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Activity, DollarSign, AlertTriangle, Brain, Play, Settings } from 'lucide-react';
import { useHotkeys } from 'react-hotkeys-hook';
import clsx from 'clsx';
import { Tooltip } from '@/components/shared/Tooltip';

const navItems = [
  { icon: Activity, label: 'Traces', path: '/', shortcut: '1' },
  { icon: DollarSign, label: 'Costs', path: '/costs', shortcut: '2' },
  { icon: AlertTriangle, label: 'Hallucinations', path: '/hallucinations', shortcut: '3' },
  { icon: Brain, label: 'Memory', path: '/memory', shortcut: '4' },
  { icon: Play, label: 'Replay', path: '/replay', shortcut: '5' },
];

export function Sidebar() {
  const navigate = useNavigate();

  // Keyboard shortcuts
  useHotkeys('1', () => navigate('/'));
  useHotkeys('2', () => navigate('/costs'));
  useHotkeys('3', () => navigate('/hallucinations'));
  useHotkeys('4', () => navigate('/memory'));
  useHotkeys('5', () => navigate('/replay'));
  useHotkeys(',', () => navigate('/settings'));

  return (
    <aside
      className="flex flex-col w-14 bg-[var(--bg-secondary)] border-r border-[var(--border-subtle)] h-full"
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Logo */}
      <div className="flex items-center justify-center h-14 border-b border-[var(--border-subtle)] shrink-0">
        <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="8" stroke="#6366f1" strokeWidth="2" fill="none" />
          <circle cx="16" cy="16" r="3" fill="#6366f1" />
        </svg>
      </div>

      {/* Nav items */}
      <nav className="flex flex-col items-center gap-1 py-3 flex-1">
        {navItems.map(({ icon: Icon, label, path, shortcut }) => (
          <Tooltip key={path} content={`${label} (${shortcut})`} position="right">
            <NavLink
              to={path}
              end={path === '/'}
              className={({ isActive }) =>
                clsx(
                  'w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-150',
                  isActive
                    ? 'bg-[rgba(99,102,241,0.15)] text-[var(--accent-indigo)]'
                    : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]',
                )
              }
              aria-label={label}
            >
              <Icon size={18} />
            </NavLink>
          </Tooltip>
        ))}
      </nav>

      {/* Settings at bottom */}
      <div className="flex flex-col items-center py-3 border-t border-[var(--border-subtle)]">
        <Tooltip content="Settings (,)" position="right">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              clsx(
                'w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-150',
                isActive
                  ? 'bg-[rgba(99,102,241,0.15)] text-[var(--accent-indigo)]'
                  : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]',
              )
            }
            aria-label="Settings"
          >
            <Settings size={18} />
          </NavLink>
        </Tooltip>
      </div>
    </aside>
  );
}
