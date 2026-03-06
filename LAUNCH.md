# AgentLens — Launch Content

Ready-to-paste content for launch day. Execute in the order listed.

---

## Launch Order

| Day | Platform | Action |
|-----|----------|--------|
| Monday | Twitter/X | Post demo video thread (soft launch) |
| Tuesday 9am EST | Hacker News | Submit Show HN |
| Tuesday | Reddit | r/MachineLearning, r/LocalLLaMA, r/artificial |
| Wednesday | LinkedIn | Professional ML audience post |
| Thursday | Dev.to + Hashnode | Cross-post launch blog |
| Friday | GitHub | Respond to every issue opened this week |

---

## Hacker News — Show HN Post

**Title:**
```
Show HN: AgentLens – Open-Source Chrome DevTools for AI Agents
```

**First comment (post this yourself immediately after submitting):**
```
I built this out of frustration. I was debugging a multi-step agent by staring at
JSON logs, trying to figure out why step 8 was wrong. The bug was a number transposition
in step 3 — the agent read "$2.3M" from a tool and wrote "$3.2M" into its report.
I had no way to know that automatically.

AgentLens fixes that. Two lines to integrate:

  from agentlens_sdk import auto_instrument
  auto_instrument()

Then you get a real-time graph of every LLM call, tool invocation, and decision
your agent makes, with automatic hallucination detection that cross-checks numbers
and facts between tool outputs and LLM responses.

Works with OpenAI, Anthropic, LangChain, CrewAI, AutoGen, Semantic Kernel, and
any MCP-compatible agent (Claude Desktop, Cursor). Free, MIT, runs 100% locally on
SQLite with no API keys needed.

The demo agent in /examples intentionally plants a hallucination — the hallucination
detector catches it every time.

Happy to answer questions about any of the implementation decisions.
```

---

## Twitter/X Thread

**Tweet 1 (with demo video attached):**
```
I built Chrome DevTools for AI agents.

Every LLM call. Every tool invocation. Every number your agent hallucinated.
All visible in real time.

Two lines to instrument any agent:

  from agentlens_sdk import auto_instrument
  auto_instrument()

Open-source, MIT, runs locally. [link]

Thread on what I learned building this: 🧵
```

**Tweet 2:**
```
The debugging problem that motivated this:

Step 3: tool returns {"revenue": "$2.3M"}
Step 8: agent reports "Revenue: $3.2M"

That transposition is impossible to catch without tooling.
AgentLens catches it automatically — scans every number the agent writes
and cross-checks it against every tool response in the same session.

Hallucination Inspector tab shows you exactly where it went wrong.
```

**Tweet 3:**
```
The Cost tab is the one I use daily.

Before AgentLens: "why is this agent costing $0.80 per run?"
After: "oh, it's calling gpt-4o for a step that produces 40 output tokens.
That's gpt-4o-mini territory."

AgentLens flags those automatically. Saved ~60% on my own agent's API costs.
```

**Tweet 4:**
```
Frameworks supported:

✅ OpenAI — auto_instrument()
✅ Anthropic — auto_instrument()
✅ LangChain — callback handler
✅ CrewAI — auto-detected
✅ AutoGen — auto-detected
✅ Semantic Kernel — filter API
✅ MCP agents — zero-code (Claude Desktop, Cursor)
✅ Any Python — @trace decorator
✅ TypeScript/Node — @agentlens/sdk on npm
```

**Tweet 5:**
```
The Session Replay tab is my favorite feature.

After a failed agent run, you can scrub back through every step,
see the full input/output at each point, and share a link
with your team that opens the exact same replay.

[link to GitHub]
[link to demo video]

pip install agentlens-sdk agentlens-server
```

---

## Reddit Posts

### r/MachineLearning

**Title:** AgentLens — Open-source real-time debugger for AI agents (hallucination detection, cost tracking, session replay)

```
I've been building AI agents for the past few months and got tired of debugging
with print statements. So I built AgentLens — an open-source observability dashboard
that shows you every LLM call, tool invocation, and decision your agent makes in real time.

Key features:
- Real-time trace graph (D3.js force-directed, one node per agent step)
- Automatic hallucination detection (cross-checks numbers and facts between tool outputs and LLM responses)
- Per-step cost breakdown with optimization suggestions
- Memory inspector with version history and influence mapping
- Session replay with shareable links

Two lines to integrate:
```python
from agentlens_sdk import auto_instrument
auto_instrument()
```

Works with OpenAI, Anthropic, LangChain, CrewAI, AutoGen, Semantic Kernel, and
any MCP-compatible agent. Runs fully locally on SQLite, MIT license, no API keys needed.

The demo agent in /examples intentionally plants a hallucination — the detector
catches it on every run, which is a good sanity check.

GitHub: [link]
```

### r/LocalLLaMA

**Title:** Built an open-source debugging dashboard for local LLM agents — real-time traces, hallucination detection, cost tracking

```
For anyone running local agents (Ollama, LM Studio, etc.) or experimenting
with Anthropic/OpenAI agents — I built a dashboard that gives you visibility
into what your agent is actually doing.

It's called AgentLens. Runs 100% locally, MIT license, no cloud services required.

What it shows:
- Every LLM call and tool invocation as a visual graph
- Input/output for every single step
- Token costs (useful even for local models where you care about throughput)
- Automatic hallucination detection
- Session replay

Install:
```bash
pip install agentlens-server agentlens-sdk
agentlens-server  # starts on localhost:8766
```

Then two lines in your agent code:
```python
from agentlens_sdk import auto_instrument
auto_instrument()
```

Open http://localhost:5173 — the dashboard appears with live traces as your agent runs.

GitHub: [link]
Happy to answer questions.
```

---

## Launch Blog Post

**Title:** I Built Chrome DevTools for AI Agents

**Outline:**

```
---

# I Built Chrome DevTools for AI Agents

Every web developer has been there: something's broken, you open Chrome DevTools,
you see the exact network request that failed, the exact payload, the exact error.
Fixed in five minutes.

Every AI agent developer has also been there: something's wrong with your agent's
output, you stare at the logs, you add more print statements, you re-run the agent,
you stare at more logs. Not fixed in five minutes.

That gap annoyed me enough that I spent the last few months building a fix.
It's called AgentLens.

## The Problem

[Describe the three specific debugging nightmares with concrete examples:
 1. Number transposition hallucination you can't see
 2. No idea which step is consuming 80% of your token budget
 3. No way to replay what happened after a failure]

## What AgentLens Does

[Walk through each tab with a screenshot:
 1. Trace Graph — real-time D3 graph, click any node for full I/O
 2. Cost Analytics — per-step breakdown, suggests gpt-4o → gpt-4o-mini where applicable
 3. Hallucination Inspector — the number transposition it caught in my own demo
 4. Memory Inspector — version history + influence mapping
 5. Session Replay — scrub through any past run, share a link]

## Two Lines of Code

```python
from agentlens_sdk import auto_instrument
auto_instrument()
```

That's it. No config file. No schema changes. Works with OpenAI, Anthropic,
LangChain, CrewAI, AutoGen, Semantic Kernel, and any MCP-compatible agent.

## How It Works

[Brief technical overview:
 - SDK intercepts LLM calls via monkey-patching
 - Sends events over WebSocket to local FastAPI server
 - Server stores in SQLite, broadcasts to dashboard
 - Dashboard renders in real-time via D3/React]

## What I Learned

[3-4 honest observations from building this:
 1. Sentence-transformers + asyncio don't mix (fixed with run_in_executor)
 2. WebSocket disconnect handling is subtle
 3. The hallucination detector catches real bugs in real agents, not just demo ones]

## Get It

GitHub: [link]
pip install agentlens-server agentlens-sdk
npm install @agentlens/sdk

MIT licensed. Runs locally. No API keys.

---
```

---

## Awesome-List Submission Template

Use this as a PR description when submitting to awesome-lists:

```markdown
## Adding AgentLens

AgentLens is an open-source, real-time observability and debugging dashboard
for AI agents — the Chrome DevTools for the agentic AI era.

**What it does:**
- Real-time trace graph of every LLM call, tool invocation, and decision
- Automatic hallucination detection (cross-checks numbers between tool outputs and LLM responses)
- Per-step token cost tracking with optimization suggestions
- Session replay with shareable links
- Memory inspector with version history and influence mapping
- Native MCP server for zero-code observability

**Install:**
```bash
pip install agentlens-server agentlens-sdk
agentlens-server
```

**Links:**
- GitHub: [link]
- PyPI SDK: https://pypi.org/project/agentlens-sdk/
- PyPI Server: https://pypi.org/project/agentlens-server/
- npm: https://www.npmjs.com/package/@agentlens/sdk
- License: MIT
```

**Target awesome-lists:**
- [ ] awesome-llm
- [ ] awesome-agents
- [ ] awesome-mcp-servers (punkpeye/awesome-mcp-servers)
- [ ] awesome-devtools
- [ ] awesome-langchain (if applicable)

---

## Discord Server Setup

Create before launch so early users have a place to land.

**Server name:** AgentLens
**Channels to create:**
- `#announcements` (read-only)
- `#general`
- `#help` — for debugging questions
- `#show-and-tell` — users share what they built
- `#bugs` — issue reports before they make it to GitHub
- `#ideas` — feature requests

**Invite link:** Pin in GitHub README under a "Community" section once live.
