/** AgentLens TypeScript SDK — public API exports.
 *
 * Usage:
 *   import { init, trace, autoInstrument } from '@agentlens-sdk/sdk';
 *   init({ serverUrl: 'ws://localhost:8766/ws' });
 */

import { ulid } from 'ulid';
import { AgentLensClient } from './client';
import { setConfig } from './config';
import { setGlobalClient } from './trace';
import { patchOpenAI } from './interceptors/openai';
import { patchAnthropic } from './interceptors/anthropic';

export { trace } from './trace';
export { SpanContext } from './trace';
export type { TraceEventData, InitOptions, TraceOptions, EventType, EventStatus } from './types';

let client: AgentLensClient | null = null;

/**
 * Initialize the AgentLens SDK. Call once at the start of your application.
 */
export async function init(options: {
  serverUrl?: string;
  httpUrl?: string;
  agentName?: string;
  sessionId?: string;
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
 */
export async function autoInstrument(): Promise<void> {
  try { await patchOpenAI(); } catch {}
  try { await patchAnthropic(); } catch {}
}

/**
 * Flush buffered events and close the connection.
 */
export async function shutdown(): Promise<void> {
  try {
    await client?.close();
  } catch {}
}
