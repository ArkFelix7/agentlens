/** WebSocket/HTTP transport client for AgentLens TypeScript SDK.
 * Never throws exceptions to user code. Fails silently.
 */

import { SDKConfig } from './config';
import { TraceEventData } from './types';

type WsType = import('ws');

export class AgentLensClient {
  private ws: WsType | null = null;
  private buffer: TraceEventData[] = [];
  private connected = false;
  private flushTimer: NodeJS.Timeout | null = null;
  sessionId: string;
  private config: SDKConfig;

  constructor(config: SDKConfig) {
    this.config = config;
    this.sessionId = config.sessionId;
  }

  async connect(): Promise<void> {
    try {
      const WS = (await import('ws')).default;
      this.ws = new WS(this.config.serverUrl) as WsType;
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Connection timeout')), 3000);
        this.ws!.once('open', () => {
          clearTimeout(timeout);
          this.connected = true;
          // Identify as SDK client
          this.ws!.send(JSON.stringify({ type: 'hello', role: 'sdk' }));
          resolve();
        });
        this.ws!.once('error', (err) => {
          clearTimeout(timeout);
          reject(err);
        });
      });
      this.ws.on('close', () => { this.connected = false; });
      this.ws.on('error', () => { this.connected = false; });
      this.startFlushTimer();
    } catch {
      this.connected = false;
      console.warn('[AgentLens] Could not connect to server, using HTTP fallback.');
      this.startFlushTimer();
    }
  }

  sendEvent(event: TraceEventData): void {
    try {
      this.buffer.push(event);
      if (this.buffer.length >= this.config.maxBufferSize) {
        this.flush().catch(() => {});
      }
    } catch {
      // Silent failure
    }
  }

  private startFlushTimer(): void {
    if (this.flushTimer) return;
    this.flushTimer = setInterval(() => {
      this.flush().catch(() => {});
    }, this.config.flushInterval);
  }

  async flush(): Promise<void> {
    if (!this.buffer.length || !this.sessionId) return;
    const events = [...this.buffer];
    this.buffer = [];

    if (this.connected && this.ws) {
      try {
        this.ws.send(JSON.stringify({
          type: 'trace_events',
          session_id: this.sessionId,
          events,
        }));
        return;
      } catch {
        this.connected = false;
      }
    }

    // HTTP fallback
    await this.flushViaHttp(events);
  }

  private async flushViaHttp(events: TraceEventData[]): Promise<void> {
    try {
      const response = await fetch(`${this.config.httpUrl}/api/v1/traces`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: this.sessionId, events }),
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) {
        console.warn(`[AgentLens] HTTP flush failed: ${response.status}`);
      }
    } catch {
      // Silent failure
    }
  }

  async close(): Promise<void> {
    try {
      if (this.flushTimer) {
        clearInterval(this.flushTimer);
        this.flushTimer = null;
      }
      await this.flush();
      if (this.ws) {
        this.ws.close();
      }
    } catch {
      // Silent
    }
  }
}
