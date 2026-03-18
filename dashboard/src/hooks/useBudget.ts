/** Hook for fetching and managing budget guardrail rules and alerts. */

import { useState, useCallback } from 'react';
import { BudgetRule, BudgetAlert } from '@/types';

export function useBudget(apiUrl: string) {
  const [rules, setRules] = useState<BudgetRule[]>([]);
  const [alerts, setAlerts] = useState<BudgetAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${apiUrl}/api/v1/budget/rules`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setRules(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch rules');
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  const fetchAlerts = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    try {
      const resp = await fetch(`${apiUrl}/api/v1/budget/alerts/${sessionId}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setAlerts(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch alerts');
    }
  }, [apiUrl]);

  const createRule = useCallback(async (rule: Omit<BudgetRule, 'id' | 'created_at' | 'is_active'>) => {
    try {
      const resp = await fetch(`${apiUrl}/api/v1/budget/rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rule),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      await fetchRules();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create rule');
    }
  }, [apiUrl, fetchRules]);

  const deleteRule = useCallback(async (ruleId: string) => {
    try {
      const resp = await fetch(`${apiUrl}/api/v1/budget/rules/${ruleId}`, { method: 'DELETE' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      await fetchRules();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete rule');
    }
  }, [apiUrl, fetchRules]);

  const toggleRule = useCallback(async (ruleId: string, isActive: boolean) => {
    try {
      const resp = await fetch(`${apiUrl}/api/v1/budget/rules/${ruleId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: isActive }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      await fetchRules();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to update rule');
    }
  }, [apiUrl, fetchRules]);

  return { rules, alerts, loading, error, fetchRules, fetchAlerts, createRule, deleteRule, toggleRule };
}
