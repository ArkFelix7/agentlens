/** Hallucinations page — detect and display factual mismatches. */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSessionStore } from '@/stores/sessionStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { HallucinationAlert, HallucinationSummary, Severity } from '@/types';
import { HallucinationPanel } from '@/components/hallucination/HallucinationPanel';
import { SeverityBadge } from '@/components/hallucination/SeverityBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import clsx from 'clsx';

type Filter = 'all' | Severity;

export function HallucinationsPage() {
  const { activeSessionId } = useSessionStore();
  const { apiUrl } = useSettingsStore();
  const [severityFilter, setSeverityFilter] = useState<Filter>('all');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<{ alerts: HallucinationAlert[]; summary: HallucinationSummary }>({
    queryKey: ['hallucinations', activeSessionId],
    queryFn: async () => {
      const resp = await fetch(`${apiUrl}/api/v1/hallucinations/${activeSessionId}`);
      return resp.json();
    },
    enabled: !!activeSessionId,
  });

  const checkMutation = useMutation({
    mutationFn: async () => {
      const resp = await fetch(`${apiUrl}/api/v1/hallucinations/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: activeSessionId }),
      });
      return resp.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hallucinations', activeSessionId] });
    },
  });

  if (!activeSessionId) {
    return <EmptyState title="No session selected" description="Select a session to check for hallucinations." showSetup={false} />;
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>;
  }

  const alerts = data?.alerts || [];
  const summary = data?.summary || { total: 0, critical: 0, warning: 0, info: 0 };
  const filteredAlerts = severityFilter === 'all' ? alerts : alerts.filter((a) => a.severity === severityFilter);

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-mono font-semibold text-[var(--text-primary)]">Hallucination Detection</h1>
        <button
          onClick={() => checkMutation.mutate()}
          disabled={checkMutation.isPending}
          className="px-3 py-1.5 text-xs font-mono bg-[var(--accent-indigo)] hover:bg-[var(--accent-indigo-hover)] text-white rounded transition-colors disabled:opacity-50"
        >
          {checkMutation.isPending ? 'Checking...' : 'Run Check'}
        </button>
      </div>

      {/* Summary bar */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4">
        <p className="text-sm text-[var(--text-primary)] font-mono mb-3">
          {summary.total} potential hallucination{summary.total !== 1 ? 's' : ''} detected in this session
        </p>
        <div className="flex gap-3">
          <span className="text-xs font-mono text-[var(--accent-red)]">{summary.critical} Critical</span>
          <span className="text-xs font-mono text-[var(--accent-amber)]">{summary.warning} Warning</span>
          <span className="text-xs font-mono text-[var(--accent-cyan)]">{summary.info} Info</span>
        </div>
      </div>

      {/* Severity filter */}
      <div className="flex gap-2">
        {(['all', 'critical', 'warning', 'info'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setSeverityFilter(f)}
            className={clsx(
              'px-3 py-1 text-xs font-mono rounded border transition-colors',
              severityFilter === f
                ? 'bg-[var(--accent-indigo)] border-[var(--accent-indigo)] text-white'
                : 'border-[var(--border-subtle)] text-[var(--text-secondary)] hover:border-[var(--border-default)]',
            )}
          >
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <HallucinationPanel alerts={filteredAlerts} />
    </div>
  );
}
