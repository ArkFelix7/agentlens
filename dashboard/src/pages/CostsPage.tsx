/** Costs analysis page — overview cards, timeline, breakdown, hotspots. */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSessionStore } from '@/stores/sessionStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { useTraceStore } from '@/stores/traceStore';
import { useCostCalculator } from '@/hooks/useCostCalculator';
import { CostOverview } from '@/components/costs/CostOverview';
import { CostBreakdown } from '@/components/costs/CostBreakdown';
import { CostTimeline } from '@/components/costs/CostTimeline';
import { CostHotspots } from '@/components/costs/CostHotspots';
import { EmptyState } from '@/components/shared/EmptyState';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { CostBreakdown as CostBreakdownData, CostHotspot, CostSuggestion } from '@/types';

export function CostsPage() {
  const { activeSessionId } = useSessionStore();
  const { apiUrl } = useSettingsStore();
  const { events } = useTraceStore();

  const summary = useCostCalculator(events);

  const { data: breakdown, isLoading: loadingBreakdown } = useQuery<CostBreakdownData>({
    queryKey: ['costs', activeSessionId],
    queryFn: async () => {
      const resp = await fetch(`${apiUrl}/api/v1/costs/${activeSessionId}`);
      return resp.json();
    },
    enabled: !!activeSessionId,
  });

  const { data: hotspotsData } = useQuery<{ hotspots: CostHotspot[] }>({
    queryKey: ['hotspots', activeSessionId],
    queryFn: async () => {
      const resp = await fetch(`${apiUrl}/api/v1/costs/${activeSessionId}/hotspots`);
      return resp.json();
    },
    enabled: !!activeSessionId,
  });

  const { data: suggestionsData } = useQuery<{ suggestions: CostSuggestion[] }>({
    queryKey: ['suggestions', activeSessionId],
    queryFn: async () => {
      const resp = await fetch(`${apiUrl}/api/v1/costs/${activeSessionId}/suggestions`);
      return resp.json();
    },
    enabled: !!activeSessionId,
  });

  if (!activeSessionId) {
    return <EmptyState title="No session selected" description="Select a session from the top bar to see cost analytics." showSetup={false} />;
  }

  if (loadingBreakdown) {
    return <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <h1 className="text-lg font-mono font-semibold text-[var(--text-primary)]">Cost Analytics</h1>

      <CostOverview summary={summary} />

      {breakdown && (
        <>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4">
            <h2 className="text-sm font-mono font-medium text-[var(--text-primary)] mb-3">Cost Over Time</h2>
            <CostTimeline timeline={breakdown.timeline} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4">
              <h2 className="text-sm font-mono font-medium text-[var(--text-primary)] mb-3">Cost by Model</h2>
              <CostBreakdown byModel={breakdown.by_model} />
            </div>

            <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4">
              <h2 className="text-sm font-mono font-medium text-[var(--text-primary)] mb-3">Cost Hotspots</h2>
              <CostHotspots
                hotspots={hotspotsData?.hotspots || []}
                suggestions={suggestionsData?.suggestions || []}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
