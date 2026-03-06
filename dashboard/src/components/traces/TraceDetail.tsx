/** Right panel: detailed view of a selected trace event. */

import React from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { TraceEvent } from '@/types';
import { EventBadge } from './EventBadge';
import { JsonViewer } from '@/components/shared/JsonViewer';

interface TraceDetailProps {
  event: TraceEvent | null;
}

export function TraceDetail({ event }: TraceDetailProps) {
  if (!event) {
    return (
      <div className="flex items-center justify-center h-full p-6 text-center">
        <div>
          <p className="text-sm text-[var(--text-tertiary)] font-mono">Select an event from the trace graph</p>
          <p className="text-xs text-[var(--text-tertiary)] mt-1">to see details</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      key={event.id}
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2 }}
      className="h-full overflow-y-auto p-4 space-y-4"
    >
      {/* Header */}
      <div className="space-y-2">
        <EventBadge eventType={event.event_type} status={event.status} />
        <h3 className="font-mono font-semibold text-sm text-[var(--text-primary)] break-all">{event.event_name}</h3>
      </div>

      {/* Metadata grid */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {event.model && (
          <div className="bg-[var(--bg-tertiary)] rounded p-2">
            <p className="text-[var(--text-tertiary)] mb-0.5">Model</p>
            <p className="text-[var(--text-primary)] font-mono">{event.model}</p>
          </div>
        )}
        <div className="bg-[var(--bg-tertiary)] rounded p-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Duration</p>
          <p className="text-[var(--text-primary)] font-mono">{event.duration_ms.toFixed(0)}ms</p>
        </div>
        {(event.tokens_input > 0 || event.tokens_output > 0) && (
          <div className="bg-[var(--bg-tertiary)] rounded p-2">
            <p className="text-[var(--text-tertiary)] mb-0.5">Tokens</p>
            <p className="text-[var(--text-primary)] font-mono">
              {event.tokens_input.toLocaleString()} in / {event.tokens_output.toLocaleString()} out
            </p>
          </div>
        )}
        {event.cost_usd > 0 && (
          <div className="bg-[var(--bg-tertiary)] rounded p-2">
            <p className="text-[var(--text-tertiary)] mb-0.5">Cost</p>
            <p className="text-[var(--accent-emerald)] font-mono">${event.cost_usd.toFixed(6)}</p>
          </div>
        )}
        <div className="bg-[var(--bg-tertiary)] rounded p-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Status</p>
          <p
            className="font-mono"
            style={{ color: event.status === 'error' ? 'var(--accent-red)' : 'var(--accent-emerald)' }}
          >
            {event.status === 'success' ? '✓ Success' : event.status === 'error' ? '✗ Error' : event.status}
          </p>
        </div>
        <div className="bg-[var(--bg-tertiary)] rounded p-2 col-span-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Timestamp</p>
          <p className="text-[var(--text-primary)] font-mono">
            {format(new Date(event.timestamp), 'MMM d, HH:mm:ss.SSS')}
          </p>
        </div>
      </div>

      {/* Error message */}
      {event.error_message && (
        <div className="bg-[rgba(239,68,68,0.1)] border border-[rgba(239,68,68,0.2)] rounded p-3">
          <p className="text-xs text-[var(--accent-red)] font-mono">{event.error_message}</p>
        </div>
      )}

      {/* Input */}
      {event.input_data !== null && (
        <div>
          <p className="text-xs text-[var(--text-tertiary)] font-mono mb-2">INPUT</p>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded p-3">
            <JsonViewer data={event.input_data} />
          </div>
        </div>
      )}

      {/* Output */}
      {event.output_data !== null && (
        <div>
          <p className="text-xs text-[var(--text-tertiary)] font-mono mb-2">OUTPUT</p>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded p-3">
            <JsonViewer data={event.output_data} />
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="text-xs space-y-1 text-[var(--text-tertiary)] font-mono">
        <p>ID: {event.id}</p>
        {event.parent_event_id && <p>Parent: {event.parent_event_id}</p>}
        <p>Session: {event.session_id}</p>
      </div>
    </motion.div>
  );
}
