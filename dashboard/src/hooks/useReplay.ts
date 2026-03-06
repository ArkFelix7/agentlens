/** Session replay playback hook. Manages replay state and step progression. */

import { useState, useEffect, useRef, useCallback } from 'react';
import { TraceEvent } from '@/types';

export interface ReplayControls {
  currentStep: number;
  totalSteps: number;
  isPlaying: boolean;
  playbackSpeed: number;
  visibleEvents: TraceEvent[];
  play: () => void;
  pause: () => void;
  stepForward: () => void;
  stepBack: () => void;
  jumpToStart: () => void;
  jumpToEnd: () => void;
  seekTo: (step: number) => void;
  setSpeed: (speed: number) => void;
}

const SPEED_OPTIONS = [0.5, 1, 2, 5];

export function useReplay(events: TraceEvent[]): ReplayControls {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const totalSteps = events.length;

  // Auto-advance when playing
  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearTimeout(timerRef.current);
      return;
    }
    if (currentStep >= totalSteps) {
      setIsPlaying(false);
      return;
    }
    timerRef.current = setTimeout(() => {
      setCurrentStep((s) => Math.min(s + 1, totalSteps));
    }, 1000 / playbackSpeed);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isPlaying, currentStep, totalSteps, playbackSpeed]);

  const play = useCallback(() => setIsPlaying(true), []);
  const pause = useCallback(() => setIsPlaying(false), []);
  const stepForward = useCallback(() => setCurrentStep((s) => Math.min(s + 1, totalSteps)), [totalSteps]);
  const stepBack = useCallback(() => setCurrentStep((s) => Math.max(s - 1, 0)), []);
  const jumpToStart = useCallback(() => { setCurrentStep(0); setIsPlaying(false); }, []);
  const jumpToEnd = useCallback(() => { setCurrentStep(totalSteps); setIsPlaying(false); }, [totalSteps]);
  const seekTo = useCallback((step: number) => setCurrentStep(Math.max(0, Math.min(step, totalSteps))), [totalSteps]);
  const setSpeed = useCallback((speed: number) => setPlaybackSpeed(speed), []);

  const visibleEvents = events.slice(0, currentStep);

  return {
    currentStep,
    totalSteps,
    isPlaying,
    playbackSpeed,
    visibleEvents,
    play,
    pause,
    stepForward,
    stepBack,
    jumpToStart,
    jumpToEnd,
    seekTo,
    setSpeed,
  };
}
