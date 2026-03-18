/** Prompt Version Control page — manage prompt history, compare versions, promote. */

import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Plus, GitCommit, ArrowUp, ChevronDown, ChevronRight } from 'lucide-react';
import { useSettingsStore } from '@/stores/settingsStore';

interface PromptVersion {
  id: string;
  prompt_id: string;
  version: number;
  content: string;
  label: string | null;
  commit_message: string | null;
  created_at: string;
  total_uses: number;
  avg_cost_usd: number | null;
  avg_latency_ms: number | null;
  hallucination_rate: number | null;
}

interface Prompt {
  id: string;
  name: string;
  description: string | null;
  current_version: number;
  created_at: string;
  updated_at: string;
  versions: PromptVersion[];
}

function diffLines(a: string, b: string): Array<{ type: 'same' | 'add' | 'remove'; text: string }> {
  const aLines = a.split('\n');
  const bLines = b.split('\n');
  const result: Array<{ type: 'same' | 'add' | 'remove'; text: string }> = [];
  const maxLen = Math.max(aLines.length, bLines.length);
  for (let i = 0; i < maxLen; i++) {
    const aLine = aLines[i];
    const bLine = bLines[i];
    if (aLine === bLine) {
      result.push({ type: 'same', text: aLine ?? '' });
    } else {
      if (aLine !== undefined) result.push({ type: 'remove', text: aLine });
      if (bLine !== undefined) result.push({ type: 'add', text: bLine });
    }
  }
  return result;
}

export function PromptsPage() {
  const { apiUrl } = useSettingsStore();
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Prompt | null>(null);
  const [compareVersions, setCompareVersions] = useState<[number, number] | null>(null);
  const [showNewPrompt, setShowNewPrompt] = useState(false);
  const [showNewVersion, setShowNewVersion] = useState(false);
  const [expandedVersions, setExpandedVersions] = useState<Set<number>>(new Set());

  const [newPromptForm, setNewPromptForm] = useState({ name: '', description: '', initial_content: '', initial_commit_message: 'Initial version' });
  const [newVersionForm, setNewVersionForm] = useState({ content: '', label: '', commit_message: '' });

  const fetchPrompts = useCallback(async () => {
    try {
      const resp = await fetch(`${apiUrl}/api/v1/prompts`);
      if (resp.ok) {
        const data = await resp.json();
        setPrompts(data);
        if (selected) {
          const updated = data.find((p: Prompt) => p.id === selected.id);
          if (updated) setSelected(updated);
        }
      }
    } catch { /* silently ignore */ } finally {
      setLoading(false);
    }
  }, [apiUrl, selected]);

  useEffect(() => { fetchPrompts(); }, [apiUrl]);

  const createPrompt = async () => {
    const resp = await fetch(`${apiUrl}/api/v1/prompts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newPromptForm),
    });
    if (resp.ok) {
      setShowNewPrompt(false);
      setNewPromptForm({ name: '', description: '', initial_content: '', initial_commit_message: 'Initial version' });
      fetchPrompts();
    }
  };

  const addVersion = async () => {
    if (!selected) return;
    const resp = await fetch(`${apiUrl}/api/v1/prompts/${selected.name}/versions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: newVersionForm.content,
        label: newVersionForm.label || null,
        commit_message: newVersionForm.commit_message || null,
      }),
    });
    if (resp.ok) {
      setShowNewVersion(false);
      setNewVersionForm({ content: '', label: '', commit_message: '' });
      fetchPrompts();
    }
  };

  const promoteVersion = async (versionNum: number) => {
    if (!selected) return;
    const resp = await fetch(`${apiUrl}/api/v1/prompts/${selected.name}/versions/${versionNum}/promote`, {
      method: 'PATCH',
    });
    if (resp.ok) fetchPrompts();
  };

  const toggleVersionExpand = (v: number) => {
    setExpandedVersions(prev => {
      const next = new Set(prev);
      if (next.has(v)) next.delete(v); else next.add(v);
      return next;
    });
  };

  const compareVersionDiff = compareVersions && selected
    ? (() => {
        const vA = selected.versions.find(v => v.version === compareVersions[0]);
        const vB = selected.versions.find(v => v.version === compareVersions[1]);
        if (!vA || !vB) return null;
        return { vA, vB, diff: diffLines(vA.content, vB.content) };
      })()
    : null;

  return (
    <div className="h-full flex overflow-hidden">
      {/* Left: Prompt List */}
      <div className="w-64 border-r border-[var(--border-subtle)] flex flex-col bg-[var(--bg-secondary)]">
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-subtle)]">
          <h2 className="text-sm font-medium text-[var(--text-primary)] flex items-center gap-2">
            <FileText size={14} className="text-[var(--accent-indigo)]" />
            Prompts
          </h2>
          <button
            onClick={() => setShowNewPrompt(true)}
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
          >
            <Plus size={14} />
          </button>
        </div>

        {loading ? (
          <div className="p-4 text-xs text-[var(--text-muted)]">Loading…</div>
        ) : prompts.length === 0 ? (
          <div className="p-4 text-xs text-[var(--text-muted)] text-center space-y-2">
            <p>No prompts yet.</p>
            <button onClick={() => setShowNewPrompt(true)} className="text-[var(--accent-indigo)] hover:underline">
              Create first prompt
            </button>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto py-1">
            {prompts.map(p => (
              <button
                key={p.id}
                onClick={() => { setSelected(p); setCompareVersions(null); }}
                className={`w-full text-left px-4 py-3 hover:bg-[var(--bg-tertiary)] transition-colors border-b border-[var(--border-subtle)] last:border-0 ${
                  selected?.id === p.id ? 'bg-[rgba(99,102,241,0.08)] border-l-2 border-l-[var(--accent-indigo)]' : ''
                }`}
              >
                <div className="text-sm font-medium text-[var(--text-primary)] truncate">{p.name}</div>
                <div className="text-xs text-[var(--text-muted)] mt-0.5">v{p.current_version} · {p.versions.length} versions</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Center/Right: Version History + Diff */}
      {selected ? (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Prompt header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-subtle)]">
            <div>
              <h1 className="text-base font-semibold text-[var(--text-primary)]">{selected.name}</h1>
              {selected.description && (
                <p className="text-xs text-[var(--text-muted)] mt-0.5">{selected.description}</p>
              )}
            </div>
            <div className="flex gap-2">
              {compareVersions && (
                <button
                  onClick={() => setCompareVersions(null)}
                  className="text-xs px-3 py-1.5 border border-[var(--border-subtle)] text-[var(--text-tertiary)] rounded-md hover:text-[var(--text-primary)] transition-colors"
                >
                  Clear diff
                </button>
              )}
              <button
                onClick={() => setShowNewVersion(true)}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-[var(--accent-indigo)] text-white rounded-md hover:opacity-90 transition-opacity"
              >
                <Plus size={12} />
                New version
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-3">
            {/* New version form */}
            {showNewVersion && (
              <div className="bg-[var(--bg-secondary)] border border-[var(--accent-indigo)]/30 rounded-xl p-4 space-y-3">
                <h3 className="text-sm font-medium text-[var(--text-primary)]">New Version</h3>
                <textarea
                  value={newVersionForm.content}
                  onChange={e => setNewVersionForm(f => ({ ...f, content: e.target.value }))}
                  placeholder="Prompt content..."
                  rows={6}
                  className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] font-mono placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-indigo)] resize-none"
                />
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    value={newVersionForm.commit_message}
                    onChange={e => setNewVersionForm(f => ({ ...f, commit_message: e.target.value }))}
                    placeholder="Commit message (e.g. 'Reduce hallucination rate')"
                    className="text-xs bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-indigo)]"
                  />
                  <input
                    type="text"
                    value={newVersionForm.label}
                    onChange={e => setNewVersionForm(f => ({ ...f, label: e.target.value }))}
                    placeholder="Label (e.g. 'production', 'experiment')"
                    className="text-xs bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-indigo)]"
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <button onClick={() => setShowNewVersion(false)} className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] px-3 py-1.5 transition-colors">Cancel</button>
                  <button onClick={addVersion} disabled={!newVersionForm.content} className="text-xs px-4 py-1.5 bg-[var(--accent-indigo)] text-white rounded-md hover:opacity-90 disabled:opacity-40 transition-opacity">Save version</button>
                </div>
              </div>
            )}

            {/* Version list */}
            {[...selected.versions].reverse().map(v => (
              <div
                key={v.id}
                className={`bg-[var(--bg-secondary)] border rounded-xl overflow-hidden transition-colors ${
                  v.version === selected.current_version
                    ? 'border-[var(--accent-indigo)]/40'
                    : 'border-[var(--border-subtle)]'
                }`}
              >
                <div className="flex items-center gap-3 px-4 py-3">
                  <GitCommit size={14} className="text-[var(--text-muted)] shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-mono font-medium text-[var(--text-primary)]">v{v.version}</span>
                      {v.version === selected.current_version && (
                        <span className="text-xs px-1.5 py-0.5 bg-[var(--accent-indigo)]/20 text-[var(--accent-indigo)] rounded-full font-medium">current</span>
                      )}
                      {v.label && (
                        <span className="text-xs px-1.5 py-0.5 bg-[var(--bg-tertiary)] text-[var(--text-muted)] rounded-full">{v.label}</span>
                      )}
                    </div>
                    {v.commit_message && (
                      <div className="text-xs text-[var(--text-muted)] mt-0.5 truncate">{v.commit_message}</div>
                    )}
                  </div>

                  {/* Metrics */}
                  <div className="flex items-center gap-4 text-xs text-[var(--text-muted)] shrink-0">
                    {v.avg_cost_usd != null && <span>${v.avg_cost_usd.toFixed(4)} avg</span>}
                    {v.total_uses > 0 && <span>{v.total_uses} uses</span>}
                    {v.hallucination_rate != null && (
                      <span className={v.hallucination_rate > 0 ? 'text-red-400' : 'text-[#22c55e]'}>
                        {(v.hallucination_rate * 100).toFixed(1)}% halluc
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    {v.version !== selected.current_version && (
                      <button
                        onClick={() => promoteVersion(v.version)}
                        title="Promote to current"
                        className="text-xs flex items-center gap-1 px-2 py-1 text-[var(--text-tertiary)] hover:text-[var(--accent-indigo)] transition-colors"
                      >
                        <ArrowUp size={12} />
                        Promote
                      </button>
                    )}
                    <button
                      onClick={() => {
                        if (compareVersions) {
                          setCompareVersions([compareVersions[0], v.version]);
                        } else {
                          setCompareVersions([v.version, selected.current_version]);
                        }
                      }}
                      className="text-xs px-2 py-1 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      Diff
                    </button>
                    <button onClick={() => toggleVersionExpand(v.version)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                      {expandedVersions.has(v.version) ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </button>
                  </div>
                </div>

                {expandedVersions.has(v.version) && (
                  <div className="border-t border-[var(--border-subtle)] px-4 py-3">
                    <pre className="text-xs font-mono text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed">{v.content}</pre>
                  </div>
                )}
              </div>
            ))}

            {/* Diff view */}
            {compareVersionDiff && (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border-subtle)]">
                  <span className="text-xs font-medium text-[var(--text-secondary)]">
                    Diff: v{compareVersionDiff.vA.version} → v{compareVersionDiff.vB.version}
                  </span>
                  {/* Metric comparison */}
                  {compareVersionDiff.vA.avg_cost_usd != null && compareVersionDiff.vB.avg_cost_usd != null && (
                    <span className="text-xs text-[var(--text-muted)]">
                      Cost: ${compareVersionDiff.vA.avg_cost_usd.toFixed(4)} → ${compareVersionDiff.vB.avg_cost_usd.toFixed(4)}
                      {compareVersionDiff.vB.avg_cost_usd < compareVersionDiff.vA.avg_cost_usd && (
                        <span className="ml-1 text-[#22c55e]">↓ {((1 - compareVersionDiff.vB.avg_cost_usd / compareVersionDiff.vA.avg_cost_usd) * 100).toFixed(0)}%</span>
                      )}
                    </span>
                  )}
                </div>
                <div className="overflow-x-auto max-h-64">
                  {compareVersionDiff.diff.map((line, i) => (
                    <div
                      key={i}
                      className={`px-4 py-0.5 text-xs font-mono whitespace-pre ${
                        line.type === 'add' ? 'bg-green-950/40 text-green-300' :
                        line.type === 'remove' ? 'bg-red-950/40 text-red-300' :
                        'text-[var(--text-muted)]'
                      }`}
                    >
                      <span className="mr-2 select-none opacity-40">
                        {line.type === 'add' ? '+' : line.type === 'remove' ? '-' : ' '}
                      </span>
                      {line.text}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-2">
            <FileText size={32} className="mx-auto text-[var(--text-muted)]" />
            <p className="text-sm text-[var(--text-secondary)]">Select a prompt to view versions</p>
          </div>
        </div>
      )}

      {/* New Prompt Modal */}
      {showNewPrompt && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl w-full max-w-lg p-6 space-y-4">
            <h2 className="text-base font-semibold text-[var(--text-primary)]">New Prompt</h2>
            <div className="space-y-3">
              <input
                type="text"
                value={newPromptForm.name}
                onChange={e => setNewPromptForm(f => ({ ...f, name: e.target.value }))}
                placeholder="Prompt name (e.g. research_system_prompt)"
                className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] font-mono placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-indigo)]"
              />
              <input
                type="text"
                value={newPromptForm.description}
                onChange={e => setNewPromptForm(f => ({ ...f, description: e.target.value }))}
                placeholder="Description (optional)"
                className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-indigo)]"
              />
              <textarea
                value={newPromptForm.initial_content}
                onChange={e => setNewPromptForm(f => ({ ...f, initial_content: e.target.value }))}
                placeholder="Initial prompt content..."
                rows={6}
                className="w-full text-sm bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-[var(--text-primary)] font-mono placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-indigo)] resize-none"
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowNewPrompt(false)} className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] px-3 py-2 transition-colors">Cancel</button>
              <button
                onClick={createPrompt}
                disabled={!newPromptForm.name || !newPromptForm.initial_content}
                className="text-xs px-4 py-2 bg-[var(--accent-indigo)] text-white rounded-md hover:opacity-90 disabled:opacity-40 transition-opacity"
              >
                Create Prompt
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
