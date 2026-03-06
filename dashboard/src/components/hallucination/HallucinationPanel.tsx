/** List of detected hallucination alerts, each collapsible. */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { format } from 'date-fns';
import { HallucinationAlert } from '@/types';
import { SeverityBadge } from './SeverityBadge';
import { DiffViewer } from './DiffViewer';
import clsx from 'clsx';

interface HallucinationPanelProps {
  alerts: HallucinationAlert[];
}

function AlertCard({ alert }: { alert: HallucinationAlert }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-4 flex items-center justify-between gap-3 hover:bg-[var(--bg-tertiary)] transition-colors"
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <SeverityBadge severity={alert.severity} />
          <span className="text-sm font-mono text-[var(--text-primary)] truncate">{alert.description}</span>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className="text-xs text-[var(--text-tertiary)] font-mono">
            {format(new Date(alert.detected_at), 'HH:mm:ss')}
          </span>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="px-4 pb-4 border-t border-[var(--border-subtle)] pt-3 space-y-3">
              <DiffViewer expected={alert.expected_value} actual={alert.actual_value} />
              <div className="flex gap-4 text-xs font-mono text-[var(--text-tertiary)]">
                <span>Similarity: {(alert.similarity_score * 100).toFixed(0)}%</span>
                <span>Event: {alert.trace_event_id.slice(-8)}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function HallucinationPanel({ alerts }: HallucinationPanelProps) {
  if (alerts.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-[var(--text-tertiary)] text-sm font-mono">
        No hallucinations detected
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert) => (
        <AlertCard key={alert.id} alert={alert} />
      ))}
    </div>
  );
}
