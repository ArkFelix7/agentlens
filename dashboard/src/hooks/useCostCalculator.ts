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

    return {
      totalCost,
      totalTokens,
      avgCostPerStep,
      costByModel,
      mostExpensiveModel,
      mostExpensiveCost,
    };
  }, [events]);
}
