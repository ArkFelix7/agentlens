/** Memory inspector page — timeline + detail with version history. */

import React, { useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useSessionStore } from '@/stores/sessionStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { MemoryEntry } from '@/types';
import { MemoryTimeline } from '@/components/memory/MemoryTimeline';
import { MemoryDetail } from '@/components/memory/MemoryDetail';
import { MemorySearch } from '@/components/memory/MemorySearch';
import { EmptyState } from '@/components/shared/EmptyState';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';

export function MemoryPage() {
  const { activeSessionId } = useSessionStore();
  const { apiUrl } = useSettingsStore();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<{ entries: MemoryEntry[] }>({
    queryKey: ['memory', activeSessionId],
    queryFn: async () => {
      const resp = await fetch(`${apiUrl}/api/v1/memory/${activeSessionId}`);
      return resp.json();
    },
    enabled: !!activeSessionId,
  });

  const handleEdit = useCallback(async (entry: MemoryEntry, newContent: string) => {
    await fetch(`${apiUrl}/api/v1/memory/entry/${entry.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newContent }),
    });
    queryClient.invalidateQueries({ queryKey: ['memory', activeSessionId] });
  }, [apiUrl, activeSessionId, queryClient]);

  const handleDelete = useCallback(async (entry: MemoryEntry) => {
    await fetch(`${apiUrl}/api/v1/memory/entry/${entry.id}`, { method: 'DELETE' });
    setSelectedId(null);
    queryClient.invalidateQueries({ queryKey: ['memory', activeSessionId] });
  }, [apiUrl, activeSessionId, queryClient]);

  if (!activeSessionId) {
    return <EmptyState title="No session selected" description="Select a session to inspect memory." showSetup={false} />;
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>;
  }

  const entries = data?.entries || [];
  const selectedEntry = entries.find((e) => e.id === selectedId) || null;
  const history = selectedEntry
    ? entries.filter((e) => e.memory_key === selectedEntry.memory_key && e.id !== selectedEntry.id)
    : [];

  return (
    <div className="flex h-full">
      {/* Left: Timeline */}
      <div className="w-2/5 flex flex-col border-r border-[var(--border-subtle)]">
        <div className="p-3 border-b border-[var(--border-subtle)]">
          <h1 className="text-sm font-mono font-semibold text-[var(--text-primary)] mb-2">Memory Inspector</h1>
          <MemorySearch value={searchQuery} onChange={setSearchQuery} />
        </div>
        {entries.length === 0 ? (
          <EmptyState title="No memory entries" description="Agent memory operations will appear here." showSetup={false} />
        ) : (
          <MemoryTimeline
            entries={entries}
            selectedId={selectedId}
            onSelect={setSelectedId}
            searchQuery={searchQuery}
          />
        )}
      </div>

      {/* Right: Detail */}
      <div className="flex-1 min-w-0">
        <MemoryDetail
          entry={selectedEntry}
          history={history}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>
    </div>
  );
}
