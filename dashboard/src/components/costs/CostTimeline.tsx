/** Line chart of cumulative cost over time using Recharts. */

import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { format } from 'date-fns';

interface CostTimelineProps {
  timeline: Array<{ timestamp: string; cumulative_cost: number; event_name: string }>;
}

export function CostTimeline({ timeline }: CostTimelineProps) {
  if (timeline.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-[var(--text-tertiary)] text-sm font-mono">
        No timeline data yet
      </div>
    );
  }

  const data = timeline.map((t, i) => ({
    ...t,
    label: format(new Date(t.timestamp), 'HH:mm:ss'),
    index: i,
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data} margin={{ left: 8, right: 16, top: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
        <XAxis dataKey="label" tick={{ fill: 'var(--text-tertiary)', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
        <YAxis tickFormatter={(v) => `$${v.toFixed(4)}`} tick={{ fill: 'var(--text-tertiary)', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
        <Tooltip
          contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 6, fontFamily: 'JetBrains Mono', fontSize: 12 }}
          formatter={(value: number) => [`$${value.toFixed(6)}`, 'Cumulative']}
          labelFormatter={(label, payload) => payload?.[0]?.payload?.event_name || label}
        />
        <Line
          type="monotone"
          dataKey="cumulative_cost"
          stroke="var(--accent-indigo)"
          strokeWidth={2}
          dot={{ fill: 'var(--accent-indigo)', r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
