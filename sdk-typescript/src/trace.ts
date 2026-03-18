/** trace() wrapper function and SpanContext for the TypeScript SDK. */

import { ulid } from 'ulid';
import { AgentLensClient } from './client';
import { TraceEventData, TraceOptions, EventType } from './types';
import { redactSensitive } from './config';

let globalClient: AgentLensClient | null = null;
let globalSessionId: string | null = null;

export function setGlobalClient(client: AgentLensClient, sessionId: string): void {
  globalClient = client;
  globalSessionId = sessionId;
}

export function getGlobalClient(): AgentLensClient | null {
  return globalClient;
}

export function getGlobalSessionId(): string | null {
  return globalSessionId;
}

export class SpanContext {
  readonly id: string;
  private startTime: number;
  private timestamp: string;
  private inputData: Record<string, unknown> | null = null;
  private outputData: Record<string, unknown> | null = null;
  private model: string | null = null;
  private tokensInput = 0;
  private tokensOutput = 0;
  private status: 'success' | 'error' = 'success';
  private errorMessage: string | null = null;
  private metadata: Record<string, unknown> | null = null;

  constructor(
    private eventType: EventType,
    private eventName: string,
    private sessionId: string,
    private client: AgentLensClient | null,
    private parentEventId?: string,
  ) {
    this.id = ulid();
    this.startTime = Date.now();
    this.timestamp = new Date().toISOString();
  }

  setInput(data: Record<string, unknown>): void {
    this.inputData = redactSensitive(data);
  }

  setOutput(data: Record<string, unknown>): void {
    this.outputData = redactSensitive(data);
  }

  setModel(model: string): void {
    this.model = model;
  }

  setTokens(inputTokens: number, outputTokens: number): void {
    this.tokensInput = inputTokens;
    this.tokensOutput = outputTokens;
  }

  setError(error: string): void {
    this.status = 'error';
    this.errorMessage = error;
  }

  setAttribute(key: string, value: unknown): void {
    if (!this.metadata) this.metadata = {};
    this.metadata[key] = value;
  }

  end(): void {
    try {
      const event: TraceEventData = {
        id: this.id,
        session_id: this.sessionId,
        parent_event_id: this.parentEventId || null,
        event_type: this.eventType,
        event_name: this.eventName,
        timestamp: this.timestamp,
        duration_ms: Date.now() - this.startTime,
        input_data: this.inputData,
        output_data: this.outputData,
        model: this.model,
        tokens_input: this.tokensInput,
        tokens_output: this.tokensOutput,
        status: this.status,
        error_message: this.errorMessage,
        metadata: this.metadata,
      };
      this.client?.sendEvent(event);
    } catch {
      // Silent
    }
  }
}

export function trace<T extends (...args: unknown[]) => unknown>(
  fn: T,
  options: TraceOptions = {},
): T {
  const eventName = options.name || fn.name || 'anonymous';
  const eventType: EventType = options.eventType || 'decision';

  // Build prompt metadata if provided (F10)
  const promptMeta: Record<string, unknown> = {};
  if (options.promptName) promptMeta['prompt_name'] = options.promptName;
  if (options.promptVersion) promptMeta['prompt_version'] = options.promptVersion;
  const hasPromptMeta = Object.keys(promptMeta).length > 0;

  // Detect if the original function is async
  const isAsync = fn.constructor?.name === 'AsyncFunction' ||
    (typeof fn === 'function' && fn.toString().startsWith('async '));

  if (isAsync) {
    const asyncWrapper = async (...args: unknown[]): Promise<unknown> => {
      const client = globalClient;
      const sessionId = globalSessionId || ulid();
      const span = new SpanContext(eventType, eventName, sessionId, client);
      if (hasPromptMeta) span.setAttribute('_prompt', promptMeta);
      try {
        const result = await (fn as (...a: unknown[]) => Promise<unknown>)(...args);
        if (result !== null && result !== undefined && typeof result !== 'object') {
          span.setOutput({ result: String(result) });
        } else if (result && typeof result === 'object') {
          span.setOutput(result as Record<string, unknown>);
        }
        return result;
      } catch (e) {
        span.setError(e instanceof Error ? e.message : String(e));
        throw e;
      } finally {
        span.end();
      }
    };
    return asyncWrapper as unknown as T;
  }

  const syncWrapper = (...args: unknown[]): unknown => {
    const client = globalClient;
    const sessionId = globalSessionId || ulid();
    const span = new SpanContext(eventType, eventName, sessionId, client);
    if (hasPromptMeta) span.setAttribute('_prompt', promptMeta);
    try {
      const result = (fn as (...a: unknown[]) => unknown)(...args);
      if (result !== null && result !== undefined && typeof result !== 'object') {
        span.setOutput({ result: String(result) });
      } else if (result && typeof result === 'object') {
        span.setOutput(result as Record<string, unknown>);
      }
      return result;
    } catch (e) {
      span.setError(e instanceof Error ? e.message : String(e));
      throw e;
    } finally {
      span.end();
    }
  };

  return syncWrapper as unknown as T;
}
