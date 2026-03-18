/** Agent Reliability Score page — shows 0-100 score with breakdown and embeddable badge. */

import React, { useEffect, useState } from 'react';
import { Shield, Copy, Check, RefreshCw, ExternalLink } from 'lucide-react';
import { useSessionStore } from '@/stores/sessionStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { useScore } from '@/hooks/useScore';
import { EmptyState } from '@/components/shared/EmptyState';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';

const GRADE_LABELS: Record<string, string> = {
  A: 'Excellent',
  B: 'Good',
  C: 'Fair',
  D: 'Needs Work',
};

const PENALTY_LABELS: Record<string, string> = {
  hallucinations: 'Hallucination penalty',
  errors: 'Error penalty',
  high_latency: 'High latency penalty',
  zero_issues_bonus: 'Zero-issues bonus',
};

export function ScorePage() {
  const { activeSessionId, sessions } = useSessionStore();
  const { apiUrl } = useSettingsStore();
  const { score, loading, error, fetchScore } = useScore(apiUrl);
  const [copied, setCopied] = useState(false);
  const [copiedBadge, setCopiedBadge] = useState(false);

  const activeSession = sessions.find(s => s.id === activeSessionId);

  useEffect(() => {
    if (activeSessionId) fetchScore(activeSessionId);
  }, [activeSessionId, fetchScore]);

  const badgeUrl = activeSessionId
    ? `${apiUrl}/api/v1/score/${activeSessionId}/badge.svg`
    : '';

  const badgeMarkdown = badgeUrl
    ? `![AgentLens Score](${badgeUrl})`
    : '';

  const copyBadge = () => {
    navigator.clipboard.writeText(badgeMarkdown).then(() => {
      setCopiedBadge(true);
      setTimeout(() => setCopiedBadge(false), 2000);
    });
  };

  const copyBadgeUrl = () => {
    navigator.clipboard.writeText(badgeUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  if (!activeSessionId) {
    return (
      <div className="h-full flex items-center justify-center">
        <EmptyState
          icon={<Shield size={32} className="text-[var(--text-tertiary)]" />}
          title="No session selected"
          description="Select a session from the Traces page to view its reliability score."
        />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !score) {
    return (
      <div className="h-full flex items-center justify-center">
        <EmptyState
          icon={<Shield size={32} className="text-[var(--text-tertiary)]" />}
          title="Score unavailable"
          description={error || 'Run a session first to generate a score.'}
        />
      </div>
    );
  }

  const circumference = 2 * Math.PI * 54;
  const dash = (score.score / 100) * circumference;

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--text-primary)] flex items-center gap-2">
            <Shield size={20} className="text-[var(--accent-indigo)]" />
            Reliability Score
          </h1>
          <p className="text-sm text-[var(--text-tertiary)] mt-0.5">
            {activeSession?.agent_name || 'Agent'} · {activeSessionId?.slice(0, 12)}…
          </p>
        </div>
        <button
          onClick={() => fetchScore(activeSessionId!)}
          className="flex items-center gap-1.5 text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] px-3 py-1.5 rounded-md border border-[var(--border-subtle)] hover:border-[var(--border-default)] transition-colors"
        >
          <RefreshCw size={12} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Circular Score Gauge */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-6 flex flex-col items-center gap-4">
          <div className="relative w-36 h-36">
            <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
              {/* Track */}
              <circle cx="60" cy="60" r="54" fill="none" stroke="var(--border-subtle)" strokeWidth="8" />
              {/* Progress */}
              <circle
                cx="60" cy="60" r="54"
                fill="none"
                stroke={score.color}
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${dash} ${circumference}`}
                style={{ transition: 'stroke-dasharray 0.8s ease' }}
              />
            </svg>
            {/* Center text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold font-mono" style={{ color: score.color }}>
                {score.score}
              </span>
              <span className="text-xs text-[var(--text-tertiary)]">/ 100</span>
            </div>
          </div>

          <div className="text-center">
            <div
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold font-mono"
              style={{ backgroundColor: score.color + '22', color: score.color }}
            >
              Grade {score.grade} — {GRADE_LABELS[score.grade]}
            </div>
          </div>

          {/* Quick stats */}
          <div className="w-full grid grid-cols-3 gap-3 text-center">
            <div className="bg-[var(--bg-tertiary)] rounded-lg p-3">
              <div className={`text-lg font-bold font-mono ${score.hallucination_count > 0 ? 'text-red-400' : 'text-[#22c55e]'}`}>
                {score.hallucination_count}
              </div>
              <div className="text-xs text-[var(--text-tertiary)] mt-0.5">Hallucinations</div>
            </div>
            <div className="bg-[var(--bg-tertiary)] rounded-lg p-3">
              <div className={`text-lg font-bold font-mono ${score.error_count > 0 ? 'text-orange-400' : 'text-[#22c55e]'}`}>
                {score.error_count}
              </div>
              <div className="text-xs text-[var(--text-tertiary)] mt-0.5">Errors</div>
            </div>
            <div className="bg-[var(--bg-tertiary)] rounded-lg p-3">
              <div className="text-lg font-bold font-mono text-[var(--text-primary)]">
                ${score.cost_usd.toFixed(4)}
              </div>
              <div className="text-xs text-[var(--text-tertiary)] mt-0.5">Cost</div>
            </div>
          </div>
        </div>

        {/* Score Breakdown */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-6 space-y-4">
          <h2 className="text-sm font-medium text-[var(--text-secondary)]">Score Breakdown</h2>

          {/* Base score */}
          <div className="flex items-center justify-between py-2 border-b border-[var(--border-subtle)]">
            <span className="text-sm text-[var(--text-tertiary)]">Base score</span>
            <span className="text-sm font-mono text-[var(--text-primary)]">100</span>
          </div>

          {/* Penalties */}
          {Object.entries(score.penalty_breakdown).map(([key, value]) => (
            <div key={key} className="flex items-center gap-3">
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-[var(--text-secondary)]">
                    {PENALTY_LABELS[key] || key}
                  </span>
                  <span
                    className={`text-xs font-mono font-semibold ${value < 0 ? 'text-red-400' : 'text-[#22c55e]'}`}
                  >
                    {value > 0 ? '+' : ''}{value}
                  </span>
                </div>
                <div className="h-1.5 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.abs(value)}%`,
                      backgroundColor: value < 0 ? '#ef4444' : '#22c55e',
                    }}
                  />
                </div>
              </div>
            </div>
          ))}

          {/* Final score */}
          <div className="flex items-center justify-between pt-2 border-t border-[var(--border-subtle)]">
            <span className="text-sm font-medium text-[var(--text-primary)]">Final score</span>
            <span className="text-sm font-mono font-bold" style={{ color: score.color }}>
              {score.score} / 100
            </span>
          </div>

          <div className="text-xs text-[var(--text-muted)] leading-relaxed pt-1">
            Avg step latency: {score.mean_step_ms.toFixed(0)}ms
          </div>
        </div>
      </div>

      {/* Badge Section */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-medium text-[var(--text-secondary)]">Embeddable Badge</h2>
        <p className="text-xs text-[var(--text-muted)]">
          Add this badge to your README to show your agent's reliability score.
        </p>

        {/* Live badge preview */}
        <div className="flex items-center gap-3">
          <img src={badgeUrl} alt="AgentLens Score Badge" className="h-5" />
          <span className="text-xs text-[var(--text-tertiary)]">Live preview</span>
        </div>

        {/* Markdown */}
        <div className="space-y-2">
          <label className="text-xs text-[var(--text-tertiary)]">Markdown</label>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-xs bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 font-mono text-[var(--text-secondary)] overflow-x-auto">
              {badgeMarkdown}
            </code>
            <button
              onClick={copyBadge}
              className="flex items-center gap-1.5 text-xs px-3 py-2 bg-[var(--accent-indigo)] text-white rounded-md hover:opacity-90 transition-opacity shrink-0"
            >
              {copiedBadge ? <Check size={12} /> : <Copy size={12} />}
              {copiedBadge ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>

        {/* Direct URL */}
        <div className="space-y-2">
          <label className="text-xs text-[var(--text-tertiary)]">Badge URL</label>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-xs bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 font-mono text-[var(--text-secondary)] overflow-x-auto">
              {badgeUrl}
            </code>
            <button
              onClick={copyBadgeUrl}
              className="flex items-center gap-1.5 text-xs px-3 py-2 border border-[var(--border-subtle)] text-[var(--text-secondary)] rounded-md hover:text-[var(--text-primary)] transition-colors shrink-0"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? 'Copied!' : 'Copy URL'}
            </button>
            <a
              href={badgeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
            >
              <ExternalLink size={12} />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
