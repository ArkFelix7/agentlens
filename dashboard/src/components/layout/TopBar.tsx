/** Top bar with session selector and WebSocket connection status. */

import React from 'react';
import { useSessionStore } from '@/stores/sessionStore';
import { useWebSocketStore } from '@/stores/websocketStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import clsx from 'clsx';

export function TopBar() {
  const { sessions, activeSessionId, setActiveSession } = useSessionStore();
  const { status } = useWebSocketStore();
  const { requestSessionEvents } = useWebSocket();

  const handleSessionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setActiveSession(id || null);
    if (id) requestSessionEvents(id);
  };

  const isConnected = status === 'connected';

  return (
    <header className="flex items-center h-14 px-4 bg-[var(--bg-secondary)] border-b border-[var(--border-subtle)] shrink-0 gap-4">
      {/* Brand */}
      <div className="flex items-center gap-2 mr-2">
        <span className="font-mono font-semibold text-sm text-[var(--text-primary)] tracking-tight">AgentLens</span>
      </div>

      {/* Session selector */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-[var(--text-tertiary)] font-mono">Session:</span>
        <select
          value={activeSessionId || ''}
          onChange={handleSessionChange}
          className="bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded px-2 py-1
            text-xs font-mono text-[var(--text-primary)] cursor-pointer focus:outline-none focus:border-[var(--border-focus)]
            min-w-48"
          aria-label="Select session"
        >
          <option value="">No session selected</option>
          {sessions.map((s) => (
            <option key={s.id} value={s.id}>
              {s.agent_name} — {new Date(s.started_at).toLocaleTimeString()} ({s.total_events} events)
            </option>
          ))}
        </select>
      </div>

      <div className="flex-1" />

      {/* Connection status */}
      <div className="flex items-center gap-2">
        <div
          className={clsx(
            'w-2 h-2 rounded-full',
            isConnected ? 'bg-[var(--accent-emerald)] live-pulse' : 'bg-[var(--accent-red)]',
          )}
        />
        <span
          className={clsx(
            'text-xs font-mono',
            isConnected ? 'text-[var(--accent-emerald)]' : 'text-[var(--accent-red)]',
          )}
        >
          {isConnected ? 'Live' : status === 'connecting' ? 'Connecting...' : 'Disconnected'}
        </span>
      </div>
    </header>
  );
}
