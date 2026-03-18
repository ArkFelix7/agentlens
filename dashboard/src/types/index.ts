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
  agent_id?: string | null;
  agent_role?: string | null;
  parent_session_id?: string | null;
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

// ===== SCORE TYPES =====

export interface ScoreResult {
  session_id: string;
  score: number;
  grade: 'A' | 'B' | 'C' | 'D';
  color: string;
  hallucination_count: number;
  error_count: number;
  mean_step_ms: number;
  cost_usd: number;
  penalty_breakdown: Record<string, number>;
}

// ===== BUDGET TYPES =====

export interface BudgetRule {
  id: string;
  rule_name: string;
  rule_type: 'cost_per_session' | 'cost_per_step' | 'loop_detection';
  threshold_usd: number | null;
  loop_max_calls: number | null;
  loop_window_seconds: number | null;
  webhook_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface BudgetAlert {
  session_id: string;
  rule_id: string;
  rule_name: string;
  rule_type: string;
  triggered_at: string;
  details: string;
}

export interface BudgetAlertMessage {
  type: 'budget_alert';
  data: BudgetAlert;
}

// ===== MULTI-AGENT TYPES =====

export interface AgentNode {
  id: string;
  agent_name: string;
  agent_id: string | null;
  agent_role: string | null;
  status: SessionStatus;
  total_cost_usd: number;
  total_events: number;
  children: AgentNode[];
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
  | 'budget_alert'
  | 'score_update'
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
