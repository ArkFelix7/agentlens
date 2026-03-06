/** Cost aggregation hook. Computes cost summaries from trace events. */

import { useMemo } from 'react';
import { TraceEvent } from '@/types';

export interface CostSummary {
  totalCost: number;
  totalTokens: number;
  avgCostPerStep: number;
  costByModel: Record<string, number>;
  mostExpensiveModel: string | null;
  mostExpensiveCost: number;
  projectedMonthlyCost: number | null;
}

export function useCostCalculator(events: TraceEvent[]): CostSummary {
  return useMemo(() => {
    const totalCost = events.reduce((sum, e) => sum + (e.cost_usd || 0), 0);
    const totalTokens = events.reduce((sum, e) => sum + e.tokens_input + e.tokens_output, 0);
    const llmEvents = events.filter((e) => e.event_type === 'llm_call' && e.cost_usd > 0);
    const avgCostPerStep = llmEvents.length > 0 ? totalCost / llmEvents.length : 0;

    const costByModel: Record<string, number> = {};
    for (const e of events) {
      if (e.model && e.cost_usd > 0) {
        costByModel[e.model] = (costByModel[e.model] || 0) + e.cost_usd;
      }
    }

    let mostExpensiveModel: string | null = null;
    let mostExpensiveCost = 0;
    for (const [model, cost] of Object.entries(costByModel)) {
      if (cost > mostExpensiveCost) {
        mostExpensiveCost = cost;
        mostExpensiveModel = model;
      }
    }

    // Project monthly cost based on observed event time span
    let projectedMonthlyCost: number | null = null;
    const tsEvents = events.filter((e) => e.timestamp);
    if (tsEvents.length >= 2 && totalCost > 0) {
      const times = tsEvents.map((e) => new Date(e.timestamp).getTime());
      const spanMs = Math.max(...times) - Math.min(...times);
      const FIVE_MINUTES_MS = 5 * 60 * 1000;
      const MONTH_MS = 30 * 24 * 60 * 60 * 1000;
      if (spanMs >= FIVE_MINUTES_MS) {
        projectedMonthlyCost = (totalCost / spanMs) * MONTH_MS;
      }
    }

    return {
      totalCost,
      totalTokens,
      avgCostPerStep,
      costByModel,
      mostExpensiveModel,
      mostExpensiveCost,
      projectedMonthlyCost,
    };
  }, [events]);
}
