/** Type definitions for the AgentLens TypeScript SDK. */

export type EventType = 'llm_call' | 'tool_call' | 'decision' | 'memory_read' | 'memory_write' | 'user_input' | 'error';
export type EventStatus = 'success' | 'error' | 'pending';

export interface TraceEventData {
  id: string;
  session_id: string;
  parent_event_id?: string | null;
  event_type: EventType;
  event_name: string;
  timestamp: string;
  duration_ms: number;
  input_data?: Record<string, unknown> | null;
  output_data?: Record<string, unknown> | null;
  model?: string | null;
  tokens_input: number;
  tokens_output: number;
  cost_usd?: number | null;
  status: EventStatus;
  error_message?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface InitOptions {
  serverUrl?: string;
  httpUrl?: string;
  agentName?: string;
  sessionId?: string;
}

export interface TraceOptions {
  name?: string;
  eventType?: EventType;
}
