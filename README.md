<div align="center">

# AgentLens

### Chrome DevTools for AI Agents

**See every decision, trace every tool call, catch every hallucination.**

<!-- Demo GIF goes here — record with OBS, convert to GIF with gifski, place at public/demo.gif -->
<!-- ![AgentLens Demo](https://raw.githubusercontent.com/aarya/agentlens/main/dashboard/public/demo.gif) -->

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI SDK](https://img.shields.io/pypi/v/agentlens-sdk?label=agentlens-sdk)](https://pypi.org/project/agentlens-sdk/)
[![PyPI Server](https://img.shields.io/pypi/v/agentlens-server?label=agentlens-server)](https://pypi.org/project/agentlens-server/)
[![npm](https://img.shields.io/npm/v/@agentlens/sdk)](https://www.npmjs.com/package/@agentlens/sdk)

[Quick Start](#quick-start) · [Features](#features) · [Supported Frameworks](#supported-frameworks) · [MCP Integration](#mcp-integration) · [Examples](#examples) · [Contributing](#contributing)

</div>

---

## Why AgentLens?

AI agents fail in opaque ways — wrong data, hallucinated numbers, runaway costs, corrupted memory. AgentLens gives you a real-time debugging dashboard: every LLM call, tool execution, memory operation, and decision your agent makes — visible, searchable, replayable. Two lines of code to integrate, zero config to start.

## Quick Start

### 1. Install and run the server

```bash
pip install agentlens-server
agentlens-server
# Server: http://localhost:8766  |  Dashboard: http://localhost:5173
```

### 2. Install the Python SDK

```bash
pip install agentlens-sdk
```

### 3. Add two lines to your agent

```python
from agentlens_sdk import auto_instrument
auto_instrument()

# That's it. Open http://localhost:5173 and run your agent.
```

### TypeScript / Node.js

```bash
npm install @agentlens/sdk
```

```typescript
import { autoInstrument } from '@agentlens/sdk';
autoInstrument();
```

### Run from source (development)

```bash
git clone https://github.com/aarya/agentlens
cd agentlens
make install && make dev
```

## Features

| Feature | Description |
|---------|-------------|
| **Real-time Trace Graph** | D3.js force-directed graph — every agent step as a node, click for full input/output |
| **Cost Analytics** | Per-model, per-step cost breakdown with cheapermodel suggestions |
| **Hallucination Detection** | Semantic comparison of tool outputs vs LLM responses, number transposition alerts |
| **Memory Inspector** | Version history, influence mapping, in-dashboard edit/delete for agent memory |
| **Session Replay** | VCR-style playback of any past run, shareable replay links |

## Supported Frameworks

| Framework | Integration | How |
|-----------|-------------|-----|
| OpenAI | Auto | `auto_instrument()` |
| Anthropic | Auto | `auto_instrument()` |
| LangChain | Callback | `AgentLensCallbackHandler` |
| CrewAI | Auto-detect | `auto_instrument()` |
| AutoGen | Auto-detect | `auto_instrument()` |
| Semantic Kernel | Filter | `instrument_semantic_kernel(kernel)` |
| Any Python | Decorator | `@trace(name="my_step")` |
| TypeScript/Node | Wrapper | `trace(fn, { name: "my_step" })` |
| MCP agents | Zero-code | `agentlens-mcp` server |

## MCP Integration

Zero-code observability for Claude Desktop, Cursor, Windsurf, and any MCP-compatible agent.

```bash
pip install agentlens-mcp
```

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agentlens": {
      "command": "agentlens-mcp"
    }
  }
}
```

## Examples

See [`examples/`](./examples/) for four runnable demos:

- `demo_multi_step.py` — full showcase: 8+ steps, intentional hallucination, memory ops (no API key needed)
- `demo_openai_agent.py` — minimal `@trace` usage
- `demo_anthropic_agent.py` — `auto_instrument()` usage
- `demo_langchain_agent.py` — LangChain callback handler

```bash
make demo
```

## Contributing

PRs welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) for setup instructions and the architecture overview.

## License

MIT
