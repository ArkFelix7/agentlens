# AgentLens — Project Status & Roadmap

**Last Updated:** March 2026 (session 3)
**Stage:** Launch-ready. Package names resolved, all publish blockers cleared.

---

## 1. Purpose

AgentLens is an open-source, real-time observability and debugging dashboard for AI agents — the "Chrome DevTools" for the agentic AI era.

Every developer building AI agents faces the same blind spot: agents that call tools, make multi-step decisions, and consume tokens — all inside a black box. There is no inspect element. No network tab. No breakpoints. Debugging means print statements and guessing.

AgentLens eliminates that blind spot. It gives developers:

- A real-time visual graph of every LLM call, tool invocation, decision, and memory operation
- Per-step token cost tracking with optimization suggestions
- Automatic hallucination detection (cross-checks agent outputs against tool data)
- VCR-style session replay with shareable links
- A full memory inspector for agents with persistent memory
- Native MCP server integration — zero-code observability for MCP-compatible agents

The product is MIT-licensed and free for local use. The long-term revenue model is a hosted cloud tier for teams (shared dashboards, alerts, retention, auth).

**Target audience, in order:**
1. Solo developers building agents with OpenAI, Anthropic, LangChain, CrewAI, AutoGen
2. Early-stage AI startups shipping agent-based products
3. Enterprise AI teams needing audit trails and cost governance

**Technical moat:** framework-agnostic from day one, open-source community compounds faster than any single-vendor tool, and the MCP integration positions AgentLens as the default debugger across the entire MCP ecosystem.

---

## 2. Architecture Summary

Single monorepo with 5 packages:

```
agentlens/
├── server/          # Python FastAPI — REST + WebSocket backend
├── dashboard/       # React + Vite + Tailwind — visual debugger UI
├── sdk-python/      # Python SDK — @trace decorator, auto_instrument()
├── sdk-typescript/  # TypeScript SDK — trace() wrapper
├── mcp-server/      # MCP server — zero-code observability via MCP protocol
├── examples/        # 4 demo agents (multi-step, OpenAI, Anthropic, LangChain)
└── tests/           # Integration test runner (38 tests + benchmark mode)
```

**Runtime:** Server on port 8766 (REST at `/api/v1/*`, WebSocket at `/ws`). Dashboard on port 5173. SQLite auto-created on first run. All IDs are ULIDs. All timestamps are ISO 8601 UTC.

---

## 3. What We Have Built

### 3.1 Infrastructure

| Item | Status | Notes |
|------|--------|-------|
| Monorepo structure | DONE | Matches PRD Section 2 exactly |
| Makefile (`make dev`, `make install`, `make demo`) | DONE | Starts server + dashboard together |
| docker-compose.yml | DONE | Server + dashboard as containers |
| server/Dockerfile | DONE | Production-ready Python container |
| dashboard/Dockerfile | DONE | Nginx-based static serve |
| .github/workflows/ci.yml | DONE | Server (py 3.10/3.11/3.12), dashboard, sdk-python, sdk-ts, integration jobs |
| CONTRIBUTING.md | DONE | Dev setup, test instructions, PR guidelines |
| LICENSE (MIT) | DONE | |
| README.md | DONE | Quick start, badges, features, framework table |

### 3.2 Server (FastAPI Backend)

| Component | Status | Notes |
|-----------|--------|-------|
| `main.py` — FastAPI app, CORS, lifespan, routers | DONE | Single port 8766, CORS allows `*` for dev |
| `config.py` — pydantic-settings | DONE | |
| `database.py` — async SQLAlchemy engine, auto-create tables | DONE | SQLite + PostgreSQL-compatible |
| **Models** | | |
| `session.py` — Session ORM | DONE | |
| `trace_event.py` — TraceEvent ORM (self-ref parent/children) | DONE | Bug fixed: `remote_side` on parent relationship |
| `memory_entry.py` — MemoryEntry ORM | DONE | |
| `hallucination_alert.py` — HallucinationAlert ORM | DONE | |
| **Schemas (Pydantic)** | | |
| trace.py, session.py, cost.py, hallucination.py, memory.py | DONE | All use `model_dump(mode="json")` for WS broadcast |
| **Services** | | |
| `trace_service.py` | DONE | Dedup check prevents IntegrityError on replay |
| `session_service.py` | DONE | |
| `cost_service.py` | DONE | Cost suggestions engine included |
| `hallucination_service.py` | DONE | Number regex + entity extraction |
| `memory_service.py` | DONE | Create, update, delete, version history |
| `replay_service.py` | DONE | Ordered event assembly for replay |
| **Utils** | | |
| `pricing.py` — MODEL_PRICING table | DONE | OpenAI, Anthropic, Google, Meta, Mistral; fuzzy model name match |
| `text_similarity.py` | DONE | Keyword overlap only (sentence-transformers disabled — blocks asyncio event loop) |
| **WebSocket** | | |
| `manager.py` — connection manager, heartbeat, broadcast | DONE | 30s ping heartbeat, graceful disconnect |
| `handlers.py` — SDK + dashboard message routing | DONE | Disconnect breaks loop (no spin), hello-role handshake |
| **Routers** | | |
| traces.py, sessions.py, costs.py, hallucinations.py, memory.py | DONE | All REST endpoints per PRD Section 4.3 |
| Memory PATCH/DELETE (`/api/v1/memory/entry/{id}`) | DONE | Added beyond PRD: edit + delete memory entries |
| **Alembic** | | |
| alembic.ini, env.py, 001_initial.py migration | DONE | Not required for local (auto-create), but present |
| **Tests** | | |
| test_trace_ingestion.py, test_sessions.py, test_cost_calculation.py, test_hallucination.py | DONE | |
| test_websocket.py | DONE | Uses httpx-ws; requires server running |

### 3.3 Python SDK

| Component | Status | Notes |
|-----------|--------|-------|
| `__init__.py` — public API: `init`, `trace`, `auto_instrument`, `get_tracer` | DONE | |
| `client.py` — async WebSocket + HTTP fallback transport | DONE | Non-blocking, buffers events, silent failure |
| `trace.py` — `@trace` decorator, `TracerContext`, span API | DONE | Auto session management, atexit hook |
| `config.py`, `types.py` | DONE | |
| `interceptors/openai_interceptor.py` | DONE | Monkey-patches AsyncCompletions.create |
| `interceptors/anthropic_interceptor.py` | DONE | Monkey-patches AsyncAnthropic.messages.create |
| `interceptors/langchain_interceptor.py` | DONE | BaseCallbackHandler subclass |
| `interceptors/generic_interceptor.py` | DONE | For any callable |
| `interceptors/crewai_interceptor.py` | DONE | Added beyond original PRD scope |
| `interceptors/autogen_interceptor.py` | DONE | Added beyond original PRD scope |
| Sensitive data redaction (api_key, token, password, secret) | DONE | |
| SDK never raises exceptions (all try/except) | DONE | |
| Tests: test_trace.py, test_client.py, test_interceptors.py | DONE | |
| pyproject.toml — hatchling build, optional extras (openai, anthropic, langchain, all) | DONE | |

### 3.4 TypeScript SDK

| Component | Status | Notes |
|-----------|--------|-------|
| types.ts, config.ts, client.ts, trace.ts, index.ts | DONE | |
| interceptors/openai.ts, anthropic.ts, generic.ts | DONE | |
| package.json — `@agentlens/sdk`, peer deps for openai + anthropic | DONE | |
| tsconfig.json | DONE | |

### 3.5 Dashboard (React Frontend)

| Component | Status | Notes |
|-----------|--------|-------|
| **Build config** | | |
| package.json, vite.config.ts, tailwind.config.js, postcss.config.js, index.html | DONE | |
| index.css — full CSS variable palette (--bg-*, --text-*, --accent-*, --event-*) | DONE | |
| Fonts: JetBrains Mono + IBM Plex Sans via Google Fonts | DONE | |
| **Types** | | |
| types/index.ts — all TS interfaces (TraceEvent, Session, Cost, Hallucination, Memory, Replay) | DONE | |
| types/trace.ts | DONE | |
| **Stores (Zustand)** | | |
| traceStore, sessionStore, settingsStore, websocketStore | DONE | |
| **Hooks** | | |
| useWebSocket.ts | DONE | Auto-reconnect every 5s, hello-role handshake |
| useTraceGraph.ts | DONE | D3 graph data transformation |
| useCostCalculator.ts | DONE | Includes projected monthly cost calculation |
| useReplay.ts | DONE | VCR playback with speed control |
| **Contexts** | | |
| WebSocketContext.tsx | DONE | |
| **Shared components** | | |
| Badge, LoadingSpinner, EmptyState, JsonViewer, CodeBlock, Tooltip, Modal, Toast | DONE | |
| **Layout** | | |
| Sidebar.tsx, TopBar.tsx, MainLayout.tsx | DONE | |
| **Traces components** | | |
| TraceGraph.tsx — D3 force-directed graph, node types, zoom/pan | DONE | |
| TraceTimeline.tsx — horizontal timeline alternate view | DONE | |
| TraceDetail.tsx — right panel, JsonViewer for input/output | DONE | |
| EventNode.tsx, EventBadge.tsx | DONE | |
| **Cost components** | | |
| CostOverview.tsx — 4 summary cards + projected monthly cost | DONE | |
| CostBreakdown.tsx, CostTimeline.tsx, CostHotspots.tsx | DONE | |
| **Hallucination components** | | |
| HallucinationPanel.tsx, DiffViewer.tsx, SeverityBadge.tsx | DONE | |
| **Memory components** | | |
| MemoryTimeline.tsx, MemoryDetail.tsx, MemorySearch.tsx, MemoryInfluence.tsx | DONE | |
| Memory edit/delete UI | DONE | Added beyond PRD: PATCH/DELETE via API |
| **Replay components** | | |
| ReplayPlayer.tsx — VCR controls (play/pause/step/speed) | DONE | |
| ReplayTimeline.tsx — scrubber bar | DONE | |
| ReplayState.tsx — cumulative state at current step | DONE | |
| Shareable replay links (`?session=<id>` URL param + copy button) | DONE | Added beyond PRD |
| **Pages** | | |
| TracesPage, CostsPage, HallucinationsPage, MemoryPage, ReplayPage, SettingsPage | DONE | |
| **App** | | |
| App.tsx — React Router, all routes, theme class toggle | DONE | |
| main.tsx | DONE | |
| Light/dark theme switching | DONE | useEffect toggles `.dark`/`.light` on `<html>` |

### 3.6 MCP Server

| Component | Status | Notes |
|-----------|--------|-------|
| server.py — MCP server with stdio transport | DONE | |
| tools.py — agentlens_start_session, agentlens_report_trace, agentlens_report_memory | DONE | |
| pyproject.toml | DONE | |

### 3.7 Examples

| File | Status | Notes |
|------|--------|-------|
| demo_multi_step.py | DONE | 8+ steps, intentional number-transposition hallucination, memory ops, works without API keys |
| demo_openai_agent.py | DONE | Minimal @trace usage, falls back to mock if no key |
| demo_anthropic_agent.py | DONE | auto_instrument() usage |
| demo_langchain_agent.py | DONE | LangChain CallbackHandler |

### 3.8 Integration Tests

| Item | Status | Notes |
|------|--------|-------|
| tests/integration/test_runner.py | DONE | 38 tests covering all endpoints, WS protocol, hallucination, memory, replay |
| Benchmark mode (`--bench`) | DONE | p50/p95/p99 latency, throughput (events/s), concurrent sessions |

**Performance baseline (local SQLite, macOS):**
- Single event POST: p50=1.6ms, p95=2.1ms
- Batch throughput: ~2500 events/s
- GET /traces (500 events): p50=6.2ms, p95=14.9ms

### 3.9 Critical Bugs Fixed

These bugs were found during integration testing and fixed:

1. **WebSocket spin loop** — `except Exception: continue` inside the receive loop caught `WebSocketDisconnect`, creating an infinite tight loop at 100% CPU. Fixed by splitting into two try/except blocks with `break` on disconnect.

2. **sentence-transformers blocks asyncio** — `model.encode()` (PyTorch) blocks the GIL and makes the server unresponsive. Fixed by disabling sentence-transformers; `text_similarity.py` now uses keyword overlap only. This means hallucination detection uses regex number matching + keyword overlap, not semantic embeddings (acceptable for v1, fix planned).

3. **SQLAlchemy self-referential relationship** — Both parent and children used `ONETOMANY` direction. Fixed by adding `remote_side="TraceEvent.id"` on the parent side.

4. **Python 3.10 compatibility** — System has Python 3.10; `T | None` union syntax is 3.10+. Changed `pyproject.toml` to `requires-python = ">=3.10"` and used `Optional[T]` throughout.

5. **Datetime not JSON-serializable in WS broadcasts** — `model_dump()` returns `datetime` objects; `json.dumps()` raises `TypeError` silently → endpoint returned 500. Fixed by using `model_dump(mode="json")` everywhere a Pydantic model feeds a WS broadcast.

6. **Duplicate event ID IntegrityError** — `db.add(event)` with a duplicate PK raised `IntegrityError` at commit, returning 500 instead of silently skipping. Fixed with a `get()` check before `add()`.

---

## 4. What Is NOT Done Yet

### 4.1 Missing Files (minor, low effort)

| Missing | Priority | Notes |
|---------|----------|-------|
| `dashboard/public/agentlens-og.png` | Medium | Open Graph image for social sharing — needed for Twitter/LinkedIn posts |
| `sdk-python/README.md` | Medium | Package-level README for PyPI listing |
| `sdk-typescript/README.md` | Medium | Package-level README for npm listing |
| `mcp-server/README.md` | Medium | Setup instructions for MCP clients |
| `examples/README.md` | Low | Overview of each demo and how to run |

### 4.2 Missing CLI Entrypoint (blocks PyPI usability)

The server's `pyproject.toml` has no `[project.scripts]` section. Running `pip install agentlens-server` installs the package but provides no `agentlens-server` command. The README currently says `uvicorn src.main:app --port 8766` which is not the clean UX promised in the PRD (`agentlens-server` one-command start).

```toml
# Needs to be added to server/pyproject.toml:
[project.scripts]
agentlens-server = "src.main:run"
```

### 4.3 Missing SDK TypeScript publish setup

`@agentlens/sdk` `package.json` has no `files` field, no `publishConfig`, and no `prepublishOnly` build script. Running `npm publish` would publish without built artifacts.

### 4.4 Functional Gaps

| Gap | Priority | Notes |
|-----|----------|-------|
| Semantic Kernel interceptor | Medium | Mentioned in Blueprint Phase 4 (Weeks 7-8); LangChain, CrewAI, AutoGen done but Semantic Kernel not yet |
| "What If" replay branching | Low | PRD 3.4.5 mentions ability to replay from any point with different inputs; standard VCR is done but branching is not |
| Sentence-transformers (async) | Medium | Hallucination detection currently uses regex + keyword overlap only. Running `model.encode()` in a `ThreadPoolExecutor` via `asyncio.run_in_executor` would restore semantic similarity without blocking the event loop |
| MCP server registry listing | Medium | Not submitted to awesome-mcp or any MCP directory yet |

### 4.5 Not Started: Launch Preparation

| Item | Priority | Notes |
|------|----------|-------|
| Demo GIF / 60-second video | CRITICAL | Missing from README (placeholder exists). Without this, the GitHub README has no visual hook. |
| PyPI publication (`pip install agentlens`) | CRITICAL | Package is structured correctly; needs `pip install build && python -m build` + `twine upload` |
| npm publication (`@agentlens/sdk`) | High | Needs `npm run build` + `npm publish` with proper publishConfig |
| Hacker News Show HN post | High | "Show HN: AgentLens — Open-Source Chrome DevTools for AI Agents" |
| Twitter/X launch thread | High | Demo video + before/after framing |
| Reddit posts | High | r/MachineLearning, r/LocalLLaMA, r/artificial |
| Awesome-list submissions | High | awesome-llm, awesome-agents, awesome-mcp, awesome-devtools |
| Launch blog post | High | "I Built Chrome DevTools for AI Agents" |
| Discord community | Medium | Set up before launch so early users have a place to land |

### 4.6 Not Started: Cloud/Monetization (Phase 5)

| Item | Notes |
|------|-------|
| Cloud deployment (Railway/Render) | Dockerfiles exist; needs deployment config |
| PostgreSQL backend (Supabase) | Server is SQLite-only; PostgreSQL migration needs `DATABASE_URL` env var support |
| GitHub OAuth | No auth system exists yet |
| Team workspaces | No multi-tenancy |
| Stripe payment integration | No payment system |
| Pricing page | Not built |

---

## 5. What We Wish to Achieve

### Near-term (1-3 months)
- **1,000+ GitHub stars** within 2 weeks of launch
- **100+ developers** actively using the local version
- **PyPI + npm packages** publicly installable (`pip install agentlens`, `npm install @agentlens/sdk`)
- **Listed in 3+ awesome-lists** (awesome-llm, awesome-agents, awesome-mcp)
- **Show HN front page** — this single event can drive 5-10K GitHub profile views and 500+ stars in a day
- **AgentLens Cloud beta** — hosted version with GitHub OAuth and shared dashboards

### Medium-term (3-6 months)
- **5,000+ GitHub stars**
- **50+ paying Pro/Team customers** at $15-40/seat/month
- **Framework integrations** for Semantic Kernel (last major one missing)
- **MCP registry listing** — every MCP developer discovers AgentLens when exploring the ecosystem
- **Featured in one major AI newsletter** (TLDR AI, The Batch, Import AI)
- **Conference talk invitation** based on AgentLens work (NYC AI meetups are the pipeline)

### Long-term (6-18 months)
- **AgentLens Score** — a Lighthouse-style reliability grade (0-100) for any agent, embeddable as a README badge
- **GitHub Actions integration** — runs AgentLens checks on every PR modifying agent code, comments on hallucination rate changes
- **Academic paper** — publish findings from anonymized AgentLens trace data on agent failure patterns (doubles as masters thesis material)
- **Seed round** — $1-2M from developer-tool-focused VCs (Heavybit, Boldstart, Redpoint) with 10K+ stars + paying customers as evidence
- **Datadog for agents** — the default observability platform that every serious agent deployment uses

---

## 6. What We Should Do Next — Prioritized Action List

### Priority 1: Unblock PyPI/npm Publishing (2-4 hours)

These are blocking the entire launch. Nothing else matters until `pip install agentlens` works cleanly.

**Task 1.1 — Add CLI entrypoint to server**
```toml
# server/pyproject.toml — add under [project]:
[project.scripts]
agentlens-server = "src.main:run"
```
Add `def run(): uvicorn.run("src.main:app", host="0.0.0.0", port=8766)` to `server/src/main.py`.

**Task 1.2 — Fix TypeScript SDK for npm publish**
```json
// sdk-typescript/package.json — add:
"files": ["dist", "README.md"],
"prepublishOnly": "npm run build"
```

**Task 1.3 — Build and publish to PyPI**
```bash
cd sdk-python && python -m build && twine upload dist/*
cd server && python -m build && twine upload dist/*
```

**Task 1.4 — Build and publish to npm**
```bash
cd sdk-typescript && npm run build && npm publish
```

---

### Priority 2: Demo GIF (3-5 hours)

The single most impactful item. Every GitHub README needs a GIF above the fold. Without it, conversion from viewer to star to installer is dead.

**Script for the 60-second demo recording:**
1. Open a blank terminal — no AgentLens running
2. Run `python examples/demo_multi_step.py` — show it completing with no visibility
3. Start AgentLens: `make dev`
4. Re-run the demo agent
5. Switch to browser at `localhost:5173` — show the trace graph populating in real time
6. Click a node — show the full input/output detail panel
7. Click Costs tab — show the per-step cost breakdown
8. Click Hallucinations tab — show the detected number transposition (the planted bug)
9. Click Replay — scrub through the session step by step
10. Generate shareable link — paste it in a new tab to demonstrate

**Tools:** OBS (free, open-source) for recording. Convert to GIF with `ffmpeg` or Gifski. Target: 800px wide, < 5MB.

Place the GIF at `dashboard/public/demo.gif` and embed in README directly below the tagline.

---

### Priority 3: Write Launch Content (1 day)

**Task 3.1 — Blog post: "I Built Chrome DevTools for AI Agents"**
Structure:
- The problem: debugging agents is like web dev in 2001 before Firebug
- What AgentLens shows (with screenshots from the 5 tabs)
- The hallucination I caught in my own demo agent
- Two lines of code to integrate
- What's next (Cloud, Semantic Kernel, GitHub Actions)

Post to: personal blog → cross-post to Dev.to, Hashnode, Medium.

**Task 3.2 — Show HN post text**
```
Show HN: AgentLens — Open-Source Chrome DevTools for AI Agents

I built AgentLens because I was debugging a multi-step agent by reading JSON logs
and got frustrated. It's a real-time visual debugger that shows every LLM call,
tool invocation, and memory operation your agent makes — with automatic hallucination
detection and session replay.

Two lines to instrument any agent:
  from agentlens import auto_instrument
  auto_instrument()

Works with OpenAI, Anthropic, LangChain, CrewAI, AutoGen, and any MCP-compatible agent.
Free and open-source (MIT). Self-hosted, SQLite, no API keys needed.

GitHub: [link]
Demo video: [link]
```

**Task 3.3 — Twitter/X thread outline**
- Tweet 1: Demo video (the before/after reveal is the hook)
- Tweet 2: The hallucination detection feature — "it caught a number transposition I didn't even notice"
- Tweet 3: "Two lines of code" code block
- Tweet 4: Framework support table
- Tweet 5: "Open-source, MIT, runs on localhost" → GitHub link

---

### Priority 4: Missing READMEs and Social Assets (2-3 hours)

- `dashboard/public/agentlens-og.png` — 1200×630px open graph card (text: "AgentLens — Chrome DevTools for AI Agents" + a screenshot)
- `sdk-python/README.md` — install, quick start, decorator API, interceptor list
- `sdk-typescript/README.md` — install, quick start, trace() wrapper, interceptors
- `mcp-server/README.md` — MCP client config (Claude Desktop, Cursor), tool list
- `examples/README.md` — table of demos and what each showcases

---

### Priority 5: Hallucination Detection Improvement (4-6 hours)

Current hallucination detection uses number regex extraction only. Restore semantic similarity without blocking the event loop:

```python
# server/src/utils/text_similarity.py
import asyncio
from functools import partial

_model = None

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

async def semantic_similarity(text1: str, text2: str) -> float:
    loop = asyncio.get_event_loop()
    model = await loop.run_in_executor(None, _get_model)
    encode = partial(model.encode, [text1, text2], convert_to_tensor=False)
    embeddings = await loop.run_in_executor(None, encode)
    # cosine similarity
    a, b = embeddings[0], embeddings[1]
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

This runs the PyTorch encode in a thread pool, returns control to the event loop, and does not block.

---

### Priority 6: Semantic Kernel Interceptor (3-4 hours)

LangChain, CrewAI, and AutoGen are done. Semantic Kernel is the last major framework gap.

```python
# sdk-python/src/agentlens/interceptors/semantic_kernel_interceptor.py
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext

class AgentLensKernelFilter:
    async def on_function_invocation(
        self,
        context: FunctionInvocationContext,
        next: Callable
    ) -> None:
        # Start event, call next(), capture result + tokens
```

Also expose it in `auto_instrument()` alongside the existing interceptors.

---

### Priority 7: MCP Server Registry Submission (1 hour)

Submit the MCP server to:
- `github.com/punkpeye/awesome-mcp-servers` — open a PR adding AgentLens
- `mcpservers.org` or equivalent directories
- The Anthropic Discord `#mcp-servers` channel

This is purely distribution — costs nothing and reaches every MCP developer actively exploring the ecosystem.

---

### Priority 8: Launch (1 day — time-sensitive)

Execute in this exact order:

1. Monday: Soft launch — tweet the demo video, tag 5-10 AI developer accounts
2. Tuesday 9am EST: Submit Show HN
3. Tuesday: Post to r/MachineLearning, r/LocalLLaMA, r/artificial
4. Wednesday: LinkedIn post for professional ML audience
5. Thursday: Dev.to + Hashnode cross-post of launch blog
6. Friday: Respond to every GitHub issue opened in the first week
7. Weekend: DM 10 developers who showed interest asking for feedback

---

### Priority 9: Cloud Infrastructure (after launch, when usage is confirmed)

Only begin after the local version has real users. The usage signals will inform which cloud features to prioritize.

**Phase 5A: Basic Cloud**
- Deploy server Dockerfile to Railway (already written, costs $5/mo)
- Swap SQLite for Supabase PostgreSQL (free tier, 500MB) — `DATABASE_URL` env var support already partially present in config
- Add GitHub OAuth (FastAPI + authlib, 1 day of work)
- Add user sessions table and middleware

**Phase 5B: Team Features**
- Team workspace model (org → members → shared sessions)
- RBAC (admin, member, viewer)
- 30-day trace retention policy
- Slack/Discord alerts for hallucinations and errors

**Phase 5C: Monetization**
- Stripe integration for Pro ($15/seat) and Team ($40/seat)
- Pricing page on the dashboard's Settings route
- Upgrade prompts at natural friction points (storage limit hit, team share attempted)

---

## 7. Quick Reference: How to Run Everything

```bash
# Install all dependencies
make install

# Start server + dashboard (development)
make dev
# Server: http://localhost:8766
# Dashboard: http://localhost:5173

# Run showcase demo agent
make demo

# Run integration tests (requires server running)
python3 tests/integration/test_runner.py

# Run integration tests with benchmark
python3 tests/integration/test_runner.py --bench

# Run server unit tests
cd server && pytest tests/ -v

# Run SDK tests
cd sdk-python && pytest tests/ -v
```

---

## 8. Key File Reference

| What you're looking for | File |
|------------------------|------|
| Server entry point | `server/src/main.py` |
| WebSocket message routing | `server/src/websocket/handlers.py` |
| WebSocket connection manager | `server/src/websocket/manager.py` |
| Cost calculation + pricing | `server/src/utils/pricing.py`, `server/src/services/cost_service.py` |
| Hallucination detection | `server/src/services/hallucination_service.py` |
| Text similarity (keyword-only) | `server/src/utils/text_similarity.py` |
| Memory CRUD | `server/src/routers/memory.py`, `server/src/services/memory_service.py` |
| Python SDK public API | `sdk-python/src/agentlens/__init__.py` |
| OpenAI interceptor | `sdk-python/src/agentlens/interceptors/openai_interceptor.py` |
| Dashboard state | `dashboard/src/stores/` |
| D3 trace graph | `dashboard/src/components/traces/TraceGraph.tsx` |
| Replay page (with shareable links) | `dashboard/src/pages/ReplayPage.tsx` |
| Memory detail (with edit/delete) | `dashboard/src/components/memory/MemoryDetail.tsx` |
| Projected monthly cost | `dashboard/src/hooks/useCostCalculator.ts`, `dashboard/src/components/costs/CostOverview.tsx` |
| CI pipeline | `.github/workflows/ci.yml` |
| Integration test runner | `tests/integration/test_runner.py` |
| MCP server tools | `mcp-server/src/agentlens_mcp/tools.py` |

---

## 9. Known Technical Debt

| Issue | Severity | Fix |
|-------|----------|-----|
| Hallucination uses keyword overlap only, not semantic embeddings | Medium | `run_in_executor` wrapping for sentence-transformers (see Priority 5 above) |
| No `agentlens-server` CLI command | High | Add `[project.scripts]` to server/pyproject.toml |
| TypeScript SDK missing `files` + `prepublishOnly` in package.json | High | Blocks `npm publish` |
| `sdk-typescript/package-lock.json` is untracked | Low | Either commit it or add to .gitignore |
| Alembic migrations not used (tables created via SQLAlchemy directly) | Low | Fine for local/v1; required before cloud migration |
| No rate limiting on trace ingestion endpoint | Low | DoS risk in cloud mode; not a concern for local |
| `sentence-transformers` is in `requirements.txt` / `pyproject.toml` but not used | Low | Either remove the dependency or implement async wrapper (Priority 5) |

---

*This document is a living reference. Update it as tasks are completed and new issues are discovered.*
