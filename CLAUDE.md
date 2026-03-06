# AgentLens — Project Instructions for Claude Code

## What This Project Is
AgentLens is an open-source, real-time observability and debugging dashboard for AI agents. It is a monorepo with 5 packages: a React dashboard, a Python FastAPI backend, a Python SDK, a TypeScript SDK, and an MCP server. Plus example demo agents.

## Master Specification
The complete PRD is in `AgentLens_PRD.md` in this repository root. It contains every file path, every database schema, every API endpoint, every component spec, every type definition, and the exact build order. **Read the entire PRD before writing any code.** Follow it precisely. Do not skip any file or component described in the PRD.

## Build Rules

### Order of Operations
You MUST build in this exact order (Section 15 of the PRD):
1. Repository structure + config files (Makefile, docker-compose, .gitignore, LICENSE, README)
2. Server (FastAPI backend) — fully functional with all endpoints and WebSocket
3. Python SDK — with @trace decorator and all interceptors
4. TypeScript SDK
5. Dashboard (React frontend) — all 6 pages, all components
6. MCP Server
7. Example agents (3 demo scripts)
8. Integration test: run server + dashboard + demo agent together, fix any issues

### Tech Stack (Do Not Deviate)
- Dashboard: React 18 + Vite + Tailwind CSS + Zustand + D3.js + Recharts + Framer Motion + TypeScript
- Server: Python FastAPI + SQLAlchemy (async) + aiosqlite + WebSockets + sentence-transformers
- SDK Python: websockets + aiohttp + python-ulid
- SDK TypeScript: ws + ulid
- MCP Server: mcp sdk (python)

### Code Quality Standards
- TypeScript: strict mode, no `any` except JSON data fields
- Python: type hints on all function signatures, Pydantic models for all API boundaries
- Every file starts with a docstring/comment explaining its purpose
- All user-facing errors are clear and actionable
- The SDK must NEVER raise exceptions to user code — always try/except with silent failure
- The server must handle CORS allowing localhost:5173

### Design System (Dashboard)
- Dark mode first. Use the exact CSS variables from PRD Section 3.2
- Fonts: JetBrains Mono (display/mono) + IBM Plex Sans (body) via Google Fonts
- Colors: Near-black backgrounds (#0a0a0f), indigo accents (#6366f1), event-type color coding
- Animations: Framer Motion for page transitions and node appearances
- No generic AI aesthetics. This should feel like a professional Bloomberg-terminal-grade developer tool.

### Critical Implementation Details
- Server runs on single port 8766 with REST at /api/v1/* and WebSocket at /ws
- Database: SQLite with auto-creation on first run, no manual migration needed
- All IDs are ULIDs (sortable by time)
- All timestamps are ISO 8601 UTC
- JSON fields in DB stored as TEXT, serialized/deserialized in service layer
- The demo_multi_step.py must work WITHOUT any API keys using simulated/mock responses
- The demo must intentionally include one hallucination (number transposition) for the hallucination detector to find

### File Structure
Follow the exact monorepo structure from PRD Section 2. Every file listed there must exist.

### After Building Each Package
- After server: verify it starts with `uvicorn src.main:app --port 8766`
- After SDK: verify `from agentlens import init, trace, auto_instrument` works
- After dashboard: verify it starts with `npm run dev` and shows the empty state
- After examples: verify `python demo_multi_step.py` runs and sends traces to the server
- Final: run server + dashboard + demo simultaneously and verify traces appear in the dashboard

## What NOT To Do
- Do not use localStorage or sessionStorage in the dashboard
- Do not create separate CSS/JS files for the dashboard — everything in single components
- Do not use UUID — use ULID everywhere
- Do not skip the hallucination detection engine — it's a core differentiator
- Do not skip the Memory Inspector — it's a core differentiator
- Do not make the SDK blocking or exception-throwing
- Do not skip error boundaries and empty states in the dashboard
