/** Session replay page — step through past agent runs frame by frame. */

import React, { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { useHotkeys } from 'react-hotkeys-hook';
import { Link, FlaskConical } from 'lucide-react';
import { useSessionStore } from '@/stores/sessionStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { TraceEvent } from '@/types';
import { useReplay } from '@/hooks/useReplay';
import { useTraceGraph } from '@/hooks/useTraceGraph';
import { TraceGraph } from '@/components/traces/TraceGraph';
import { ReplayPlayer } from '@/components/replay/ReplayPlayer';
import { ReplayTimeline } from '@/components/replay/ReplayTimeline';
import { ReplayState } from '@/components/replay/ReplayState';
import { EmptyState } from '@/components/shared/EmptyState';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';

export function ReplayPage() {
  const { sessions, activeSessionId, setActiveSession } = useSessionStore();
  const { apiUrl } = useSettingsStore();
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const [copyLabel, setCopyLabel] = useState('Copy link');
  const [saveTestLabel, setSaveTestLabel] = useState('Save as Test');
  const [generatedTest, setGeneratedTest] = useState<string | null>(null);

  // Auto-select session from URL param on mount
  useEffect(() => {
    const sessionParam = searchParams.get('session');
    if (sessionParam && sessionParam !== activeSessionId) {
      setActiveSession(sessionParam);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Keep URL in sync with active session
  useEffect(() => {
    if (activeSessionId) {
      setSearchParams({ session: activeSessionId }, { replace: true });
    }
  }, [activeSessionId, setSearchParams]);

  const saveAsTest = useCallback(async () => {
    if (!activeSessionId) return;
    setSaveTestLabel('Generating...');
    try {
      const resp = await fetch(`${apiUrl}/api/v1/testgen/${activeSessionId}`, { method: 'POST' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setGeneratedTest(data.test_code ?? JSON.stringify(data, null, 2));
      setSaveTestLabel('Saved!');
    } catch {
      setSaveTestLabel('Failed');
    } finally {
      setTimeout(() => setSaveTestLabel('Save as Test'), 3000);
    }
  }, [activeSessionId, apiUrl]);

  const copyShareLink = useCallback(() => {
    const url = new URL(window.location.href);
    if (activeSessionId) url.searchParams.set('session', activeSessionId);
    navigator.clipboard.writeText(url.toString()).then(() => {
      setCopyLabel('Copied!');
      setTimeout(() => setCopyLabel('Copy link'), 2000);
    });
  }, [activeSessionId]);

  const { data, isLoading } = useQuery<{ events: TraceEvent[] }>({
    queryKey: ['replay', activeSessionId],
    queryFn: async () => {
      const resp = await fetch(`${apiUrl}/api/v1/traces/${activeSessionId}`);
      return resp.json();
    },
    enabled: !!activeSessionId,
  });

  const allEvents = data?.events || [];
  const controls = useReplay(allEvents);
  const graphData = useTraceGraph(controls.visibleEvents);

  // Keyboard shortcuts
  useHotkeys('space', (e) => { e.preventDefault(); controls.isPlaying ? controls.pause() : controls.play(); });
  useHotkeys('left', () => controls.stepBack());
  useHotkeys('right', () => controls.stepForward());
  useHotkeys('home', () => controls.jumpToStart());
  useHotkeys('end', () => controls.jumpToEnd());

  const currentEvent = controls.visibleEvents[controls.visibleEvents.length - 1] || null;

  if (!activeSessionId) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4 p-8">
        <EmptyState title="Select a session to replay" description="Choose a session from the dropdown to step through it." showSetup={false} />
        {sessions.length > 0 && (
          <select
            onChange={(e) => setActiveSession(e.target.value || null)}
            className="bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded px-3 py-2 text-sm font-mono text-[var(--text-primary)] focus:outline-none"
          >
            <option value="">Select a session...</option>
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.agent_name} — {s.total_events} events — ${s.total_cost_usd.toFixed(4)}
              </option>
            ))}
          </select>
        )}
      </div>
    );
  }

  // Session is selected but still loading data
  if (!activeSessionId) return null;

  if (isLoading) {
    return <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar: save as test + share link */}
      <div className="flex items-center justify-end gap-3 px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <button
          onClick={saveAsTest}
          className="flex items-center gap-1.5 text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--accent-indigo)] transition-colors"
        >
          <FlaskConical size={12} />
          {saveTestLabel}
        </button>
        <button
          onClick={copyShareLink}
          className="flex items-center gap-1.5 text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
        >
          <Link size={12} />
          {copyLabel}
        </button>
      </div>

      {/* Generated test code modal */}
      {generatedTest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg w-[600px] max-h-[80vh] flex flex-col shadow-2xl">
            <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-subtle)]">
              <span className="text-sm font-mono font-semibold text-[var(--text-primary)]">Generated Test</span>
              <div className="flex gap-2">
                <button
                  onClick={() => navigator.clipboard.writeText(generatedTest)}
                  className="text-xs font-mono text-[var(--accent-indigo)] hover:opacity-80"
                >
                  Copy
                </button>
                <button
                  onClick={() => setGeneratedTest(null)}
                  className="text-xs font-mono text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
                >
                  Close
                </button>
              </div>
            </div>
            <pre className="flex-1 overflow-auto p-4 text-xs font-mono text-[var(--text-secondary)] whitespace-pre-wrap">
              {generatedTest}
            </pre>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 min-h-0">
        {/* Center: Graph */}
        <div className="flex-1 min-w-0 border-r border-[var(--border-subtle)]">
          {controls.visibleEvents.length === 0 ? (
            <div className="flex items-center justify-center h-full text-[var(--text-tertiary)] text-sm font-mono">
              Press Play to start replay
            </div>
          ) : (
            <TraceGraph
              graphData={graphData}
              selectedEventId={selectedEventId}
              onSelectEvent={setSelectedEventId}
            />
          )}
        </div>

        {/* Right: State panel */}
        <div className="w-72 shrink-0">
          <ReplayState
            currentEvent={selectedEventId ? (controls.visibleEvents.find((e) => e.id === selectedEventId) || currentEvent) : currentEvent}
            visibleEvents={controls.visibleEvents}
          />
        </div>
      </div>

      {/* Step timeline */}
      <div className="border-t border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <ReplayTimeline
          events={allEvents}
          currentStep={controls.currentStep}
          onSeek={controls.seekTo}
        />
        <ReplayPlayer controls={controls} />
      </div>
    </div>
  );
}
