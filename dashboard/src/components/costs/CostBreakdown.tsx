/** Bar chart of cost per model using Recharts. */

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const MODEL_COLORS = ['#6366f1', '#a855f7', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'];

interface CostBreakdownProps {
  byModel: Record<string, { cost: number; call_count: number }>;
}

export function CostBreakdown({ byModel }: CostBreakdownProps) {
  const data = Object.entries(byModel)
    .map(([model, stats]) => ({ model, cost: stats.cost, calls: stats.call_count }))
    .sort((a, b) => b.cost - a.cost);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-[var(--text-tertiary)] text-sm font-mono">
        No model costs yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 40, top: 4, bottom: 4 }}>
        <XAxis type="number" tickFormatter={(v) => `$${v.toFixed(4)}`} tick={{ fill: 'var(--text-tertiary)', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
        <YAxis type="category" dataKey="model" tick={{ fill: 'var(--text-secondary)', fontSize: 11, fontFamily: 'JetBrains Mono' }} width={120} />
        <Tooltip
          contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 6, fontFamily: 'JetBrains Mono', fontSize: 12 }}
          formatter={(value: number) => [`$${value.toFixed(6)}`, 'Cost']}
        />
        <Bar dataKey="cost" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={MODEL_COLORS[i % MODEL_COLORS.length]} fillOpacity={0.8} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
