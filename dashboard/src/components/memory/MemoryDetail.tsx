/** Expanded view of a selected memory entry with version history, edit, and delete. */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { Pencil, Trash2, Check, X } from 'lucide-react';
import { MemoryEntry } from '@/types';

interface MemoryDetailProps {
  entry: MemoryEntry | null;
  history?: MemoryEntry[];
  onEdit?: (entry: MemoryEntry, newContent: string) => Promise<void>;
  onDelete?: (entry: MemoryEntry) => Promise<void>;
}

export function MemoryDetail({ entry, history = [], onEdit, onDelete }: MemoryDetailProps) {
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [saving, setSaving] = useState(false);

  if (!entry) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--text-tertiary)] text-sm font-mono">
        Select a memory entry to see details
      </div>
    );
  }

  const handleEdit = () => {
    setEditContent(entry.content);
    setEditMode(true);
    setConfirmDelete(false);
  };

  const handleSave = async () => {
    if (!onEdit || editContent === entry.content) { setEditMode(false); return; }
    setSaving(true);
    try { await onEdit(entry, editContent); } finally { setSaving(false); setEditMode(false); }
  };

  const handleDelete = async () => {
    if (!onDelete) return;
    setSaving(true);
    try { await onDelete(entry); } finally { setSaving(false); setConfirmDelete(false); }
  };

  return (
    <motion.div
      key={entry.id}
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2 }}
      className="h-full overflow-y-auto p-4 space-y-4"
    >
      {/* Header with actions */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs text-[var(--text-tertiary)] font-mono mb-1">Memory Key</p>
          <p className="text-sm font-mono font-semibold text-[var(--text-primary)]">{entry.memory_key}</p>
        </div>
        <div className="flex items-center gap-1 shrink-0 pt-4">
          {!editMode && !confirmDelete && (
            <>
              {onEdit && (
                <button
                  onClick={handleEdit}
                  className="p-1.5 rounded text-[var(--text-tertiary)] hover:text-[var(--accent-indigo)] hover:bg-[var(--bg-tertiary)] transition-colors"
                  title="Edit content"
                >
                  <Pencil size={13} />
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="p-1.5 rounded text-[var(--text-tertiary)] hover:text-red-400 hover:bg-[var(--bg-tertiary)] transition-colors"
                  title="Delete entry"
                >
                  <Trash2 size={13} />
                </button>
              )}
            </>
          )}
          {confirmDelete && (
            <div className="flex items-center gap-1">
              <span className="text-xs text-red-400 font-mono mr-1">Delete?</span>
              <button
                onClick={handleDelete}
                disabled={saving}
                className="p-1.5 rounded text-red-400 hover:bg-[var(--bg-tertiary)] transition-colors"
              >
                <Check size={13} />
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="p-1.5 rounded text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)] transition-colors"
              >
                <X size={13} />
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-[var(--bg-tertiary)] rounded p-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Created / Updated</p>
          <p className="text-[var(--text-primary)] font-mono">{format(new Date(entry.timestamp), 'MMM d, HH:mm:ss')}</p>
        </div>
        <div className="bg-[var(--bg-tertiary)] rounded p-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Version</p>
          <p className="text-[var(--text-primary)] font-mono">v{entry.version}</p>
        </div>
        <div className="bg-[var(--bg-tertiary)] rounded p-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Action</p>
          <p className="text-[var(--accent-cyan)] font-mono">{entry.action}</p>
        </div>
        <div className="bg-[var(--bg-tertiary)] rounded p-2">
          <p className="text-[var(--text-tertiary)] mb-0.5">Agent</p>
          <p className="text-[var(--text-primary)] font-mono">{entry.agent_id}</p>
        </div>
      </div>

      <div>
        <p className="text-xs text-[var(--text-tertiary)] font-mono mb-2">CONTENT</p>
        {editMode ? (
          <div className="space-y-2">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              rows={5}
              className="w-full bg-[var(--bg-secondary)] border border-[var(--accent-indigo)] rounded p-3 text-sm text-[var(--text-primary)] font-mono resize-y focus:outline-none"
            />
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-3 py-1.5 text-xs font-mono bg-[var(--accent-indigo)] text-white rounded hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={() => setEditMode(false)}
                className="px-3 py-1.5 text-xs font-mono bg-[var(--bg-tertiary)] text-[var(--text-secondary)] rounded hover:text-[var(--text-primary)] transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded p-3 text-sm text-[var(--text-primary)]">
            {entry.content}
          </div>
        )}
      </div>

      {entry.influenced_events && entry.influenced_events.length > 0 && (
        <div>
          <p className="text-xs text-[var(--text-tertiary)] font-mono mb-2">INFLUENCE MAP</p>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded p-3 space-y-1">
            <p className="text-xs text-[var(--text-secondary)]">
              This memory influenced {entry.influenced_events.length} event(s):
            </p>
            {entry.influenced_events.map((id) => (
              <p key={id} className="text-xs font-mono text-[var(--accent-indigo)]">• {id.slice(-12)}</p>
            ))}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div>
          <p className="text-xs text-[var(--text-tertiary)] font-mono mb-2">VERSION HISTORY</p>
          <div className="space-y-2">
            {history.map((h) => (
              <div key={h.id} className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded p-2 text-xs">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-mono text-[var(--text-tertiary)]">v{h.version}</span>
                  <span className="font-mono text-[var(--text-tertiary)]">{format(new Date(h.timestamp), 'HH:mm:ss')}</span>
                </div>
                <p className="text-[var(--text-secondary)] line-clamp-2">{h.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
