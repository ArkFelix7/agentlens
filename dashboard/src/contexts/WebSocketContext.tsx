/** WebSocket context — provides requestSessionEvents and clearSession without creating extra connections. */

import React, { createContext, useContext } from 'react';

interface WebSocketContextValue {
  requestSessionEvents: (sessionId: string) => void;
  clearSession: (sessionId: string) => void;
}

export const WebSocketContext = createContext<WebSocketContextValue>({
  requestSessionEvents: () => {},
  clearSession: () => {},
});

export function useWebSocketContext(): WebSocketContextValue {
  return useContext(WebSocketContext);
}
