/** VCR-style playback controls for session replay. */

import React from 'react';
import { SkipBack, ChevronLeft, Play, Pause, ChevronRight, SkipForward } from 'lucide-react';
import { ReplayControls } from '@/hooks/useReplay';
import clsx from 'clsx';

interface ReplayPlayerProps {
  controls: ReplayControls;
}

const SPEED_OPTIONS = [0.5, 1, 2, 5];

export function ReplayPlayer({ controls }: ReplayPlayerProps) {
  const { currentStep, totalSteps, isPlaying, playbackSpeed, play, pause, stepForward, stepBack, jumpToStart, jumpToEnd, seekTo, setSpeed } = controls;

  return (
    <div className="flex items-center gap-4 px-4 py-3 bg-[var(--bg-secondary)] border-t border-[var(--border-subtle)]">
      {/* Control buttons */}
      <div className="flex items-center gap-1">
        <button onClick={jumpToStart} className="p-1.5 rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors" title="Jump to start">
          <SkipBack size={14} />
        </button>
        <button onClick={stepBack} className="p-1.5 rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors" title="Step back">
          <ChevronLeft size={14} />
        </button>
        <button
          onClick={isPlaying ? pause : play}
          className="p-2 rounded-lg bg-[var(--accent-indigo)] hover:bg-[var(--accent-indigo-hover)] text-white transition-colors"
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause size={14} /> : <Play size={14} />}
        </button>
        <button onClick={stepForward} className="p-1.5 rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors" title="Step forward">
          <ChevronRight size={14} />
        </button>
        <button onClick={jumpToEnd} className="p-1.5 rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors" title="Jump to end">
          <SkipForward size={14} />
        </button>
      </div>

      {/* Step counter */}
      <span className="text-xs font-mono text-[var(--text-secondary)] whitespace-nowrap">
        Step {currentStep} / {totalSteps}
      </span>

      {/* Scrubber */}
      <input
        type="range"
        min={0}
        max={totalSteps}
        value={currentStep}
        onChange={(e) => seekTo(Number(e.target.value))}
        className="flex-1 h-1 accent-[var(--accent-indigo)] cursor-pointer"
        aria-label="Replay scrubber"
      />

      {/* Speed selector */}
      <div className="flex items-center gap-1">
        <span className="text-xs text-[var(--text-tertiary)] font-mono">Speed:</span>
        <select
          value={playbackSpeed}
          onChange={(e) => setSpeed(Number(e.target.value))}
          className="bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded px-1 py-0.5 text-xs font-mono text-[var(--text-primary)] focus:outline-none"
        >
          {SPEED_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}x</option>
          ))}
        </select>
      </div>
    </div>
  );
}
