/** SDK configuration management. */

import { InitOptions } from './types';

export interface SDKConfig {
  serverUrl: string;
  httpUrl: string;
  agentName: string;
  sessionId: string;
  flushInterval: number;
  maxBufferSize: number;
  agentId?: string;
  agentRole?: string;
  parentSessionId?: string;
}

const SENSITIVE_KEYS = new Set(['api_key', 'token', 'password', 'secret', 'authorization', 'auth', 'bearer']);

let globalConfig: SDKConfig | null = null;

export function setConfig(options: InitOptions & { sessionId: string }): SDKConfig {
  globalConfig = {
    serverUrl: options.serverUrl || process.env.AGENTLENS_WS_URL || 'ws://localhost:8766/ws',
    httpUrl: options.httpUrl || process.env.AGENTLENS_HTTP_URL || 'http://localhost:8766',
    agentName: options.agentName || process.env.AGENTLENS_AGENT_NAME || 'typescript-agent',
    sessionId: options.sessionId,
    flushInterval: 1000,
    maxBufferSize: 20,
    agentId: options.agentId,
    agentRole: options.agentRole,
    parentSessionId: options.parentSessionId,
  };
  return globalConfig;
}

export function getConfig(): SDKConfig | null {
  return globalConfig;
}

export function redactSensitive(data: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(data)) {
    if (SENSITIVE_KEYS.has(k.toLowerCase())) {
      result[k] = '[REDACTED]';
    } else if (v && typeof v === 'object' && !Array.isArray(v)) {
      result[k] = redactSensitive(v as Record<string, unknown>);
    } else {
      result[k] = v;
    }
  }
  return result;
}
