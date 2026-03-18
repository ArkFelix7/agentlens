/** Settings page — server URL, theme, auto-connect, retention, shortcuts. */

import React from 'react';
import { useSettingsStore } from '@/stores/settingsStore';
import { Github, ExternalLink } from 'lucide-react';

const KEYBOARD_SHORTCUTS = [
  { key: '1', action: 'Navigate to Traces' },
  { key: '2', action: 'Navigate to Costs' },
  { key: '3', action: 'Navigate to Hallucinations' },
  { key: '4', action: 'Navigate to Memory' },
  { key: '5', action: 'Navigate to Replay' },
  { key: ',', action: 'Navigate to Settings' },
  { key: 'Space', action: 'Play / Pause replay' },
  { key: '← →', action: 'Step back / forward in replay' },
  { key: 'Home / End', action: 'Jump to start / end of replay' },
];

export function SettingsPage() {
  const { wsUrl, apiUrl, theme, autoConnect, traceRetention, setWsUrl, setApiUrl, setTheme, setAutoConnect, setTraceRetention } = useSettingsStore();

  return (
    <div className="h-full overflow-y-auto p-6 max-w-2xl space-y-6">
      <h1 className="text-lg font-mono font-semibold text-[var(--text-primary)]">Settings</h1>

      {/* Server connection */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4 space-y-4">
        <h2 className="text-sm font-mono font-medium text-[var(--text-primary)]">Server Connection</h2>
        <div className="space-y-3">
          <div>
            <label className="text-xs font-mono text-[var(--text-tertiary)] block mb-1">WebSocket URL</label>
            <input
              type="text"
              value={wsUrl}
              onChange={(e) => setWsUrl(e.target.value)}
              className="w-full bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded px-3 py-1.5
                text-sm font-mono text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-focus)]"
            />
          </div>
          <div>
            <label className="text-xs font-mono text-[var(--text-tertiary)] block mb-1">REST API URL</label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded px-3 py-1.5
                text-sm font-mono text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-focus)]"
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-mono text-[var(--text-primary)]">Auto-reconnect</label>
            <button
              onClick={() => setAutoConnect(!autoConnect)}
              className={`w-10 h-5 rounded-full transition-colors ${autoConnect ? 'bg-[var(--accent-indigo)]' : 'bg-[var(--border-default)]'}`}
              role="switch"
              aria-checked={autoConnect}
            >
              <div className={`w-4 h-4 rounded-full bg-white shadow mx-0.5 transition-transform ${autoConnect ? 'translate-x-5' : 'translate-x-0'}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Theme */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4">
        <h2 className="text-sm font-mono font-medium text-[var(--text-primary)] mb-3">Theme</h2>
        <div className="flex gap-2">
          {(['dark', 'light'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTheme(t)}
              className={`px-4 py-2 text-sm font-mono rounded border transition-colors ${
                theme === t
                  ? 'bg-[var(--accent-indigo)] border-[var(--accent-indigo)] text-white'
                  : 'border-[var(--border-subtle)] text-[var(--text-secondary)] hover:border-[var(--border-default)]'
              }`}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Trace retention */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4">
        <h2 className="text-sm font-mono font-medium text-[var(--text-primary)] mb-3">Trace Retention</h2>
        <select
          value={traceRetention}
          onChange={(e) => setTraceRetention(e.target.value as 10 | 50 | 100 | 'all')}
          className="bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded px-3 py-1.5
            text-sm font-mono text-[var(--text-primary)] focus:outline-none"
        >
          <option value={10}>Keep last 10 sessions</option>
          <option value={50}>Keep last 50 sessions</option>
          <option value={100}>Keep last 100 sessions</option>
          <option value="all">Keep all sessions</option>
        </select>
      </div>

      {/* Keyboard shortcuts */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4">
        <h2 className="text-sm font-mono font-medium text-[var(--text-primary)] mb-3">Keyboard Shortcuts</h2>
        <table className="w-full text-xs font-mono">
          <tbody className="divide-y divide-[var(--border-subtle)]">
            {KEYBOARD_SHORTCUTS.map(({ key, action }) => (
              <tr key={key}>
                <td className="py-1.5 pr-4">
                  <kbd className="px-1.5 py-0.5 bg-[var(--bg-tertiary)] border border-[var(--border-default)] rounded text-[var(--text-primary)]">
                    {key}
                  </kbd>
                </td>
                <td className="py-1.5 text-[var(--text-secondary)]">{action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Privacy & Data */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4 space-y-3">
        <h2 className="text-sm font-mono font-medium text-[var(--text-primary)]">Privacy &amp; Data</h2>
        <div className="text-xs font-mono text-[var(--text-secondary)]">
          Storage: Local SQLite database · No cloud sync · No telemetry
        </div>
        <button
          onClick={() => {
            fetch('/api/v1/privacy/certificate')
              .then((res) => res.json())
              .then((data) => {
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
                a.href = url;
                a.download = `agentlens-data-residency-${date}.json`;
                a.click();
                URL.revokeObjectURL(url);
              })
              .catch(() => {});
          }}
          className="px-3 py-1.5 text-xs font-mono rounded border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:border-[var(--border-default)] hover:text-[var(--text-primary)] transition-colors"
        >
          Download Data Residency Certificate
        </button>
        <p className="text-xs text-[var(--text-tertiary)]">
          All trace data is stored in a local SQLite database on this machine. No data is ever transmitted to external servers.
        </p>
      </div>

      {/* About */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4 space-y-2">
        <h2 className="text-sm font-mono font-medium text-[var(--text-primary)]">About</h2>
        <p className="text-xs text-[var(--text-secondary)] font-mono">AgentLens v0.1.0</p>
        <p className="text-xs text-[var(--text-secondary)]">Real-time observability dashboard for AI agents.</p>
        <p className="text-xs text-[var(--text-tertiary)]">MIT License • Open Source</p>
        <div className="flex gap-3 pt-1">
          <a
            href="https://github.com/agentlens/agentlens"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-[var(--accent-indigo)] hover:underline"
          >
            <Github size={12} /> GitHub
          </a>
        </div>
      </div>
    </div>
  );
}
