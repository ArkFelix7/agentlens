/** Zustand store for trace events. Manages current session's events and selection state. */

import { create } from 'zustand';
import { TraceEvent, FilterState, EventType } from '@/types';

interface TraceStore {
  events: TraceEvent[];
  selectedEventId: string | null;
  filter: FilterState;

  addEvent: (event: TraceEvent) => void;
  addEvents: (events: TraceEvent[]) => void;
  setEvents: (events: TraceEvent[]) => void;
  clearEvents: () => void;
  selectEvent: (id: string | null) => void;
  setFilter: (filter: Partial<FilterState>) => void;
  getFilteredEvents: () => TraceEvent[];
  getSelectedEvent: () => TraceEvent | null;
}

export const useTraceStore = create<TraceStore>((set, get) => ({
  events: [],
  selectedEventId: null,
  filter: {
    event_types: [],
    search_query: '',
    session_id: null,
  },

  addEvent: (event) =>
    set((state) => ({
      events: [...state.events, event],
    })),

  addEvents: (events) =>
    set((state) => ({
      events: [...state.events, ...events],
    })),

  setEvents: (events) => set({ events }),

  clearEvents: () => set({ events: [], selectedEventId: null }),

  selectEvent: (id) => set({ selectedEventId: id }),

  setFilter: (filter) =>
    set((state) => ({
      filter: { ...state.filter, ...filter },
    })),

  getFilteredEvents: () => {
    const { events, filter } = get();
    return events.filter((e) => {
      if (filter.session_id && e.session_id !== filter.session_id) return false;
      if (filter.event_types.length > 0 && !filter.event_types.includes(e.event_type)) return false;
      if (filter.search_query) {
        const q = filter.search_query.toLowerCase();
        if (
          !e.event_name.toLowerCase().includes(q) &&
          !(e.model?.toLowerCase().includes(q)) &&
          !e.event_type.includes(q)
        )
          return false;
      }
      return true;
    });
  },

  getSelectedEvent: () => {
    const { events, selectedEventId } = get();
    return events.find((e) => e.id === selectedEventId) || null;
  },
}));
