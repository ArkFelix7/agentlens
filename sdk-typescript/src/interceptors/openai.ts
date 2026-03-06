/** OpenAI auto-instrumentation for the AgentLens TypeScript SDK. */

import { SpanContext, getGlobalClient, getGlobalSessionId } from '../trace';

let patched = false;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyFn = (...args: any[]) => any;

export async function patchOpenAI(): Promise<void> {
  if (patched) return;
  try {
    // Dynamic import to avoid compile-time resolution failure when openai is not installed
    const openaiModule: { default: { prototype: Record<string, unknown> } } =
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await (Function('return import("openai")')() as Promise<any>);

    const OpenAI = openaiModule.default;
    if (!OpenAI?.prototype) return;

    const chatProto = OpenAI.prototype as Record<string, unknown>;
    const chat = chatProto['chat'] as Record<string, unknown> | undefined;
    const completions = chat?.['completions'] as Record<string, unknown> | undefined;
    const originalCreate = completions?.['create'] as AnyFn | undefined;

    if (!originalCreate) return;

    (completions as Record<string, unknown>)['create'] = async function (
      this: unknown,
      ...args: unknown[]
    ) {
      const client = getGlobalClient();
      const sessionId = getGlobalSessionId();
      if (!client || !sessionId) return originalCreate.apply(this, args);

      const span = new SpanContext('llm_call', 'openai.chat.completions.create', sessionId, client);
      const params = args[0] as Record<string, unknown> | undefined;
      if (params) {
        span.setInput({ model: params['model'], messages: params['messages'] });
        if (typeof params['model'] === 'string') span.setModel(params['model']);
      }
      try {
        const result = await originalCreate.apply(this, args);
        const choice = (result as Record<string, unknown[]>)?.['choices']?.[0] as
          | Record<string, unknown>
          | undefined;
        if (choice) {
          span.setOutput({ message: choice['message'] });
        }
        const usage = (result as Record<string, Record<string, number>>)?.['usage'];
        if (usage) {
          span.setTokens(usage['prompt_tokens'] || 0, usage['completion_tokens'] || 0);
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
    // OpenAI not installed or patch failed — skip silently
  }
}
