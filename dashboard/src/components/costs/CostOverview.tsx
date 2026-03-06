/** Summary cards for cost overview — total cost, tokens, avg/step, most expensive model, projected monthly. */

import React from 'react';
import { DollarSign, Hash, TrendingDown, Zap, Calendar } from 'lucide-react';
import { CostSummary } from '@/hooks/useCostCalculator';

interface CostOverviewProps {
  summary: CostSummary;
}

interface CardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
  subtitle?: string;
}

function Card({ icon, label, value, color, subtitle }: CardProps) {
  return (
    <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-4 flex items-start gap-3">
      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}20` }}>
        <span style={{ color }}>{icon}</span>
      </div>
      <div>
        <p className="text-xs text-[var(--text-tertiary)] font-mono mb-1">{label}</p>
        <p className="text-lg font-mono font-semibold text-[var(--text-primary)]">{value}</p>
        {subtitle && <p className="text-xs text-[var(--text-tertiary)] font-mono mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

export function CostOverview({ summary }: CostOverviewProps) {
  const projectedLabel = summary.projectedMonthlyCost !== null
    ? `$${summary.projectedMonthlyCost.toFixed(2)}`
    : 'N/A';
  const projectedSubtitle = summary.projectedMonthlyCost !== null
    ? 'based on observed rate'
    : 'need ≥5 min of data';

  return (
    <div className="grid grid-cols-2 xl:grid-cols-5 gap-3">
      <Card
        icon={<DollarSign size={16} />}
        label="Total Cost"
        value={`$${summary.totalCost.toFixed(4)}`}
        color="var(--accent-emerald)"
      />
      <Card
        icon={<Hash size={16} />}
        label="Total Tokens"
        value={summary.totalTokens.toLocaleString()}
        color="var(--accent-cyan)"
      />
      <Card
        icon={<TrendingDown size={16} />}
        label="Avg Cost / LLM Step"
        value={`$${summary.avgCostPerStep.toFixed(4)}`}
        color="var(--accent-indigo)"
      />
      <Card
        icon={<Zap size={16} />}
        label="Most Expensive Model"
        value={
          summary.mostExpensiveModel
            ? `${summary.mostExpensiveModel} ($${summary.mostExpensiveCost.toFixed(4)})`
            : 'N/A'
        }
        color="var(--accent-amber)"
      />
      <Card
        icon={<Calendar size={16} />}
        label="Projected Monthly"
        value={projectedLabel}
        subtitle={projectedSubtitle}
        color="#a78bfa"
      />
    </div>
  );
}
