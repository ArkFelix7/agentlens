# AgentLens Examples

Four runnable demo agents showing different AgentLens integration patterns.

## Prerequisites

```bash
# Terminal 1 — start the server + dashboard
make dev

# Terminal 2 — run a demo
cd examples
python demo_multi_step.py
```

Open `http://localhost:5173` to see traces appear in real time.

## Demos

### `demo_multi_step.py` — Primary showcase

A multi-step research agent that demonstrates every AgentLens feature:

- 8+ trace events (tool calls, LLM calls, decisions, memory ops)
- Automatic hallucination detection — one number transposition is intentionally planted
- Memory inspector data — agent stores and reads a preference memory
- Works fully without any API key (uses realistic mock data)

```bash
python demo_multi_step.py
# Optional: set OPENAI_API_KEY or ANTHROPIC_API_KEY to use real LLM calls
```

What to look for in the dashboard:
- **Traces tab**: the full event graph with 8+ connected nodes
- **Hallucinations tab**: one CRITICAL alert (Revenue $2.3M reported as $3.2M)
- **Memory tab**: a stored user preference memory with version history
- **Costs tab**: per-step cost breakdown (real if using an API key, $0 for mock)
- **Replay tab**: step through the session event by event

---

### `demo_openai_agent.py` — Minimal @trace usage

The simplest possible integration: one function, one decorator.

```bash
export OPENAI_API_KEY=sk-...
python demo_openai_agent.py
# Falls back to mock response if no API key set
```

---

### `demo_anthropic_agent.py` — auto_instrument() usage

Shows `auto_instrument()` — zero changes to existing agent code.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python demo_anthropic_agent.py
# Falls back to mock response if no API key set
```

---

### `demo_langchain_agent.py` — LangChain CallbackHandler

Shows the LangChain integration via `AgentLensCallbackHandler`.

```bash
pip install langchain langchain-openai
export OPENAI_API_KEY=sk-...
python demo_langchain_agent.py
```
