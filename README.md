<div align="center">

# AgentLens

### Chrome DevTools for AI Agents

**See every decision, trace every tool call, catch every hallucination.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/agentlens)](https://pypi.org/project/agentlens/)

[Quick Start](#quick-start) · [Documentation](#documentation) · [Examples](#examples) · [Contributing](#contributing)

</div>

---

## Why AgentLens?

AI agents fail in opaque ways — wrong data, hallucinated numbers, runaway costs. AgentLens gives you a real-time debugging dashboard that shows every LLM call, tool execution, memory operation, and decision your agent makes, with automatic hallucination detection built in.

## Quick Start

### 1. Install & run the server

```bash
cd server && pip install -e .
uvicorn src.main:app --port 8766
```

### 2. Install the SDK

```bash
pip install agentlens
```

### 3. Add two lines to your agent

```python
from agentlens import auto_instrument
auto_instrument()

# That's it. Open http://localhost:5173
```

Or use `make install && make dev` from the repo root.

## Features

- **Real-time Trace Graph** — D3.js force-directed graph showing every agent step
- **Cost Analytics** — Per-model cost breakdown with optimization suggestions
- **Hallucination Detection** — Automatic comparison of tool outputs vs LLM outputs
- **Memory Inspector** — Version history and influence mapping for agent memory
- **Session Replay** — Step through any past agent run frame by frame

## Supported Frameworks

| Framework | Support |
|-----------|---------|
| OpenAI | ✅ Auto-instrumented |
| Anthropic | ✅ Auto-instrumented |
| LangChain | ✅ Callback handler |
| Raw Python | ✅ `@trace` decorator |
| TypeScript/Node | ✅ TS SDK |
| MCP agents | ✅ MCP server |

## MCP Integration

Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "agentlens": {
      "command": "python",
      "args": ["-m", "agentlens_mcp.server"]
    }
  }
}
```

## Contributing

PRs welcome. Please read the PRD (`AgentLens_PRD.md`) for architecture details.

## License

MIT
