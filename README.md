<div align="center">

# AgentLens

### Chrome DevTools for AI Agents

**See every decision, trace every tool call, catch every hallucination.**

![AgentLens Demo](https://raw.githubusercontent.com/ArkFelix7/agentlens/main/demo.gif)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI SDK](https://img.shields.io/pypi/v/agentlens-sdk?label=agentlens-sdk&cacheSeconds=300)](https://pypi.org/project/agentlens-sdk/)
[![PyPI Server](https://img.shields.io/pypi/v/agentlens-server?label=agentlens-server&cacheSeconds=300)](https://pypi.org/project/agentlens-server/)
[![npm](https://img.shields.io/npm/v/@agentlens-sdk/sdk)](https://www.npmjs.com/package/@agentlens-sdk/sdk)

[Quick Start](#quick-start) · [Features](#features) · [VS Code Extension](#vs-code-extension) · [GitHub Actions CI](#github-actions-ci) · [Supported Frameworks](#supported-frameworks) · [MCP Integration](#mcp-integration) · [Examples](#examples) · [Contributing](#contributing)

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
npm install @agentlens-sdk/sdk
```

```typescript
import { autoInstrument } from '@agentlens-sdk/sdk';
autoInstrument();
```

### Run from source (development)

```bash
git clone https://github.com/ArkFelix7/agentlens
cd agentlens
make install && make dev
```

## Features

### Core Observability

| Feature | Description |
|---------|-------------|
| **Real-time Trace Graph** | D3.js force-directed graph — every agent step as a node, click for full input/output |
| **Cost Analytics** | Per-model, per-step cost breakdown with cheaper-model suggestions |
| **Hallucination Detection** | Semantic comparison of tool outputs vs LLM responses, number transposition alerts |
| **Memory Inspector** | Version history, influence mapping, in-dashboard edit/delete for agent memory |
| **Session Replay** | VCR-style playback of any past run, shareable replay links |

### v0.2 — New Features

| Feature | Description |
|---------|-------------|
| **Reliability Score Badge** | 0–100 score (A/B/C/D) grading a session on hallucinations, errors, cost, and latency. Embeddable SVG badge for any README. |
| **Budget Guardrails** | Set per-session or per-model cost/token/call limits. Real-time alerts fire the moment a running agent crosses a threshold. |
| **Auto Test Generation** | One click turns any trace into a pytest fixture — captures inputs, outputs, and assertions so production failures become regression tests. |
| **LLM Model Comparison** | Replay any session with a different model and diff the outputs side-by-side. Compare cost, latency, and accuracy across GPT-4o, Claude, Gemini. |
| **Prompt Version Control** | Track every prompt edit, compare versions, and run A/B experiments across sessions — all without leaving the dashboard. |
| **Multi-Agent Topology Map** | Visual coordination graph for CrewAI, AutoGen, and custom multi-agent setups — see which agent called which, when, and at what cost. |
| **Air-Gap Privacy Mode** | Redact PII from traces before they reach the server. Full local-only mode with no external network calls. |
| **VS Code / Cursor Extension** | Inline cost and latency annotations on `@trace` decorated functions. Sidebar showing the last trace without leaving your editor. |
| **GitHub Actions CI** | Post a trace quality report as a PR comment — hallucination count, cost, reliability score, and test pass/fail. |

## VS Code Extension

Install from the VS Code Marketplace or build from source:

```bash
cd vscode-extension
npm install
npm run compile
# Then: Extensions panel → "Install from VSIX..." → select the generated .vsix
```

Features:
- Inline cost and latency annotations on any `@trace`-decorated function
- Sidebar panel with real-time trace feed
- Command palette: `AgentLens: Show Last Trace`, `AgentLens: Toggle Cost Annotations`
- Auto-connects to `http://localhost:8766` on startup (configurable)

## GitHub Actions CI

Add to any repo to get automatic trace quality checks on every PR:

```yaml
# .github/workflows/agent-check.yml
name: Agent Trace Check
on: [pull_request]

jobs:
  trace-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ArkFelix7/agentlens/.github/actions/agentlens-check@v0.2.0
        with:
          script: python my_agent.py
          fail-on-hallucination: 'true'
          max-cost-usd: '0.10'
```

Posts a comment to the PR with: reliability score, hallucination count, total cost, and latency breakdown.

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

See [`examples/`](./examples/) for five runnable demos:

- `demo_multi_step.py` — full showcase: 8+ steps, intentional hallucination, memory ops (no API key needed)
- `demo_multi_agent.py` — multi-agent topology: orchestrator spawning researcher + writer agents
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
