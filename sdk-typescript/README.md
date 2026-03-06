# @agentlens-sdk/sdk

TypeScript/Node.js SDK for [AgentLens](https://github.com/ArkFelix7/agentlens) — real-time observability and debugging for AI agents.

## Install

```bash
npm install @agentlens-sdk/sdk
```

With peer dependencies for your AI provider:

```bash
npm install @agentlens-sdk/sdk openai                  # for OpenAI
npm install @agentlens-sdk/sdk @anthropic-ai/sdk       # for Anthropic
```

## Prerequisites

Start the AgentLens server first:

```bash
pip install agentlens-server
agentlens-server
# Server running at http://localhost:8766
```

Then open the dashboard at `http://localhost:5173`.

## Usage

### Option 1: Auto-instrument (recommended)

```typescript
import { autoInstrument } from '@agentlens-sdk/sdk';

autoInstrument(); // patches OpenAI + Anthropic Node SDKs

// All subsequent calls are traced automatically
import OpenAI from 'openai';
const client = new OpenAI();
const response = await client.chat.completions.create({ ... });
```

### Option 2: trace() wrapper

```typescript
import { init, trace } from '@agentlens-sdk/sdk';

init({ serverUrl: 'ws://localhost:8766/ws' });

const myAgent = trace(
  async (query: string) => {
    const result = await callLLM(query);
    return result;
  },
  { name: 'my_agent' }
);
```

## Configuration

```typescript
import { init } from '@agentlens-sdk/sdk';

init({
  serverUrl: 'ws://localhost:8766/ws',   // AgentLens server WebSocket URL
  httpUrl: 'http://localhost:8766',       // AgentLens server HTTP URL
  sessionName: 'my-agent-v2',            // Optional: name shown in dashboard
});
```

## Design Principles

- **Never throws** — all SDK operations are wrapped in try/catch. Your agent always runs.
- **Non-blocking** — async, buffered batch sends. Minimal overhead.
- **Graceful degradation** — if the server isn't running, events are silently dropped.

## License

MIT
