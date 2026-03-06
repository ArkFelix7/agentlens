/** Zustand store for user preferences. */

import { create } from 'zustand';

interface SettingsStore {
  wsUrl: string;
  apiUrl: string;
  theme: 'dark' | 'light';
  autoConnect: boolean;
  traceRetention: 10 | 50 | 100 | 'all';

  setWsUrl: (url: string) => void;
  setApiUrl: (url: string) => void;
  setTheme: (theme: 'dark' | 'light') => void;
  setAutoConnect: (v: boolean) => void;
  setTraceRetention: (v: 10 | 50 | 100 | 'all') => void;
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8766/ws',
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8766',
  theme: 'dark',
  autoConnect: true,
  traceRetention: 50,

  setWsUrl: (wsUrl) => set({ wsUrl }),
  setApiUrl: (apiUrl) => set({ apiUrl }),
  setTheme: (theme) => {
    set({ theme });
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.classList.toggle('light', theme === 'light');
  },
  setAutoConnect: (autoConnect) => set({ autoConnect }),
  setTraceRetention: (traceRetention) => set({ traceRetention }),
}));
