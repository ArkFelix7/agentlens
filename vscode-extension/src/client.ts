/** AgentLens server HTTP client — polls REST API using Node built-ins. */

import * as http from 'http';
import * as https from 'https';
import { URL } from 'url';

export interface Session {
  id: string;
  agent_name: string;
  started_at: string;
  ended_at: string | null;
  total_events: number;
  total_cost_usd: number;
  total_tokens_input: number;
  total_tokens_output: number;
  status: string;
}

export interface TraceEvent {
  id: string;
  session_id: string;
  event_type: string;
  event_name: string;
  timestamp: string;
  duration_ms: number;
  model: string | null;
  tokens_input: number;
  tokens_output: number;
  cost_usd: number;
  status: string;
}

export interface ScoreResult {
  session_id: string;
  score: number;
  grade: string;
  grade_color: string;
  hallucination_count: number;
  error_count: number;
  high_latency_count: number;
  total_cost_usd: number;
  penalties: Array<{ reason: string; points: number }>;
  badge_url: string;
}

function getJson(url: string): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const lib = parsed.protocol === 'https:' ? https : http;
    const req = lib.get(url, { timeout: 3000 }, (res) => {
      let data = '';
      res.on('data', (chunk: Buffer) => { data += chunk.toString(); });
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch { reject(new Error('Invalid JSON')); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

export class AgentLensClient {
  baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8766') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  async isHealthy(): Promise<boolean> {
    try {
      const data = await getJson(`${this.baseUrl}/health`) as { status: string };
      return data.status === 'healthy';
    } catch {
      return false;
    }
  }

  async getSessions(limit = 20): Promise<Session[]> {
    try {
      const data = await getJson(`${this.baseUrl}/api/v1/sessions?limit=${limit}`) as { sessions: Session[] } | Session[];
      if (Array.isArray(data)) return data;
      return (data as { sessions: Session[] }).sessions ?? [];
    } catch {
      return [];
    }
  }

  async getSessionEvents(sessionId: string): Promise<TraceEvent[]> {
    try {
      const data = await getJson(`${this.baseUrl}/api/v1/traces/${sessionId}`) as TraceEvent[] | { events: TraceEvent[] };
      if (Array.isArray(data)) return data;
      return (data as { events: TraceEvent[] }).events ?? [];
    } catch {
      return [];
    }
  }

  async getScore(sessionId: string): Promise<ScoreResult | null> {
    try {
      return await getJson(`${this.baseUrl}/api/v1/score/${sessionId}`) as ScoreResult;
    } catch {
      return null;
    }
  }

  setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/$/, '');
  }
}
