/** Hook for fetching the AgentLens Reliability Score for a session. */

import { useState, useCallback } from 'react';

export interface ScoreResult {
  session_id: string;
  score: number;
  grade: 'A' | 'B' | 'C' | 'D';
  color: string;
  hallucination_count: number;
  error_count: number;
  mean_step_ms: number;
  cost_usd: number;
  penalty_breakdown: Record<string, number>;
}

export function useScore(apiUrl: string) {
  const [score, setScore] = useState<ScoreResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchScore = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${apiUrl}/api/v1/score/${sessionId}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setScore(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch score');
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  return { score, loading, error, fetchScore };
}
