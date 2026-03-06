/** Zustand store for sessions. */

import { create } from 'zustand';
import { Session } from '@/types';

interface SessionStore {
  sessions: Session[];
  activeSessionId: string | null;

  setSessions: (sessions: Session[]) => void;
  addSession: (session: Session) => void;
  setActiveSession: (id: string | null) => void;
  getActiveSession: () => Session | null;
  removeSession: (id: string) => void;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  sessions: [],
  activeSessionId: null,

  setSessions: (sessions) => set({ sessions }),

  addSession: (session) =>
    set((state) => {
      const exists = state.sessions.some((s) => s.id === session.id);
      if (exists) return state;
      return { sessions: [session, ...state.sessions] };
    }),

  setActiveSession: (id) => set({ activeSessionId: id }),

  getActiveSession: () => {
    const { sessions, activeSessionId } = get();
    return sessions.find((s) => s.id === activeSessionId) || null;
  },

  removeSession: (id) =>
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== id),
      activeSessionId: state.activeSessionId === id ? null : state.activeSessionId,
    })),
}));
