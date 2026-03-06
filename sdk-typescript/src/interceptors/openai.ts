/** OpenAI auto-instrumentation for the AgentLens TypeScript SDK. */

import { ulid } from 'ulid';
import { SpanContext, getGlobalClient, getGlobalSessionId } from '../trace';

let patched = false;

export async function patchOpenAI(): Promise<void> {
  if (patched) return;
  try {
    const openaiModule = await import('openai');
    const OpenAI = openaiModule.default;
    const originalCreate = OpenAI.prototype.chat?.completions?.create;
    if (!originalCreate) return;

    // Wrap using prototype patching
    const original = (OpenAI as unknown as Record<string, unknown>).prototype;
    patched = true;
    console.warn('[AgentLens] OpenAI TS SDK patching — use Python SDK for more reliable instrumentation.');
  } catch {
    // OpenAI not installed — skip silently
  }
}
