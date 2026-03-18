/** LLM Model Comparison page — A/B replay against a different model. */

import React, { useState } from 'react';
import { GitCompare, Play, AlertCircle } from 'lucide-react';
import { useSessionStore } from '@/stores/sessionStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';

interface CompareStepResult {
  event_id: string;
  event_name: string;
  original_model: string;
  original_output: string;
  original_cost_usd: number;
  original_latency_ms: number;
  original_hallucinations: number;
  comparison_model: string;
  comparison_output: string;
  comparison_cost_usd: number;
  comparison_latency_ms: number;
  comparison_hallucinations: number;
  output_diff_score: number;
}

interface CompareResponse {
  session_id: string;
  original_model: string;
  comparison_model: string;
  total_original_cost_usd: number;
  total_comparison_cost_usd: number;
  cost_delta_pct: number;
  original_hallucination_count: number;
  comparison_hallucination_count: number;
  steps: CompareStepResult[];
  recommendation: string;
}

const MODELS = [
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini', provider: 'openai' },
  { value: 'gpt-4o', label: 'GPT-4o', provider: 'openai' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', provider: 'openai' },
  { value: 'claude-3-5-haiku-20251001', label: 'Claude 3.5 Haiku', provider: 'anthropic' },
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet', provider: 'anthropic' },
  { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku', provider: 'anthropic' },
  { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash', provider: 'google' },
  { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash', provider: 'google' },
];

export function ComparePage() {
  const { activeSessionId, sessions } = useSessionStore();
  const { apiUrl } = useSettingsStore();

  const [targetModel, setTargetModel] = useState('claude-3-5-haiku-20251001');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);

  const selectedModel = MODELS.find(m => m.value === targetModel);
  const activeSession = sessions.find(s => s.id === activeSessionId);

  const runComparison = async () => {
    if (!activeSessionId || !apiKey) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch(`${apiUrl}/api/v1/compare/${activeSessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_model: targetModel,
          provider: selectedModel?.provider || 'openai',
          api_key: apiKey,
          max_steps: 20,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: 'Comparison failed' }));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-[var(--text-primary)] flex items-center gap-2">
          <GitCompare size={20} className="text-[var(--accent-indigo)]" />
          Model Comparison
        </h1>
        <p className="text-sm text-[var(--text-tertiary)] mt-0.5">
          Re-run the selected session against a different model and compare outputs, cost, and hallucinations.
        </p>
      </div>

      {/* Config panel */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1">
            <label className="text-xs text-[var(--text-tertiary)]">Session</label>
            <div className="text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-secondary)] truncate">
              {activeSession?.agent_name || 'No session selected'} {activeSessionId ? `· ${activeSessionId.slice(0,10)}…` : ''}
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs text-[var(--text-tertiary)]">Comparison model</label>
            <select
              value={targetModel}
              onChange={e => setTargetModel(e.target.value)}
              className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-indigo)]"
            >
              {MODELS.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs text-[var(--text-tertiary)]">
              API Key <span className="text-[var(--text-muted)]">(not stored)</span>
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder={`${selectedModel?.provider || 'provider'} API key`}
              className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-indigo)]"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={runComparison}
            disabled={!activeSessionId || !apiKey || loading}
            className="flex items-center gap-2 text-sm px-4 py-2 bg-[var(--accent-indigo)] text-white rounded-md hover:opacity-90 disabled:opacity-40 transition-opacity"
          >
            {loading ? <LoadingSpinner size="sm" /> : <Play size={14} />}
            {loading ? 'Running comparison…' : 'Run Comparison'}
          </button>
          <p className="text-xs text-[var(--text-muted)]">
            Re-runs up to 20 LLM call steps. May take 30–60 seconds.
          </p>
        </div>

        {error && (
          <div className="flex items-start gap-2 text-sm text-red-400 bg-red-950/30 border border-red-500/20 rounded-md px-3 py-2">
            <AlertCircle size={14} className="mt-0.5 shrink-0" />
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Summary bar */}
          <div className="grid grid-cols-2 gap-4">
            {/* Original */}
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-4 space-y-2">
              <div className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">Original</div>
              <div className="text-sm font-medium text-[var(--text-primary)]">{result.original_model}</div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-[var(--text-muted)]">Total cost</span>
                  <span className="font-mono text-[var(--text-primary)]">${result.total_original_cost_usd.toFixed(4)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-[var(--text-muted)]">Hallucinations</span>
                  <span className={`font-mono ${result.original_hallucination_count > 0 ? 'text-red-400' : 'text-[#22c55e]'}`}>
                    {result.original_hallucination_count}
                  </span>
                </div>
              </div>
            </div>

            {/* Comparison */}
            <div className="bg-[var(--bg-secondary)] border border-[var(--accent-indigo)]/30 rounded-xl p-4 space-y-2">
              <div className="text-xs font-semibold text-[var(--accent-indigo)] uppercase tracking-wide">Comparison</div>
              <div className="text-sm font-medium text-[var(--text-primary)]">{result.comparison_model}</div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-[var(--text-muted)]">Total cost</span>
                  <span className="font-mono text-[var(--text-primary)]">
                    ${result.total_comparison_cost_usd.toFixed(4)}
                    {result.cost_delta_pct < 0 && (
                      <span className="ml-1 text-[#22c55e]">↓{Math.abs(result.cost_delta_pct).toFixed(0)}%</span>
                    )}
                    {result.cost_delta_pct > 0 && (
                      <span className="ml-1 text-red-400">↑{result.cost_delta_pct.toFixed(0)}%</span>
                    )}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-[var(--text-muted)]">Hallucinations</span>
                  <span className={`font-mono ${result.comparison_hallucination_count > 0 ? 'text-red-400' : 'text-[#22c55e]'}`}>
                    {result.comparison_hallucination_count}
                    {result.comparison_hallucination_count < result.original_hallucination_count && (
                      <span className="ml-1 text-[#22c55e]">↓</span>
                    )}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Recommendation */}
          {result.recommendation && (
            <div className="bg-[var(--accent-indigo)]/10 border border-[var(--accent-indigo)]/20 rounded-xl px-4 py-3">
              <p className="text-sm text-[var(--text-secondary)]">
                <span className="font-semibold text-[var(--accent-indigo)]">Recommendation: </span>
                {result.recommendation}
              </p>
            </div>
          )}

          {/* Per-step results */}
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-[var(--text-secondary)]">Step-by-step comparison</h2>
            {result.steps.map((step, i) => (
              <div key={step.event_id} className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border-subtle)]">
                  <span className="text-xs font-mono text-[var(--text-muted)]">Step {i + 1}</span>
                  <span className="text-sm font-medium text-[var(--text-primary)] truncate">{step.event_name}</span>
                  <div className="ml-auto flex items-center gap-3 text-xs text-[var(--text-muted)] shrink-0">
                    <span>Similarity: {((1 - step.output_diff_score) * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 divide-x divide-[var(--border-subtle)]">
                  {/* Original */}
                  <div className="p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[var(--text-muted)]">{step.original_model}</span>
                      <div className="flex gap-2 text-xs">
                        <span className="font-mono">${step.original_cost_usd.toFixed(5)}</span>
                        <span className="text-[var(--text-muted)]">{step.original_latency_ms.toFixed(0)}ms</span>
                        {step.original_hallucinations > 0 && (
                          <span className="text-red-400">{step.original_hallucinations} halluc</span>
                        )}
                      </div>
                    </div>
                    <pre className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap font-mono leading-relaxed max-h-32 overflow-y-auto">
                      {step.original_output?.slice(0, 400) || '(no output)'}
                    </pre>
                  </div>
                  {/* Comparison */}
                  <div className="p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[var(--accent-indigo)]">{step.comparison_model}</span>
                      <div className="flex gap-2 text-xs">
                        <span className={`font-mono ${step.comparison_cost_usd < step.original_cost_usd ? 'text-[#22c55e]' : ''}`}>
                          ${step.comparison_cost_usd.toFixed(5)}
                        </span>
                        <span className="text-[var(--text-muted)]">{step.comparison_latency_ms.toFixed(0)}ms</span>
                        {step.comparison_hallucinations > 0 ? (
                          <span className="text-red-400">{step.comparison_hallucinations} halluc</span>
                        ) : (
                          <span className="text-[#22c55e]">✓ clean</span>
                        )}
                      </div>
                    </div>
                    <pre className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap font-mono leading-relaxed max-h-32 overflow-y-auto">
                      {step.comparison_output?.slice(0, 400) || '(no output)'}
                    </pre>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
