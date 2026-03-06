/** Anthropic auto-instrumentation for the AgentLens TypeScript SDK. */

import { SpanContext, getGlobalClient, getGlobalSessionId } from '../trace';

let patched = false;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyFn = (...args: any[]) => any;

export async function patchAnthropic(): Promise<void> {
  if (patched) return;
  try {
    // Dynamic import to avoid compile-time resolution failure when @anthropic-ai/sdk is not installed
    const anthropicModule: { default: { prototype: Record<string, unknown> } } =
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await (Function('return import("@anthropic-ai/sdk")')() as Promise<any>);

    const Anthropic = anthropicModule.default;
    if (!Anthropic?.prototype) return;

    const proto = Anthropic.prototype as Record<string, unknown>;
    const messages = proto['messages'] as Record<string, unknown> | undefined;
    const originalCreate = messages?.['create'] as AnyFn | undefined;

    if (!originalCreate) return;

    (messages as Record<string, unknown>)['create'] = async function (
      this: unknown,
      ...args: unknown[]
    ) {
      const client = getGlobalClient();
      const sessionId = getGlobalSessionId();
      if (!client || !sessionId) return originalCreate.apply(this, args);

      const span = new SpanContext('llm_call', 'anthropic.messages.create', sessionId, client);
      const params = args[0] as Record<string, unknown> | undefined;
      if (params) {
        span.setInput({ model: params['model'], messages: params['messages'] });
        if (typeof params['model'] === 'string') span.setModel(params['model']);
      }
      try {
        const result = await originalCreate.apply(this, args);
        const content = (result as Record<string, unknown>)?.['content'];
        if (content) span.setOutput({ content });
        const usage = (result as Record<string, Record<string, number>>)?.['usage'];
        if (usage) {
          span.setTokens(usage['input_tokens'] || 0, usage['output_tokens'] || 0);
        }
        return result;
      } catch (e) {
        span.setError(e instanceof Error ? e.message : String(e));
        throw e;
      } finally {
        span.end();
      }
    };

    patched = true;
  } catch {
    // Anthropic not installed or patch failed — skip silently
  }
}
