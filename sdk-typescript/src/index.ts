/** AgentLens TypeScript SDK — public API exports.
 *
 * Usage:
 *   import { init, trace, autoInstrument } from '@agentlens-sdk/sdk';
 *   await init({ serverUrl: 'ws://localhost:8766/ws' });
 */

import { ulid } from 'ulid';
import { AgentLensClient } from './client';
import { setConfig, getConfig } from './config';
import { setGlobalClient } from './trace';
import { patchOpenAI } from './interceptors/openai';
import { patchAnthropic } from './interceptors/anthropic';

export { trace } from './trace';
export { SpanContext } from './trace';
export type { TraceEventData, InitOptions, TraceOptions, EventType, EventStatus } from './types';

let client: AgentLensClient | null = null;

/**
 * Initialize the AgentLens SDK. Call once at the start of your application.
 *
 * Multi-agent topology (F9): pass agentId, agentRole, and parentSessionId to
 * link this agent to a parent in the coordination map.
 */
export async function init(options: {
  serverUrl?: string;
  httpUrl?: string;
  agentName?: string;
  sessionId?: string;
  /** Unique agent identifier for multi-agent topology. */
  agentId?: string;
  /** Role label for this agent (e.g. "planner", "executor"). */
  agentRole?: string;
  /** Session ID of the parent agent — creates a topology edge in the dashboard. */
  parentSessionId?: string;
} = {}): Promise<void> {
  try {
    const sessionId = options.sessionId || ulid();
    const config = setConfig({ ...options, sessionId });
    client = new AgentLensClient(config);
    setGlobalClient(client, sessionId);
    await client.connect();
  } catch {
    // Silent failure
    console.warn('[AgentLens] Init failed silently — tracing disabled.');
  }
}

/**
 * Auto-instrument OpenAI and Anthropic Node SDKs.
 * Must be awaited before making any LLM calls to ensure patches are active.
 */
export async function autoInstrument(): Promise<void> {
  try { await patchOpenAI(); } catch {}
  try { await patchAnthropic(); } catch {}
}

/**
 * Fetch a prompt from the AgentLens prompt registry (F10).
 *
 * Returns the prompt text, or an empty string if unavailable.
 * Never throws — fails silently so agent code is not disrupted.
 *
 * @param name    Prompt name (e.g. "system_prompt")
 * @param version Specific version number. If omitted, fetches the current/promoted version.
 */
export async function getPrompt(name: string, version?: number): Promise<string> {
  try {
    const config = getConfig();
    if (!config) return '';
    const base = config.httpUrl.replace(/\/$/, '');
    const url = version !== undefined
      ? `${base}/api/v1/prompts/${encodeURIComponent(name)}/versions/${version}`
      : `${base}/api/v1/prompts/${encodeURIComponent(name)}/current`;
    const response = await fetch(url, { signal: AbortSignal.timeout(2000) });
    if (!response.ok) return '';
    if (version !== undefined) {
      const data = await response.json() as { content?: string };
      return data.content ?? '';
    }
    return await response.text();
  } catch {
    return '';
  }
}

/**
 * Flush buffered events and close the connection.
 */
export async function shutdown(): Promise<void> {
  try {
    await client?.close();
  } catch {}
}
