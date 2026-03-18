/** Budget Guardrails page — manage cost thresholds and view alert history. */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Plus, Trash2, ToggleLeft, ToggleRight, Webhook } from 'lucide-react';
import { useSettingsStore } from '@/stores/settingsStore';

interface BudgetRule {
  id: string;
  rule_name: string;
  rule_type: 'session_total' | 'per_model_call' | 'daily_total' | 'loop_detection';
  threshold_usd: number | null;
  loop_max_calls: number | null;
  loop_window_seconds: number | null;
  webhook_url: string | null;
  is_active: boolean;
  created_at: string;
}

const RULE_TYPE_LABELS: Record<string, string> = {
  session_total: 'Session total cost',
  per_model_call: 'Per LLM call cost',
  daily_total: 'Daily total cost',
  loop_detection: 'Loop detection',
};

export function BudgetPage() {
  const { apiUrl } = useSettingsStore();
  const [rules, setRules] = useState<BudgetRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    rule_name: '',
    rule_type: 'session_total' as BudgetRule['rule_type'],
    threshold_usd: '',
    loop_max_calls: '5',
    loop_window_seconds: '60',
    webhook_url: '',
  });

  const fetchRules = async () => {
    try {
      const resp = await fetch(`${apiUrl}/api/v1/budget/rules`);
      if (resp.ok) setRules(await resp.json());
    } catch {
      /* silently ignore */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRules(); }, [apiUrl]);

  const createRule = async () => {
    const body: Record<string, unknown> = {
      rule_name: form.rule_name,
      rule_type: form.rule_type,
    };
    if (form.rule_type !== 'loop_detection' && form.threshold_usd) {
      body.threshold_usd = parseFloat(form.threshold_usd);
    }
    if (form.rule_type === 'loop_detection') {
      body.loop_max_calls = parseInt(form.loop_max_calls);
      body.loop_window_seconds = parseInt(form.loop_window_seconds);
    }
    if (form.webhook_url) body.webhook_url = form.webhook_url;

    const resp = await fetch(`${apiUrl}/api/v1/budget/rules`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (resp.ok) {
      setShowForm(false);
      setForm({ rule_name: '', rule_type: 'session_total', threshold_usd: '', loop_max_calls: '5', loop_window_seconds: '60', webhook_url: '' });
      fetchRules();
    }
  };

  const toggleRule = async (rule: BudgetRule) => {
    await fetch(`${apiUrl}/api/v1/budget/rules/${rule.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !rule.is_active }),
    });
    fetchRules();
  };

  const deleteRule = async (id: string) => {
    await fetch(`${apiUrl}/api/v1/budget/rules/${id}`, { method: 'DELETE' });
    fetchRules();
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--text-primary)] flex items-center gap-2">
            <AlertTriangle size={20} className="text-[var(--accent-indigo)]" />
            Budget Guardrails
          </h1>
          <p className="text-sm text-[var(--text-tertiary)] mt-0.5">
            Set cost thresholds and loop detection rules. Alerts fire in real-time.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1.5 text-xs px-3 py-2 bg-[var(--accent-indigo)] text-white rounded-md hover:opacity-90 transition-opacity"
        >
          <Plus size={13} />
          Add Rule
        </button>
      </div>

      {/* New Rule Form */}
      {showForm && (
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-medium text-[var(--text-primary)]">New Budget Rule</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-[var(--text-tertiary)]">Rule name</label>
              <input
                type="text"
                value={form.rule_name}
                onChange={e => setForm(f => ({ ...f, rule_name: e.target.value }))}
                placeholder="e.g. production-session-cap"
                className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-indigo)]"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[var(--text-tertiary)]">Rule type</label>
              <select
                value={form.rule_type}
                onChange={e => setForm(f => ({ ...f, rule_type: e.target.value as BudgetRule['rule_type'] }))}
                className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-indigo)]"
              >
                {Object.entries(RULE_TYPE_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            </div>

            {form.rule_type !== 'loop_detection' ? (
              <div className="space-y-1">
                <label className="text-xs text-[var(--text-tertiary)]">Threshold (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={form.threshold_usd}
                  onChange={e => setForm(f => ({ ...f, threshold_usd: e.target.value }))}
                  placeholder="0.50"
                  className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-indigo)]"
                />
              </div>
            ) : (
              <>
                <div className="space-y-1">
                  <label className="text-xs text-[var(--text-tertiary)]">Max calls in window</label>
                  <input
                    type="number"
                    value={form.loop_max_calls}
                    onChange={e => setForm(f => ({ ...f, loop_max_calls: e.target.value }))}
                    className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-indigo)]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-[var(--text-tertiary)]">Window (seconds)</label>
                  <input
                    type="number"
                    value={form.loop_window_seconds}
                    onChange={e => setForm(f => ({ ...f, loop_window_seconds: e.target.value }))}
                    className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-indigo)]"
                  />
                </div>
              </>
            )}

            <div className="col-span-2 space-y-1">
              <label className="text-xs text-[var(--text-tertiary)]">
                Webhook URL <span className="text-[var(--text-muted)]">(optional — Slack, Discord, or custom)</span>
              </label>
              <input
                type="url"
                value={form.webhook_url}
                onChange={e => setForm(f => ({ ...f, webhook_url: e.target.value }))}
                placeholder="https://hooks.slack.com/services/..."
                className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-indigo)]"
              />
            </div>
          </div>

          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowForm(false)}
              className="text-xs px-3 py-2 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={createRule}
              disabled={!form.rule_name || (!form.threshold_usd && form.rule_type !== 'loop_detection')}
              className="text-xs px-4 py-2 bg-[var(--accent-indigo)] text-white rounded-md hover:opacity-90 disabled:opacity-40 transition-opacity"
            >
              Create Rule
            </button>
          </div>
        </div>
      )}

      {/* Rules List */}
      {loading ? (
        <div className="text-sm text-[var(--text-tertiary)]">Loading rules…</div>
      ) : rules.length === 0 ? (
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-8 text-center space-y-2">
          <AlertTriangle size={28} className="mx-auto text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No budget rules yet</p>
          <p className="text-xs text-[var(--text-muted)]">
            Add a rule to get real-time alerts when your agent exceeds cost thresholds.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {rules.map(rule => (
            <div
              key={rule.id}
              className={`flex items-center gap-4 bg-[var(--bg-secondary)] border rounded-xl px-5 py-4 transition-colors ${
                rule.is_active ? 'border-[var(--border-subtle)]' : 'border-[var(--border-subtle)] opacity-50'
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-[var(--text-primary)] truncate">
                    {rule.rule_name}
                  </span>
                  <span className="text-xs px-2 py-0.5 bg-[var(--bg-tertiary)] rounded-full text-[var(--text-tertiary)]">
                    {RULE_TYPE_LABELS[rule.rule_type]}
                  </span>
                </div>
                <div className="text-xs text-[var(--text-muted)] mt-1">
                  {rule.rule_type === 'loop_detection'
                    ? `Alert if same call >${rule.loop_max_calls}× in ${rule.loop_window_seconds}s`
                    : `Threshold: $${rule.threshold_usd?.toFixed(4)}`}
                  {rule.webhook_url && (
                    <span className="ml-2 inline-flex items-center gap-1 text-[var(--accent-indigo)]">
                      <Webhook size={10} /> Webhook configured
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => toggleRule(rule)}
                  className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                  title={rule.is_active ? 'Disable' : 'Enable'}
                >
                  {rule.is_active
                    ? <ToggleRight size={20} className="text-[var(--accent-indigo)]" />
                    : <ToggleLeft size={20} />
                  }
                </button>
                <button
                  onClick={() => deleteRule(rule.id)}
                  className="text-[var(--text-tertiary)] hover:text-red-400 transition-colors"
                  title="Delete rule"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info box */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-4 text-xs text-[var(--text-muted)] space-y-1">
        <p className="font-medium text-[var(--text-secondary)]">How it works</p>
        <p>Budget rules are checked after every trace event is ingested. When a threshold is breached, a red alert banner appears at the top of the dashboard in real-time. If a webhook URL is configured, a POST request is sent to that URL with the alert payload — compatible with Slack incoming webhooks, Discord webhooks, and custom endpoints.</p>
      </div>
    </div>
  );
}
