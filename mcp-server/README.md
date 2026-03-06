# agentlens-mcp

MCP server for [AgentLens](https://github.com/ArkFelix7/agentlens) — zero-code observability for any MCP-compatible agent (Claude Desktop, Cursor, Windsurf, etc.).

Any agent that supports MCP can send traces to AgentLens without installing the Python or TypeScript SDK.

## Install

```bash
pip install agentlens-mcp
```

## Prerequisites

Start the AgentLens server:

```bash
pip install agentlens-server
agentlens-server
```

## Configure in your MCP client

### Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "agentlens": {
      "command": "agentlens-mcp"
    }
  }
}
```

### Cursor / Windsurf

Add to your MCP server config:

```json
{
  "agentlens": {
    "command": "agentlens-mcp"
  }
}
```

## Tools Exposed

Once connected, your MCP agent can call these tools:

| Tool | Description |
|------|-------------|
| `agentlens_start_session` | Start a new debugging session. Returns a `session_id` to use in subsequent calls. |
| `agentlens_report_trace` | Report a trace event (LLM call, tool call, decision, memory op, error). |
| `agentlens_report_memory` | Report a memory state change (created, updated, accessed, deleted). |

## How It Works

The MCP server receives tool calls from your agent and forwards them to the AgentLens HTTP server (`http://localhost:8766`). Events appear in the dashboard in real-time.

```
Agent → MCP call → agentlens-mcp server → HTTP POST → AgentLens server → Dashboard
```

## Example Usage (inside a Claude conversation)

Once the MCP server is connected, Claude can instrument its own tasks:

```
1. Call agentlens_start_session → get session_id
2. For each tool call: agentlens_report_trace(session_id, event_type="tool_call", ...)
3. For each LLM decision: agentlens_report_trace(session_id, event_type="decision", ...)
```

Open `http://localhost:5173` to watch the trace build in real time.

## License

MIT
