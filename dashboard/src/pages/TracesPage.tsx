/** Main traces page — D3 graph (or timeline) + event detail panel. */

import React, { useState } from 'react';
import { useTraceStore } from '@/stores/traceStore';
import { useTraceGraph } from '@/hooks/useTraceGraph';
import { TraceGraph } from '@/components/traces/TraceGraph';
import { TraceTimeline } from '@/components/traces/TraceTimeline';
import { TraceDetail } from '@/components/traces/TraceDetail';
import { EmptyState } from '@/components/shared/EmptyState';
import { EventType } from '@/types';
import clsx from 'clsx';

const EVENT_TYPES: EventType[] = ['llm_call', 'tool_call', 'decision', 'memory_read', 'memory_write', 'user_input', 'error'];

export function TracesPage() {
  const { selectedEventId, selectEvent, filter, setFilter, getFilteredEvents, getSelectedEvent } = useTraceStore();
  const [viewMode, setViewMode] = useState<'graph' | 'timeline'>('timeline');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredEvents = getFilteredEvents();
  const selectedEvent = getSelectedEvent();
  const graphData = useTraceGraph(filteredEvents);

  const toggleEventType = (type: EventType) => {
    const current = filter.event_types;
    if (current.includes(type)) {
      setFilter({ event_types: current.filter((t) => t !== type) });
    } else {
      setFilter({ event_types: [...current, type] });
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Controls bar */}
      <div className="flex items-center gap-3 px-4 py-2 bg-[var(--bg-secondary)] border-b border-[var(--border-subtle)] flex-wrap">
        {/* View toggle */}
        <div className="flex gap-1">
          <button
            onClick={() => setViewMode('graph')}
            className={clsx(
              'px-2 py-1 text-xs font-mono rounded transition-colors',
              viewMode === 'graph'
                ? 'bg-[var(--accent-indigo)] text-white'
                : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]',
            )}
          >
            Graph
          </button>
          <button
            onClick={() => setViewMode('timeline')}
            className={clsx(
              'px-2 py-1 text-xs font-mono rounded transition-colors',
              viewMode === 'timeline'
                ? 'bg-[var(--accent-indigo)] text-white'
                : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]',
            )}
          >
            Timeline
          </button>
        </div>

        {/* Event type filters */}
        <div className="flex gap-1 flex-wrap">
          {EVENT_TYPES.map((type) => (
            <button
              key={type}
              onClick={() => toggleEventType(type)}
              className={clsx(
                'px-2 py-0.5 text-xs font-mono rounded border transition-colors',
                filter.event_types.includes(type)
                  ? 'bg-[var(--accent-indigo)] border-[var(--accent-indigo)] text-white'
                  : 'border-[var(--border-subtle)] text-[var(--text-tertiary)] hover:border-[var(--border-default)]',
              )}
            >
              {type.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        {/* Search */}
        <input
          type="text"
          placeholder="Search events..."
          value={filter.search_query}
          onChange={(e) => setFilter({ search_query: e.target.value })}
          className="bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded px-2 py-1 text-xs font-mono
            text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--border-focus)]
            w-40"
        />

        <div className="flex-1" />
        <span className="text-xs text-[var(--text-tertiary)] font-mono">
          {filteredEvents.length} events
        </span>
      </div>

      {/* Main area */}
      <div className="flex flex-1 min-h-0">
        {/* Left panel — graph or timeline */}
        <div className="flex-1 min-w-0 border-r border-[var(--border-subtle)] overflow-hidden">
          {filteredEvents.length === 0 ? (
            <EmptyState />
          ) : viewMode === 'graph' ? (
            <TraceGraph
              graphData={graphData}
              selectedEventId={selectedEventId}
              onSelectEvent={selectEvent}
            />
          ) : (
            <TraceTimeline
              events={filteredEvents}
              selectedEventId={selectedEventId}
              onSelectEvent={selectEvent}
            />
          )}
        </div>

        {/* Right panel — event detail */}
        <div className="w-80 shrink-0">
          <TraceDetail event={selectedEvent} />
        </div>
      </div>
    </div>
  );
}
