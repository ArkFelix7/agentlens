/** WebSocket connection hook. Auto-reconnects on disconnect. */

import { useEffect, useRef, useCallback } from 'react';
import { useSettingsStore } from '@/stores/settingsStore';
import { useWebSocketStore } from '@/stores/websocketStore';
import { useTraceStore } from '@/stores/traceStore';
import { useSessionStore } from '@/stores/sessionStore';
import { WSMessage, TraceEvent, Session } from '@/types';

// Global budget alert event emitter (simple pub-sub for cross-component alerts)
type BudgetAlertListener = (alert: unknown) => void;
const _budgetListeners: Set<BudgetAlertListener> = new Set();
export function onBudgetAlert(fn: BudgetAlertListener) { _budgetListeners.add(fn); return () => _budgetListeners.delete(fn); }
function _emitBudgetAlert(alert: unknown) { _budgetListeners.forEach(fn => fn(alert)); }

const RECONNECT_DELAY = 5000;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { wsUrl, autoConnect } = useSettingsStore();
  const { setStatus, incrementReconnects, resetReconnects } = useWebSocketStore();
  const { addEvent, setEvents } = useTraceStore();
  const { setSessions, addSession, removeSession } = useSessionStore();

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const msg: WSMessage = JSON.parse(event.data as string);

      switch (msg.type) {
        case 'trace_event': {
          const traceEvent = msg.data as TraceEvent;
          if (traceEvent) addEvent(traceEvent);
          break;
        }
        case 'session_start': {
          const sessionData = msg.data as Session;
          if (sessionData) addSession(sessionData);
          break;
        }
        case 'sessions_list': {
          const sessions = msg.data as Session[];
          if (sessions) setSessions(sessions);
          break;
        }
        case 'session_events': {
          const events = msg.data as TraceEvent[];
          if (events) setEvents(events);
          break;
        }
        case 'session_cleared': {
          if (msg.session_id) removeSession(msg.session_id);
          break;
        }
        case 'ping': {
          wsRef.current?.send(JSON.stringify({ type: 'pong' }));
          break;
        }
        case 'budget_alert': {
          _emitBudgetAlert(msg.data);
          break;
        }
        default:
          break;
      }
    } catch (e) {
      console.warn('[AgentLens WS] Failed to parse message:', e);
    }
  }, [addEvent, setEvents, setSessions, addSession, removeSession]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    setStatus('connecting');

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        resetReconnects();
        // Identify as dashboard
        ws.send(JSON.stringify({ type: 'hello', role: 'dashboard' }));
        // Request session list on connect
        ws.send(JSON.stringify({ type: 'get_sessions' }));
      };

      ws.onmessage = handleMessage;

      ws.onclose = () => {
        setStatus('disconnected');
        wsRef.current = null;
        if (autoConnect) {
          incrementReconnects();
          reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY);
        }
      };

      ws.onerror = () => {
        setStatus('error');
      };
    } catch (e) {
      setStatus('error');
      if (autoConnect) {
        reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY);
      }
    }
  }, [wsUrl, autoConnect, setStatus, resetReconnects, incrementReconnects, handleMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const requestSessionEvents = useCallback((sessionId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'get_session_events', session_id: sessionId }));
    }
  }, []);

  const clearSession = useCallback((sessionId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'clear_session', session_id: sessionId }));
    }
  }, []);

  return { requestSessionEvents, clearSession };
}
