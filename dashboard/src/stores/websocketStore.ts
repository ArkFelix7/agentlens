/** Zustand store for WebSocket connection state. */

import { create } from 'zustand';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface WebSocketStore {
  status: ConnectionStatus;
  lastConnectedAt: string | null;
  reconnectAttempts: number;

  setStatus: (status: ConnectionStatus) => void;
  incrementReconnects: () => void;
  resetReconnects: () => void;
}

export const useWebSocketStore = create<WebSocketStore>((set) => ({
  status: 'disconnected',
  lastConnectedAt: null,
  reconnectAttempts: 0,

  setStatus: (status) =>
    set({
      status,
      lastConnectedAt: status === 'connected' ? new Date().toISOString() : undefined,
    }),

  incrementReconnects: () =>
    set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 })),

  resetReconnects: () => set({ reconnectAttempts: 0 }),
}));
