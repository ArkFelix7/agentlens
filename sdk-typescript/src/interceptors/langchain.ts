/** LangChain.js callback handler for AgentLens tracing.
 *
 * Usage:
 *   import { AgentLensCallbackHandler } from '@agentlens-sdk/sdk/interceptors/langchain';
 *   const handler = new AgentLensCallbackHandler();
 *   const llm = new ChatOpenAI({ callbacks: [handler] });
 */

import { SpanContext, getGlobalClient, getGlobalSessionId } from '../trace';
import { ulid } from 'ulid';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyRecord = Record<string, any>;

export class AgentLensCallbackHandler {
  private _spans: Map<string, SpanContext> = new Map();

  private _getOrCreateSessionId(): string {
    return getGlobalSessionId() || ulid();
  }

  handleLLMStart(serialized: AnyRecord, prompts: string[], runId: string): void {
    try {
      const client = getGlobalClient();
      const sessionId = this._getOrCreateSessionId();
      const modelName: string = serialized?.['name'] || serialized?.['id']?.slice(-1)?.[0] || 'unknown';
      const span = new SpanContext('llm_call', `langchain:${modelName}`, sessionId, client);
      span.setInput({ prompts });
      this._spans.set(runId, span);
    } catch {}
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  handleLLMEnd(output: AnyRecord, runId: string): void {
    try {
      const span = this._spans.get(runId);
      if (!span) return;
      const generations: AnyRecord[][] = output?.['generations'] || [];
      if (generations.length > 0 && generations[0].length > 0) {
        const first = generations[0][0];
        span.setOutput({ content: first?.['text'] || String(first) });
      }
      const llmOutput: AnyRecord = output?.['llmOutput'] || {};
      const usage: AnyRecord = llmOutput?.['tokenUsage'] || {};
      if (usage) {
        span.setTokens(usage['promptTokens'] || 0, usage['completionTokens'] || 0);
      }
      span.end();
      this._spans.delete(runId);
    } catch {}
  }

  handleLLMError(error: Error, runId: string): void {
    try {
      const span = this._spans.get(runId);
      if (!span) return;
      span.setError(error?.message || String(error));
      span.end();
      this._spans.delete(runId);
    } catch {}
  }

  handleToolStart(serialized: AnyRecord, input: string, runId: string): void {
    try {
      const client = getGlobalClient();
      const sessionId = this._getOrCreateSessionId();
      const toolName: string = serialized?.['name'] || 'unknown_tool';
      const span = new SpanContext('tool_call', toolName, sessionId, client);
      span.setInput({ input });
      this._spans.set(runId, span);
    } catch {}
  }

  handleToolEnd(output: string, runId: string): void {
    try {
      const span = this._spans.get(runId);
      if (!span) return;
      span.setOutput({ output });
      span.end();
      this._spans.delete(runId);
    } catch {}
  }

  handleToolError(error: Error, runId: string): void {
    try {
      const span = this._spans.get(runId);
      if (!span) return;
      span.setError(error?.message || String(error));
      span.end();
      this._spans.delete(runId);
    } catch {}
  }

  handleChainStart(serialized: AnyRecord, inputs: AnyRecord, runId: string): void {
    try {
      const client = getGlobalClient();
      const sessionId = this._getOrCreateSessionId();
      const chainName: string = serialized?.['name'] || serialized?.['id']?.slice(-1)?.[0] || 'chain';
      const span = new SpanContext('decision', chainName, sessionId, client);
      span.setInput(inputs);
      this._spans.set(runId, span);
    } catch {}
  }

  handleChainEnd(outputs: AnyRecord, runId: string): void {
    try {
      const span = this._spans.get(runId);
      if (!span) return;
      span.setOutput(outputs);
      span.end();
      this._spans.delete(runId);
    } catch {}
  }

  handleChainError(error: Error, runId: string): void {
    try {
      const span = this._spans.get(runId);
      if (!span) return;
      span.setError(error?.message || String(error));
      span.end();
      this._spans.delete(runId);
    } catch {}
  }
}
