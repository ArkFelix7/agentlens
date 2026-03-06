# agentlens-sdk

Python SDK for [AgentLens](https://github.com/ArkFelix7/agentlens) — real-time observability and debugging for AI agents.

## Install

```bash
pip install agentlens-sdk
```

With framework extras:

```bash
pip install "agentlens-sdk[openai]"
pip install "agentlens-sdk[anthropic]"
pip install "agentlens-sdk[langchain]"
pip install "agentlens-sdk[all]"
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

```python
from agentlens_sdk import auto_instrument

auto_instrument()  # patches OpenAI + Anthropic clients automatically

# All subsequent OpenAI/Anthropic calls are traced — no other changes needed
import openai
client = openai.AsyncOpenAI()
response = await client.chat.completions.create(...)
```

### Option 2: @trace decorator

```python
from agentlens_sdk import init, trace

init(server_url="ws://localhost:8766/ws")

@trace(name="my_agent")
async def my_agent(query: str) -> str:
    result = await call_llm(query)
    return result
```

### Option 3: Manual spans

```python
from agentlens_sdk import get_tracer

async def my_agent(query: str) -> str:
    with get_tracer().span("my_agent") as span:
        span.set_attribute("query", query)
        result = await call_llm(query)
        span.set_output(result)
        return result
```

## Framework Integrations

### LangChain

```python
from agentlens_sdk.interceptors.langchain_interceptor import AgentLensCallbackHandler

handler = AgentLensCallbackHandler()
chain = my_chain.with_config(callbacks=[handler])
```

### CrewAI

```python
from agentlens_sdk import auto_instrument
auto_instrument()  # CrewAI is auto-detected
```

### AutoGen

```python
from agentlens_sdk import auto_instrument
auto_instrument()  # AutoGen ConversableAgent is auto-detected
```

## Configuration

```python
from agentlens_sdk import init

init(
    server_url="ws://localhost:8766/ws",   # AgentLens server WebSocket URL
    http_url="http://localhost:8766",       # AgentLens server HTTP URL
    session_name="my-agent-v2",            # Optional: name shown in dashboard
)
```

## Design Principles

- **Never raises exceptions** — all SDK operations are silent on failure. Your agent always runs.
- **Non-blocking** — async, buffered, batch-sent. Adds <5ms overhead per traced call.
- **Auto session management** — creates a session on first event, closes it on process exit.
- **Sensitive data redaction** — fields named `api_key`, `token`, `password`, `secret`, `authorization` are automatically replaced with `[REDACTED]`.
- **Graceful degradation** — if the server isn't running, events are silently dropped.

## License

MIT
