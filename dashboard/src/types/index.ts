// ===== TRACE TYPES =====

export type EventType = 'llm_call' | 'tool_call' | 'decision' | 'memory_read' | 'memory_write' | 'user_input' | 'error';
export type EventStatus = 'success' | 'error' | 'pending';
export type Severity = 'critical' | 'warning' | 'info';
export type SessionStatus = 'active' | 'completed' | 'error';

export interface TraceEvent {
  id: string;
  session_id: string;
  parent_event_id: string | null;
  event_type: EventType;
  event_name: string;
  timestamp: string;              // ISO 8601
  duration_ms: number;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  model: string | null;
  tokens_input: number;
  tokens_output: number;
  cost_usd: number;
  status: EventStatus;
  error_message: string | null;
  metadata: Record<string, unknown> | null;
}

export interface TraceEventNode extends TraceEvent {
  children: TraceEventNode[];
}

// ===== SESSION TYPES =====

export interface Session {
  id: string;
  agent_name: string;
  started_at: string;
  ended_at: string | null;
  total_events: number;
  total_cost_usd: number;
  total_tokens_input: number;
  total_tokens_output: number;
  status: SessionStatus;
  metadata: Record<string, unknown> | null;
}

export interface SessionSummary {
  session_id: string;
  total_events: number;
  total_cost_usd: number;
  total_tokens: number;
  event_type_counts: Record<EventType, number>;
  models_used: string[];
  duration_ms: number;
  error_count: number;
}

// ===== COST TYPES =====

export interface CostBreakdown {
  total_usd: number;
  by_model: Record<string, { cost: number; tokens_input: number; tokens_output: number; call_count: number }>;
  by_step: Array<{ event_id: string; event_name: string; model: string; cost: number; tokens: number; percentage: number }>;
  timeline: Array<{ timestamp: string; cumulative_cost: number; event_name: string }>;
}

export interface CostHotspot {
  event_id: string;
  event_name: string;
  model: string;
  tokens_input: number;
  tokens_output: number;
  cost_usd: number;
  percentage_of_total: number;
}

export interface CostSuggestion {
  event_id: string;
  current_model: string;
  suggested_model: string;
  current_cost: number;
  estimated_savings: number;
  reason: string;
}

// ===== HALLUCINATION TYPES =====

export interface HallucinationAlert {
  id: string;
  session_id: string;
  trace_event_id: string;
  source_event_id: string;
  severity: Severity;
  description: string;
  expected_value: string;
  actual_value: string;
  similarity_score: number;
  detected_at: string;
}

export interface HallucinationSummary {
  total: number;
  critical: number;
  warning: number;
  info: number;
}

// ===== MEMORY TYPES =====

export type MemoryAction = 'created' | 'updated' | 'accessed' | 'deleted';

export interface MemoryEntry {
  id: string;
  session_id: string;
  agent_id: string;
  memory_key: string;
  content: string;
  action: MemoryAction;
  version: number;
  timestamp: string;
  influenced_events: string[] | null;
  metadata: Record<string, unknown> | null;
}

// ===== WEBSOCKET TYPES =====

export type WSMessageType =
  | 'trace_event'
  | 'session_start'
  | 'session_end'
  | 'hallucination_detected'
  | 'memory_update'
  | 'get_sessions'
  | 'get_session_events'
  | 'clear_session'
  | 'sessions_list'
  | 'session_events'
  | 'session_cleared'
  | 'ping'
  | 'pong';

export interface WSMessage {
  type: WSMessageType;
  data?: unknown;
  session_id?: string;
}

// ===== UI STATE TYPES =====

export interface ReplayState {
  session_id: string;
  events: TraceEvent[];
  current_step: number;
  is_playing: boolean;
  playback_speed: number;       // 0.5, 1, 2, 5
  total_steps: number;
}

export interface FilterState {
  event_types: EventType[];
  search_query: string;
  session_id: string | null;
}
