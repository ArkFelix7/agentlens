/** Generic callable wrapper for the AgentLens TypeScript SDK. */

import { SpanContext, getGlobalClient, getGlobalSessionId } from '../trace';
import { ulid } from 'ulid';
import { EventType } from '../types';

export function traceCallable<T extends (...args: unknown[]) => unknown>(
  fn: T,
  name?: string,
  eventType: EventType = 'tool_call',
): T {
  const eventName = name || fn.name || 'anonymous';

  const wrapper = async (...args: unknown[]): Promise<unknown> => {
    const client = getGlobalClient();
    const sessionId = getGlobalSessionId() || ulid();
    const span = new SpanContext(eventType, eventName, sessionId, client);
    try {
      const result = await (fn as (...a: unknown[]) => Promise<unknown>)(...args);
      return result;
    } catch (e) {
      span.setError(e instanceof Error ? e.message : String(e));
      throw e;
    } finally {
      span.end();
    }
  };

  return wrapper as unknown as T;
}
