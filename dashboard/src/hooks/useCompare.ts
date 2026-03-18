/** Hook for fetching model comparison results between two sessions. */

import { useState, useCallback } from 'react';

export interface CompareResult {
  session_a_id: string;
  session_b_id: string;
  cost_delta_usd: number;
  latency_delta_ms: number;
  token_delta: number;
  quality_delta: number;
  hallucination_delta: number;
  winner: 'a' | 'b' | 'tie';
  summary: string;
}

export function useCompare(apiUrl: string) {
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const compare = useCallback(async (sessionA: string, sessionB: string) => {
    if (!sessionA || !sessionB) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${apiUrl}/api/v1/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_a_id: sessionA, session_b_id: sessionB }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Comparison failed');
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, compare, reset };
}
