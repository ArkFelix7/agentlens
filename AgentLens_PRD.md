# AgentLens — Product Requirements Document (PRD)

## For: Claude Code (Autonomous Build)

**Version:** 1.0
**Target:** Production-grade, fully functional, shippable project
**Instruction to Claude Code:** Read this entire document before writing any code. Build every component described. Do not skip any section. Follow the exact file structure, schemas, and specifications. Build in the exact order specified in Section 15 (Build Order).

---

## 1. Project Overview

AgentLens is an open-source, real-time observability and debugging dashboard for AI agents. It consists of five packages in a monorepo:

1. **`@agentlens/dashboard`** — React frontend (the visual debugger UI)
2. **`@agentlens/server`** — Python FastAPI backend (trace ingestion, storage, analysis)
3. **`@agentlens/sdk-python`** — Python SDK (decorator/wrapper for agent instrumentation)
4. **`@agentlens/sdk-typescript`** — TypeScript SDK (same functionality for TS agents)
5. **`@agentlens/mcp-server`** — MCP server (receives traces from MCP-native agents)

Additionally there is a **`/examples`** directory with 3 fully working demo agents.

---

## 2. Monorepo Structure

```
agentlens/
├── README.md
├── LICENSE                          # MIT License
├── .gitignore
├── docker-compose.yml               # Optional: run everything in containers
├── Makefile                         # Convenience commands
│
├── dashboard/                       # React Frontend
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   ├── public/
│   │   ├── favicon.svg
│   │   └── agentlens-og.png         # Open graph image for social sharing
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css                # Tailwind base + custom styles + fonts
│       ├── types/
│       │   ├── index.ts             # All TypeScript interfaces/types
│       │   └── trace.ts             # Trace-specific types
│       ├── stores/
│       │   ├── traceStore.ts        # Zustand store for traces
│       │   ├── sessionStore.ts      # Zustand store for sessions
│       │   ├── settingsStore.ts     # Zustand store for user preferences
│       │   └── websocketStore.ts    # Zustand store for WS connection state
│       ├── hooks/
│       │   ├── useWebSocket.ts      # WebSocket connection hook
│       │   ├── useTraceGraph.ts     # D3 graph data transformation hook
│       │   ├── useCostCalculator.ts # Cost aggregation hook
│       │   └── useReplay.ts         # Session replay playback hook
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.tsx       # Left sidebar navigation
│       │   │   ├── TopBar.tsx        # Top bar with session selector + connection status
│       │   │   └── MainLayout.tsx    # Overall layout wrapper
│       │   ├── traces/
│       │   │   ├── TraceGraph.tsx     # D3 force-directed graph of trace events
│       │   │   ├── TraceTimeline.tsx  # Horizontal timeline view (alternate to graph)
│       │   │   ├── TraceDetail.tsx    # Right panel: detail view of selected event
│       │   │   ├── EventNode.tsx      # Individual node in the graph
│       │   │   └── EventBadge.tsx     # Status badge (success/warning/error)
│       │   ├── costs/
│       │   │   ├── CostOverview.tsx    # Summary cards (total cost, avg per session, etc.)
│       │   │   ├── CostBreakdown.tsx   # Bar chart: cost per model
│       │   │   ├── CostTimeline.tsx    # Line chart: cost over time
│       │   │   └── CostHotspots.tsx    # Table: most expensive steps
│       │   ├── hallucination/
│       │   │   ├── HallucinationPanel.tsx  # List of detected mismatches
│       │   │   ├── DiffViewer.tsx          # Side-by-side diff of tool output vs agent output
│       │   │   └── SeverityBadge.tsx       # Critical/Warning/Info badge
│       │   ├── memory/
│       │   │   ├── MemoryTimeline.tsx   # Vertical timeline of memory events
│       │   │   ├── MemoryDetail.tsx     # Expanded view of a single memory
│       │   │   ├── MemorySearch.tsx     # Search/filter memories
│       │   │   └── MemoryInfluence.tsx  # Shows which memories influenced a decision
│       │   ├── replay/
│       │   │   ├── ReplayPlayer.tsx     # VCR controls (play, pause, step forward/back)
│       │   │   ├── ReplayTimeline.tsx   # Scrubber bar showing all steps
│       │   │   └── ReplayState.tsx      # State snapshot at current replay step
│       │   └── shared/
│       │       ├── JsonViewer.tsx       # Collapsible JSON tree viewer
│       │       ├── CodeBlock.tsx        # Syntax-highlighted code display
│       │       ├── EmptyState.tsx       # "No data yet" placeholder with instructions
│       │       ├── LoadingSpinner.tsx
│       │       ├── Badge.tsx            # Generic badge component
│       │       ├── Tooltip.tsx
│       │       ├── Modal.tsx
│       │       └── Toast.tsx            # Notification toasts
│       └── pages/
│           ├── TracesPage.tsx
│           ├── CostsPage.tsx
│           ├── HallucinationsPage.tsx
│           ├── MemoryPage.tsx
│           ├── ReplayPage.tsx
│           └── SettingsPage.tsx
│
├── server/                          # Python FastAPI Backend
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── alembic.ini                  # Database migration config
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial.py
│   └── src/
│       ├── __init__.py
│       ├── main.py                  # FastAPI app entry point
│       ├── config.py                # Settings via pydantic-settings
│       ├── database.py              # SQLAlchemy async engine + session
│       ├── models/
│       │   ├── __init__.py
│       │   ├── trace_event.py       # TraceEvent ORM model
│       │   ├── session.py           # Session ORM model
│       │   └── memory_entry.py      # MemoryEntry ORM model
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── trace.py             # Pydantic schemas for trace API
│       │   ├── session.py           # Pydantic schemas for session API
│       │   ├── memory.py            # Pydantic schemas for memory API
│       │   ├── cost.py              # Pydantic schemas for cost API
│       │   └── hallucination.py     # Pydantic schemas for hallucination API
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── traces.py            # REST endpoints for traces
│       │   ├── sessions.py          # REST endpoints for sessions
│       │   ├── memory.py            # REST endpoints for memory
│       │   ├── costs.py             # REST endpoints for cost analysis
│       │   └── hallucinations.py    # REST endpoints for hallucination checks
│       ├── services/
│       │   ├── __init__.py
│       │   ├── trace_service.py     # Business logic for trace processing
│       │   ├── cost_service.py      # Cost calculation engine
│       │   ├── hallucination_service.py  # Hallucination detection engine
│       │   ├── memory_service.py    # Memory indexing and retrieval
│       │   └── replay_service.py    # Session replay data assembly
│       ├── websocket/
│       │   ├── __init__.py
│       │   ├── manager.py           # WebSocket connection manager
│       │   └── handlers.py          # WebSocket message handlers
│       └── utils/
│           ├── __init__.py
│           ├── pricing.py           # Model pricing table
│           └── text_similarity.py   # Semantic similarity for hallucination detection
│
├── sdk-python/                      # Python SDK
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   └── agentlens/
│   │       ├── __init__.py          # Public API exports
│   │       ├── client.py            # WebSocket/HTTP client to AgentLens server
│   │       ├── trace.py             # @trace decorator and TracerContext
│   │       ├── interceptors/
│       │   ├── __init__.py
│       │   ├── openai_interceptor.py    # Monkey-patches openai.ChatCompletion
│       │   ├── anthropic_interceptor.py # Monkey-patches anthropic.Messages
│       │   ├── langchain_interceptor.py # LangChain CallbackHandler
│       │   └── generic_interceptor.py   # For any callable
│       │       ├── types.py             # SDK type definitions
│       │       └── config.py            # SDK configuration
│   └── tests/
│       ├── test_trace.py
│       ├── test_client.py
│       └── test_interceptors.py
│
├── sdk-typescript/                  # TypeScript SDK
│   ├── package.json
│   ├── tsconfig.json
│   ├── README.md
│   └── src/
│       ├── index.ts                 # Public API exports
│       ├── client.ts                # WebSocket/HTTP client
│       ├── trace.ts                 # trace() wrapper function
│       ├── interceptors/
│       │   ├── openai.ts
│       │   ├── anthropic.ts
│       │   └── generic.ts
│       ├── types.ts
│       └── config.ts
│
├── mcp-server/                      # MCP Server
│   ├── pyproject.toml
│   ├── README.md
│   └── src/
│       └── agentlens_mcp/
│           ├── __init__.py
│           ├── server.py            # MCP server implementation
│           └── tools.py             # Tool definitions (report_trace, report_memory)
│
└── examples/                        # Demo Agents
    ├── README.md
    ├── demo_openai_agent.py         # Simple OpenAI agent with AgentLens
    ├── demo_anthropic_agent.py      # Simple Anthropic agent with AgentLens
    ├── demo_langchain_agent.py      # LangChain agent with AgentLens
    └── demo_multi_step.py           # Complex multi-step agent (best for showcasing)
```

---

## 3. Dashboard Specifications

### 3.1 Technology Stack

| Dependency | Version | Purpose |
|-----------|---------|---------|
| react | ^18.3.0 | UI framework |
| react-dom | ^18.3.0 | DOM rendering |
| react-router-dom | ^6.26.0 | Client-side routing |
| zustand | ^4.5.0 | State management |
| d3 | ^7.9.0 | Trace graph visualization |
| recharts | ^2.12.0 | Cost charts (line, bar, pie) |
| @tanstack/react-query | ^5.56.0 | Server state + REST API calls |
| lucide-react | ^0.441.0 | Icons |
| tailwindcss | ^3.4.0 | Styling |
| vite | ^5.4.0 | Build tool + dev server |
| typescript | ^5.5.0 | Type safety |
| date-fns | ^3.6.0 | Date formatting |
| react-diff-viewer-continued | ^3.4.0 | Hallucination diff view |
| framer-motion | ^11.5.0 | Animations |
| react-hotkeys-hook | ^4.5.0 | Keyboard shortcuts |
| react-json-view-lite | ^1.5.0 | JSON tree viewer |
| clsx | ^2.1.0 | Conditional classnames |

### 3.2 Design System

**Aesthetic Direction:** Dark-mode-first, industrial-precision dashboard inspired by professional audio mixing consoles and Bloomberg terminals. Dense but readable. Feels like a power tool, not a toy.

**Color Palette (CSS Variables in index.css):**

```css
:root {
  /* Backgrounds */
  --bg-primary: #0a0a0f;           /* Near-black with slight blue */
  --bg-secondary: #12121a;         /* Card/panel backgrounds */
  --bg-tertiary: #1a1a26;          /* Hover states, subtle elevation */
  --bg-elevated: #222233;          /* Modals, dropdowns */

  /* Borders */
  --border-subtle: #2a2a3a;
  --border-default: #3a3a4a;
  --border-focus: #6366f1;

  /* Text */
  --text-primary: #e4e4ed;
  --text-secondary: #9494a8;
  --text-tertiary: #6b6b80;
  --text-inverse: #0a0a0f;

  /* Accent Colors */
  --accent-indigo: #6366f1;         /* Primary actions, links */
  --accent-indigo-hover: #818cf8;
  --accent-emerald: #10b981;        /* Success, positive states */
  --accent-amber: #f59e0b;          /* Warnings */
  --accent-red: #ef4444;            /* Errors, critical hallucinations */
  --accent-cyan: #06b6d4;           /* Info, memory-related */
  --accent-purple: #a855f7;         /* LLM call nodes */

  /* Trace Event Type Colors */
  --event-llm: #a855f7;            /* Purple for LLM calls */
  --event-tool: #06b6d4;           /* Cyan for tool calls */
  --event-decision: #f59e0b;       /* Amber for decisions */
  --event-memory: #6366f1;         /* Indigo for memory ops */
  --event-error: #ef4444;          /* Red for errors */
  --event-user: #10b981;           /* Green for user input */

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.4);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.5);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.6);

  /* Radii */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
}
```

**Typography:**

```css
/* Import via Google Fonts in index.html */
/* Display/Headings: JetBrains Mono — a monospace font that signals "developer tool" */
/* Body: IBM Plex Sans — clean, technical, high readability */

--font-display: 'JetBrains Mono', monospace;
--font-body: 'IBM Plex Sans', sans-serif;
--font-mono: 'JetBrains Mono', monospace;    /* Code blocks, JSON, data */
```

Font sizes: Use Tailwind scale — `text-xs` (12px) for metadata, `text-sm` (14px) for body, `text-base` (16px) for emphasis, `text-lg` (18px) for section headers, `text-xl`/`text-2xl` for page titles.

**Animations (via Framer Motion):**

- Page transitions: Fade-in with slight upward slide (duration: 200ms)
- Panel open: Slide from right, 250ms ease-out
- Trace nodes appearing: Scale from 0 → 1 with stagger (50ms per node)
- Status badges: Gentle pulse animation for live/active states
- Toast notifications: Slide in from top-right, auto-dismiss after 4s

### 3.3 Layout Specification

```
┌──────────────────────────────────────────────────────────┐
│  TopBar (h-14)                                           │
│  [AgentLens logo] [Session: dropdown] [● Connected]      │
├──────┬───────────────────────────────────────────────────┤
│      │                                                   │
│  S   │  Main Content Area                                │
│  i   │                                                   │
│  d   │  (Switches based on active tab/route)             │
│  e   │                                                   │
│  b   │  For Traces: splits into                          │
│  a   │  ┌──────────────────────┬──────────────────┐      │
│  r   │  │  Trace Graph/Timeline│  Event Detail    │      │
│      │  │  (70% width)         │  Panel (30%)     │      │
│  w   │  │                      │                  │      │
│  -   │  └──────────────────────┴──────────────────┘      │
│  5   │                                                   │
│  6   │                                                   │
│      │                                                   │
└──────┴───────────────────────────────────────────────────┘
```

**Sidebar Navigation Items:**

| Icon | Label | Route | Keyboard Shortcut |
|------|-------|-------|-------------------|
| Activity | Traces | `/` | `1` |
| DollarSign | Costs | `/costs` | `2` |
| AlertTriangle | Hallucinations | `/hallucinations` | `3` |
| Brain | Memory | `/memory` | `4` |
| Play | Replay | `/replay` | `5` |
| Settings | Settings | `/settings` | `,` |

### 3.4 Page-by-Page Specifications

#### 3.4.1 Traces Page (`/`)

This is the primary view and the first thing users see.

**Left Panel (70%): Trace Graph**

- D3.js force-directed graph
- Each trace event is a node; edges connect parent → child events
- Node appearance varies by event type:
  - **LLM Call:** Circle with purple fill, shows model name (e.g., "gpt-4o") inside
  - **Tool Call:** Rounded rectangle with cyan border, shows tool name inside
  - **Decision:** Diamond shape with amber fill
  - **Memory Read/Write:** Hexagon with indigo fill
  - **Error:** Red circle with exclamation icon
  - **User Input:** Green circle with user icon
- Node size proportional to token cost (minimum 32px, maximum 64px diameter)
- Edges are animated (dashed line moving in flow direction) for the currently-active step
- Clicking a node selects it (adds glow ring) and opens detail in right panel
- Zoom and pan with mouse wheel + drag (d3-zoom)
- **Toggle button** in top-left of graph panel switches between Graph View and Timeline View

**Timeline View (alternate):**
- Horizontal timeline with events as cards arranged left-to-right
- Vertical line between each card showing data flow
- More readable for linear agent workflows
- Same click-to-select behavior

**Right Panel (30%): Event Detail**

When no event selected, show: "Select an event from the trace graph to see details"

When event selected, show:

```
┌─────────────────────────────┐
│  Event: tool_call            │  ← EventBadge with type + color
│  Tool: web_search            │
│  Duration: 342ms             │
│  Tokens: 0 in / 0 out       │
│  Cost: $0.000                │
│  Status: ✓ Success           │
├─────────────────────────────┤
│  INPUT                       │
│  ┌─────────────────────────┐ │
│  │ { "query": "latest..." }│ │  ← JsonViewer, collapsible
│  └─────────────────────────┘ │
├─────────────────────────────┤
│  OUTPUT                      │
│  ┌─────────────────────────┐ │
│  │ { "results": [...]  }   │ │  ← JsonViewer, collapsible
│  └─────────────────────────┘ │
├─────────────────────────────┤
│  METADATA                    │
│  Model: -                    │
│  Timestamp: 2026-03-06...    │
│  Parent: event_abc123        │
│  Session: sess_xyz789        │
└─────────────────────────────┘
```

**Top Controls Bar (above graph):**
- Session selector dropdown (shows recent sessions, sorted by time)
- Filter by event type (toggle buttons: LLM | Tool | Decision | Memory | Error)
- Search box (searches event names, tool names, model names)
- "Clear" button to clear current session data
- Live indicator: green dot + "Live" when WebSocket connected, red dot + "Disconnected" when not

#### 3.4.2 Costs Page (`/costs`)

**Top Row: Summary Cards (4 cards, equal width)**

| Card | Content | Icon |
|------|---------|------|
| Total Cost (Session) | "$1.23" | DollarSign in green circle |
| Total Tokens | "45,230 tokens" | Hash icon |
| Avg Cost/Step | "$0.08" | TrendingDown icon |
| Most Expensive Model | "gpt-4o ($0.89)" | Zap icon |

**Row 2: Cost Over Time (Recharts LineChart)**
- X-axis: timestamp of each event
- Y-axis: cumulative cost in USD
- Line color: var(--accent-indigo)
- Tooltip shows: event name, model, token count, cost
- Height: 300px

**Row 3: Two columns**

Left: **Cost by Model (Recharts BarChart)**
- Horizontal bars, one per model used
- Bar color varies by model (assign colors in a lookup table)
- Shows dollar amount at end of each bar

Right: **Cost Hotspots (Table)**
- Columns: Step Name | Model | Tokens | Cost | % of Total
- Sorted by cost descending
- Top 3 rows highlighted with subtle amber background
- "Optimization Tip" column: If a step uses gpt-4o but has <100 output tokens, suggest "Consider gpt-4o-mini"

#### 3.4.3 Hallucinations Page (`/hallucinations`)

**Top: Summary Bar**
- "X potential hallucinations detected in this session"
- Breakdown: Y Critical | Z Warning | W Info

**Main: List of Detected Mismatches**

Each mismatch is a card:

```
┌─────────────────────────────────────────────────────────┐
│ ⚠ WARNING  Step 5: summarize_results       12:34:05 PM  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  TOOL OUTPUT (Source of Truth)     AGENT OUTPUT          │
│  ┌──────────────────────────┐     ┌──────────────────┐  │
│  │ Revenue: $2.3M           │     │ Revenue: $3.2M   │  │  ← Red highlight on diff
│  │ Growth: 12% YoY          │     │ Growth: 12% YoY  │  │  ← No highlight (match)
│  │ Customers: 1,450         │     │ Customers: 1,450 │  │
│  └──────────────────────────┘     └──────────────────┘  │
│                                                         │
│  Mismatch: Number transposition detected                │
│  Similarity Score: 0.87                                 │
└─────────────────────────────────────────────────────────┘
```

- Use `react-diff-viewer-continued` for the side-by-side diff
- Each card is collapsible (click to expand/collapse)
- Filter by severity: Critical | Warning | Info | All

#### 3.4.4 Memory Page (`/memory`)

**Left Column (40%): Memory Timeline**
- Vertical timeline with newest at top
- Each entry shows: timestamp, memory key/topic, action (CREATED / UPDATED / ACCESSED / DELETED)
- Color-coded by action type
- Click to select and show detail in right panel
- Search bar at top filters by memory content

**Right Column (60%): Memory Detail**

When selected:
```
┌───────────────────────────────────────┐
│  Memory: "user_preference_language"    │
│  Created: 2026-03-06 12:30:00         │
│  Last Accessed: 2026-03-06 14:15:00   │
│  Access Count: 7                       │
├───────────────────────────────────────┤
│  CONTENT                               │
│  "The user prefers Python and has      │
│   expressed interest in async..."      │
├───────────────────────────────────────┤
│  INFLUENCE MAP                         │
│  This memory influenced 3 decisions:   │
│  • Step 12: chose Python code example  │
│  • Step 18: suggested asyncio          │
│  • Step 25: recommended FastAPI        │
├───────────────────────────────────────┤
│  VERSION HISTORY                       │
│  v1 (12:30): "User likes Python"       │
│  v2 (13:45): "User prefers Python      │
│              and async patterns"       │
│  v3 (14:15): Current version           │
└───────────────────────────────────────┘
```

#### 3.4.5 Replay Page (`/replay`)

**Top: Session Selector**
- Dropdown to choose which session to replay
- Shows session timestamp, event count, total cost

**Center: Trace Graph (same as Traces page, but frozen/non-live)**
- Events appear one at a time as replay progresses
- Current event is highlighted with animated glow
- Past events are shown at full opacity
- Future events are hidden or grayed out

**Bottom: Replay Controls**

```
[|◄] [◄] [▶/❚❚] [►] [►|]    Step 5 / 23    Speed: [1x ▼]    ━━━━━●━━━━━━━━━
 ↑    ↑     ↑     ↑    ↑                                        ↑
Start Back Play  Fwd  End                                     Scrubber
```

- Play: Auto-advances one step per second (adjustable speed: 0.5x, 1x, 2x, 5x)
- Step Forward/Back: Manual single-step
- Scrubber: Drag to jump to any step
- Keyboard: Space = play/pause, Left/Right arrows = step, Home/End = jump

**Right Panel: State at Current Step**
- Shows the full event detail (same as Traces right panel)
- Additionally shows cumulative state: total cost so far, tokens so far, errors so far

#### 3.4.6 Settings Page (`/settings`)

- **Server URL:** Text input, default `ws://localhost:8765` (WebSocket) and `http://localhost:8766` (REST)
- **Theme:** Toggle Dark/Light (Dark is default; build both themes)
- **Auto-connect:** Toggle (default: on) — auto-reconnect WebSocket on disconnect
- **Trace Retention:** Dropdown — Keep last 10 / 50 / 100 / All sessions
- **Cost Display Currency:** USD only for v1
- **Keyboard Shortcuts:** Reference table showing all shortcuts
- **About:** Version number, GitHub link, MIT license notice

### 3.5 WebSocket Protocol (Dashboard ↔ Server)

The dashboard connects to `ws://localhost:8765/ws` on mount.

**Messages FROM Server → Dashboard:**

```typescript
// New trace event in real-time
{
  type: "trace_event",
  data: TraceEvent
}

// Session started
{
  type: "session_start",
  data: { session_id: string, agent_name: string, started_at: string }
}

// Session ended
{
  type: "session_end",
  data: { session_id: string, ended_at: string, summary: SessionSummary }
}

// Hallucination detected
{
  type: "hallucination_detected",
  data: HallucinationAlert
}

// Memory updated
{
  type: "memory_update",
  data: MemoryEntry
}
```

**Messages FROM Dashboard → Server:**

```typescript
// Request session list
{ type: "get_sessions" }

// Request specific session's events
{ type: "get_session_events", session_id: string }

// Clear session data
{ type: "clear_session", session_id: string }
```

---

## 4. Server Specifications

### 4.1 Technology Stack

| Dependency | Version | Purpose |
|-----------|---------|---------|
| fastapi | >=0.115.0 | Web framework |
| uvicorn[standard] | >=0.30.0 | ASGI server |
| websockets | >=12.0 | WebSocket support |
| sqlalchemy[asyncio] | >=2.0.35 | ORM |
| aiosqlite | >=0.20.0 | Async SQLite driver |
| alembic | >=1.13.0 | Migrations |
| pydantic | >=2.9.0 | Data validation |
| pydantic-settings | >=2.5.0 | Configuration |
| sentence-transformers | >=3.1.0 | Hallucination detection (semantic similarity) |
| numpy | >=1.26.0 | Vector operations |
| python-ulid | >=2.7.0 | ULID generation for IDs |

### 4.2 Database Schema (SQLite for local, PostgreSQL-compatible)

**Table: sessions**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | ULID |
| agent_name | TEXT | NOT NULL, DEFAULT 'unnamed' | Name of the agent |
| started_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Session start time |
| ended_at | TIMESTAMP | NULLABLE | Session end time |
| total_events | INTEGER | NOT NULL, DEFAULT 0 | Count of events |
| total_cost_usd | REAL | NOT NULL, DEFAULT 0.0 | Cumulative cost |
| total_tokens_input | INTEGER | NOT NULL, DEFAULT 0 | |
| total_tokens_output | INTEGER | NOT NULL, DEFAULT 0 | |
| status | TEXT | NOT NULL, DEFAULT 'active' | 'active' or 'completed' or 'error' |
| metadata | TEXT | NULLABLE | JSON string for extra data |

**Table: trace_events**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | ULID |
| session_id | TEXT | FOREIGN KEY → sessions.id, NOT NULL | |
| parent_event_id | TEXT | FOREIGN KEY → trace_events.id, NULLABLE | For building event tree |
| event_type | TEXT | NOT NULL | 'llm_call', 'tool_call', 'decision', 'memory_read', 'memory_write', 'user_input', 'error' |
| event_name | TEXT | NOT NULL | Human-readable name (e.g., "gpt-4o completion", "web_search") |
| timestamp | TIMESTAMP | NOT NULL | When the event started |
| duration_ms | REAL | NOT NULL, DEFAULT 0 | Execution duration |
| input_data | TEXT | NULLABLE | JSON string of input |
| output_data | TEXT | NULLABLE | JSON string of output |
| model | TEXT | NULLABLE | Model name if LLM call |
| tokens_input | INTEGER | NOT NULL, DEFAULT 0 | |
| tokens_output | INTEGER | NOT NULL, DEFAULT 0 | |
| cost_usd | REAL | NOT NULL, DEFAULT 0.0 | |
| status | TEXT | NOT NULL, DEFAULT 'success' | 'success', 'error', 'pending' |
| error_message | TEXT | NULLABLE | Error details if status='error' |
| metadata | TEXT | NULLABLE | JSON string for extra data |

**Indexes on trace_events:** session_id, event_type, timestamp

**Table: hallucination_alerts**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | ULID |
| session_id | TEXT | FOREIGN KEY → sessions.id | |
| trace_event_id | TEXT | FOREIGN KEY → trace_events.id | The event that produced the hallucination |
| source_event_id | TEXT | FOREIGN KEY → trace_events.id | The tool event that provided ground truth |
| severity | TEXT | NOT NULL | 'critical', 'warning', 'info' |
| description | TEXT | NOT NULL | Human-readable explanation |
| expected_value | TEXT | NOT NULL | What the tool returned |
| actual_value | TEXT | NOT NULL | What the agent reported |
| similarity_score | REAL | NOT NULL | 0.0 to 1.0 |
| detected_at | TIMESTAMP | NOT NULL | |

**Table: memory_entries**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | ULID |
| session_id | TEXT | FOREIGN KEY → sessions.id | Session where memory was created/updated |
| agent_id | TEXT | NOT NULL, DEFAULT 'default' | For multi-agent setups |
| memory_key | TEXT | NOT NULL | Identifier/topic for this memory |
| content | TEXT | NOT NULL | The memory content |
| action | TEXT | NOT NULL | 'created', 'updated', 'accessed', 'deleted' |
| version | INTEGER | NOT NULL, DEFAULT 1 | Incrementing version |
| timestamp | TIMESTAMP | NOT NULL | |
| influenced_events | TEXT | NULLABLE | JSON array of event IDs this memory influenced |
| metadata | TEXT | NULLABLE | JSON string |

### 4.3 REST API Endpoints

**Base URL:** `http://localhost:8766/api/v1`

#### Sessions

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| GET | `/sessions` | List all sessions | Query: `?limit=50&offset=0&status=active` | `{ sessions: Session[], total: number }` |
| GET | `/sessions/:id` | Get session detail | — | `Session` with full summary |
| DELETE | `/sessions/:id` | Delete a session and its events | — | `{ deleted: true }` |

#### Traces

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| POST | `/traces` | Ingest a batch of trace events | `{ session_id: str, events: TraceEvent[] }` | `{ ingested: number }` |
| GET | `/traces/:session_id` | Get all events for a session | Query: `?event_type=llm_call` | `{ events: TraceEvent[] }` |
| GET | `/traces/:session_id/tree` | Get events as nested tree | — | `TraceEventTree` (events with children array) |

#### Costs

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/costs/:session_id` | Cost breakdown for session | `{ total_usd, by_model: {}, by_step: [], timeline: [] }` |
| GET | `/costs/:session_id/hotspots` | Most expensive steps | `{ hotspots: CostHotspot[] }` |
| GET | `/costs/:session_id/suggestions` | Cost optimization suggestions | `{ suggestions: CostSuggestion[] }` |

#### Hallucinations

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/hallucinations/:session_id` | All hallucination alerts | `{ alerts: HallucinationAlert[], summary: { critical, warning, info } }` |
| POST | `/hallucinations/check` | Manually trigger check for a session | `{ session_id }` → `{ alerts: HallucinationAlert[] }` |

#### Memory

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/memory/:session_id` | All memory entries for session | `{ entries: MemoryEntry[] }` |
| GET | `/memory/:session_id/:memory_key` | Specific memory with version history | `{ current: MemoryEntry, history: MemoryEntry[] }` |

### 4.4 WebSocket Server

**Endpoint:** `ws://localhost:8765/ws`

The server manages bidirectional communication:

1. **SDK → Server:** Receives trace events via WebSocket or REST POST
2. **Server → Dashboard:** Broadcasts trace events to all connected dashboard clients
3. **Dashboard → Server:** Receives commands (get sessions, get events, etc.)

**Connection Manager Requirements:**
- Track connected clients (dashboard instances)
- Broadcast new events to all connected dashboards in real-time
- Handle reconnection gracefully (client sends `get_session_events` on reconnect)
- Heartbeat ping every 30s to detect stale connections

### 4.5 Cost Calculation Engine

**Model Pricing Table (as of March 2026 — store in `utils/pricing.py`):**

```python
MODEL_PRICING = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},         # per 1M tokens
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "o3-mini": {"input": 1.10, "output": 4.40},

    # Anthropic
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},

    # Google
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},

    # Meta (via API providers)
    "llama-3.1-70b": {"input": 0.35, "output": 0.40},
    "llama-3.1-8b": {"input": 0.05, "output": 0.08},

    # Mistral
    "mistral-large": {"input": 2.00, "output": 6.00},
    "mistral-small": {"input": 0.20, "output": 0.60},
}

def calculate_cost(model: str, tokens_input: int, tokens_output: int) -> float:
    """Returns cost in USD. Returns 0.0 for unknown models."""
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        # Try fuzzy match (e.g., "gpt-4o-2024-08-06" should match "gpt-4o")
        for key in MODEL_PRICING:
            if key in model or model.startswith(key):
                pricing = MODEL_PRICING[key]
                break
    if not pricing:
        return 0.0
    return (tokens_input * pricing["input"] / 1_000_000) + (tokens_output * pricing["output"] / 1_000_000)
```

**Cost Suggestion Engine:**

```python
def generate_suggestions(events: list[TraceEvent]) -> list[CostSuggestion]:
    suggestions = []
    for event in events:
        if event.event_type != "llm_call":
            continue
        # Suggestion 1: Expensive model for simple tasks
        if event.model in ["gpt-4o", "gpt-4", "claude-opus-4-6"]:
            if event.tokens_output < 200:
                suggestions.append(CostSuggestion(
                    event_id=event.id,
                    current_model=event.model,
                    suggested_model=get_cheaper_alternative(event.model),
                    current_cost=event.cost_usd,
                    estimated_savings=estimate_savings(event),
                    reason=f"This step produced only {event.tokens_output} output tokens. "
                           f"A smaller model could handle this at ~{estimate_savings_pct(event)}% less cost."
                ))
        # Suggestion 2: Repeated identical calls
        # (detect by comparing input_data hashes)
        # Suggest caching
    return suggestions
```

### 4.6 Hallucination Detection Engine

The hallucination detector runs automatically whenever a session contains both tool_call events and llm_call events that follow them.

**Algorithm:**

1. For each `llm_call` event that follows one or more `tool_call` events in the trace:
   a. Extract all numeric values, proper nouns, dates, and key facts from the tool output
   b. Extract the same entity types from the LLM output
   c. Compare:
      - **Numbers:** Exact match required. "$2.3M" in tool but "$3.2M" in LLM = CRITICAL
      - **Dates:** Exact match required. "March 5" vs "March 6" = CRITICAL
      - **Names/Entities:** Fuzzy match via similarity. Score < 0.85 = WARNING
      - **General text:** Semantic similarity via sentence-transformers. Score < 0.75 = INFO
2. For the initial version, use a simpler heuristic approach:
   - Extract all numbers (regex) from tool outputs and LLM outputs
   - Check if LLM output numbers are a subset of tool output numbers
   - Flag any numbers in LLM output not found in tool output as potential hallucinations
   - Use `sentence-transformers/all-MiniLM-L6-v2` for text similarity when needed

**Implementation Note:** Load the sentence-transformer model lazily (on first hallucination check request, not on server startup) to avoid slow startup times. Cache the model in memory.

---

## 5. Python SDK Specifications

### 5.1 Public API Surface

```python
# The user-facing API must be this simple:

from agentlens import init, trace, get_tracer

# Option 1: Decorator (simplest)
init(server_url="ws://localhost:8765")  # Optional — uses default if omitted

@trace(name="my_agent")
async def my_agent(query: str) -> str:
    # ... agent code ...
    return result

# Option 2: Context manager
async def my_agent(query: str) -> str:
    with get_tracer().span("my_agent") as span:
        span.set_attribute("query", query)
        result = await do_something()
        span.set_output(result)
        return result

# Option 3: Auto-instrument (monkey-patches OpenAI/Anthropic clients)
from agentlens import auto_instrument
auto_instrument()  # From this point, all OpenAI/Anthropic calls are traced
```

### 5.2 SDK Internals

**`client.py` — Transport Layer:**

```python
class AgentLensClient:
    def __init__(self, server_url="ws://localhost:8765", http_url="http://localhost:8766"):
        self.ws_url = server_url
        self.http_url = http_url
        self._ws = None
        self._buffer: list[dict] = []
        self._flush_interval = 1.0  # seconds
        self._max_buffer_size = 20
        self._connected = False
        self._session_id: str | None = None

    async def connect(self):
        """Non-blocking connection attempt. Fails silently."""
        try:
            self._ws = await websockets.connect(self.ws_url)
            self._connected = True
            asyncio.create_task(self._flush_loop())
        except Exception:
            self._connected = False

    async def send_event(self, event: dict):
        """Buffer event for batch sending. Never blocks or raises."""
        self._buffer.append(event)
        if len(self._buffer) >= self._max_buffer_size:
            await self._flush()

    async def _flush(self):
        if not self._buffer:
            return
        if not self._connected:
            # Fallback to HTTP POST
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        f"{self.http_url}/api/v1/traces",
                        json={"session_id": self._session_id, "events": self._buffer}
                    )
            except Exception:
                pass  # Silent failure — never crash the user's agent
            self._buffer.clear()
            return
        try:
            await self._ws.send(json.dumps({
                "type": "trace_events",
                "session_id": self._session_id,
                "events": self._buffer
            }))
            self._buffer.clear()
        except Exception:
            self._connected = False

    async def _flush_loop(self):
        while True:
            await asyncio.sleep(self._flush_interval)
            await self._flush()
```

**Critical SDK Design Rules:**

1. **Never raise exceptions** — All SDK operations are wrapped in try/except. The SDK must never crash the user's agent.
2. **Never block** — All operations are async and non-blocking. If the server is down, events are silently dropped.
3. **Minimal overhead** — SDK adds <5ms per traced event
4. **Auto-session management** — The SDK creates a new session on first traced event and ends it when the process exits (via atexit hook)
5. **Sensitive data redaction** — By default, redact any field named "api_key", "token", "password", "secret", "authorization" in input/output data

### 5.3 Framework Interceptors

**OpenAI Interceptor (`interceptors/openai_interceptor.py`):**

```python
def patch_openai():
    """Monkey-patches the OpenAI client to auto-trace all completions."""
    import openai
    original_create = openai.resources.chat.completions.Completions.create
    original_acreate = openai.resources.chat.completions.AsyncCompletions.create

    async def traced_acreate(self, *args, **kwargs):
        tracer = get_current_tracer()
        event = tracer.start_event(
            event_type="llm_call",
            event_name=f"openai:{kwargs.get('model', 'unknown')}",
            input_data={"messages": kwargs.get("messages", []), "model": kwargs.get("model")},
        )
        try:
            result = await original_acreate(self, *args, **kwargs)
            event.set_output({
                "content": result.choices[0].message.content,
                "finish_reason": result.choices[0].finish_reason,
            })
            event.set_tokens(
                input_tokens=result.usage.prompt_tokens,
                output_tokens=result.usage.completion_tokens,
            )
            event.set_model(result.model)
            return result
        except Exception as e:
            event.set_error(str(e))
            raise
        finally:
            event.end()

    # Apply patches
    openai.resources.chat.completions.AsyncCompletions.create = traced_acreate
    # Similar for sync version
```

**Anthropic Interceptor (`interceptors/anthropic_interceptor.py`):**
Same pattern — monkey-patch `anthropic.AsyncAnthropic.messages.create` to capture input messages, output content, token usage, and model name.

**LangChain Interceptor (`interceptors/langchain_interceptor.py`):**
Implement a `BaseCallbackHandler` subclass:

```python
from langchain.callbacks.base import BaseCallbackHandler

class AgentLensCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        # Start LLM call event
    def on_llm_end(self, response, **kwargs):
        # End LLM call event with token usage
    def on_tool_start(self, serialized, input_str, **kwargs):
        # Start tool call event
    def on_tool_end(self, output, **kwargs):
        # End tool call event
    def on_chain_start(self, serialized, inputs, **kwargs):
        # Start decision event
    def on_chain_end(self, outputs, **kwargs):
        # End decision event
    def on_llm_error(self, error, **kwargs):
        # Record error
    def on_tool_error(self, error, **kwargs):
        # Record error
```

---

## 6. TypeScript SDK Specifications

### 6.1 Public API Surface

```typescript
import { init, trace, autoInstrument } from '@agentlens/sdk';

// Initialize
init({ serverUrl: 'ws://localhost:8765' });

// Option 1: Wrapper function
const myAgent = trace(async (query: string) => {
  // ... agent code ...
  return result;
}, { name: 'my_agent' });

// Option 2: Auto-instrument
autoInstrument(); // Patches OpenAI and Anthropic Node SDKs
```

### 6.2 Package Configuration

```json
{
  "name": "@agentlens/sdk",
  "version": "0.1.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch"
  },
  "dependencies": {
    "ws": "^8.18.0",
    "ulid": "^2.3.0"
  },
  "peerDependencies": {
    "openai": ">=4.0.0",
    "@anthropic-ai/sdk": ">=0.25.0"
  },
  "peerDependenciesMeta": {
    "openai": { "optional": true },
    "@anthropic-ai/sdk": { "optional": true }
  }
}
```

---

## 7. MCP Server Specifications

### 7.1 Overview

The MCP server allows any MCP-compatible agent (Claude Desktop, Cursor, etc.) to send traces to AgentLens without using the SDK. It registers as an MCP server and exposes tools that agents can call to report their activity.

### 7.2 Tools Exposed

**Tool 1: `agentlens_report_trace`**

```json
{
  "name": "agentlens_report_trace",
  "description": "Report an agent execution trace event to AgentLens for debugging and observability. Call this after completing a tool call, LLM request, or decision to enable real-time debugging.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "session_id": { "type": "string", "description": "Unique session identifier. Generate one at the start and reuse." },
      "event_type": { "type": "string", "enum": ["llm_call", "tool_call", "decision", "memory_read", "memory_write", "error"], "description": "Type of event" },
      "event_name": { "type": "string", "description": "Human-readable name for this event" },
      "input_data": { "type": "string", "description": "JSON string of input to this step" },
      "output_data": { "type": "string", "description": "JSON string of output from this step" },
      "duration_ms": { "type": "number", "description": "Duration in milliseconds" },
      "model": { "type": "string", "description": "Model name if LLM call (e.g., 'gpt-4o')" },
      "tokens_input": { "type": "integer", "description": "Input token count" },
      "tokens_output": { "type": "integer", "description": "Output token count" },
      "status": { "type": "string", "enum": ["success", "error"], "default": "success" },
      "error_message": { "type": "string", "description": "Error details if status is error" }
    },
    "required": ["session_id", "event_type", "event_name"]
  }
}
```

**Tool 2: `agentlens_report_memory`**

```json
{
  "name": "agentlens_report_memory",
  "description": "Report a memory state change to AgentLens. Call when agent creates, updates, reads, or deletes a memory.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "session_id": { "type": "string" },
      "memory_key": { "type": "string", "description": "Identifier for this memory" },
      "content": { "type": "string", "description": "Memory content" },
      "action": { "type": "string", "enum": ["created", "updated", "accessed", "deleted"] }
    },
    "required": ["session_id", "memory_key", "content", "action"]
  }
}
```

**Tool 3: `agentlens_start_session`**

```json
{
  "name": "agentlens_start_session",
  "description": "Start a new AgentLens debugging session. Call once at the beginning of a task.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "agent_name": { "type": "string", "description": "Name of the agent", "default": "mcp-agent" }
    }
  }
}
```

### 7.3 MCP Server Implementation

```python
# mcp-server/src/agentlens_mcp/server.py

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx
import json
from ulid import ULID

AGENTLENS_HTTP_URL = "http://localhost:8766/api/v1"
server = Server("agentlens")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="agentlens_start_session", description="...", inputSchema={...}),
        Tool(name="agentlens_report_trace", description="...", inputSchema={...}),
        Tool(name="agentlens_report_memory", description="...", inputSchema={...}),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    async with httpx.AsyncClient() as client:
        if name == "agentlens_start_session":
            session_id = str(ULID())
            # POST to server to create session
            await client.post(f"{AGENTLENS_HTTP_URL}/sessions", json={
                "id": session_id,
                "agent_name": arguments.get("agent_name", "mcp-agent"),
            })
            return [TextContent(type="text", text=f"Session started: {session_id}")]

        elif name == "agentlens_report_trace":
            event = {
                "id": str(ULID()),
                "session_id": arguments["session_id"],
                "event_type": arguments["event_type"],
                "event_name": arguments["event_name"],
                "input_data": arguments.get("input_data"),
                "output_data": arguments.get("output_data"),
                "duration_ms": arguments.get("duration_ms", 0),
                "model": arguments.get("model"),
                "tokens_input": arguments.get("tokens_input", 0),
                "tokens_output": arguments.get("tokens_output", 0),
                "status": arguments.get("status", "success"),
                "error_message": arguments.get("error_message"),
            }
            await client.post(f"{AGENTLENS_HTTP_URL}/traces", json={
                "session_id": arguments["session_id"],
                "events": [event],
            })
            return [TextContent(type="text", text="Trace event recorded")]

        elif name == "agentlens_report_memory":
            await client.post(f"{AGENTLENS_HTTP_URL}/memory", json=arguments)
            return [TextContent(type="text", text="Memory state updated")]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 8. Example Agents

### 8.1 Demo: Multi-Step Research Agent (Primary Demo)

**File: `examples/demo_multi_step.py`**

This is the showcase demo that demonstrates all AgentLens features. It's a simple research agent that:

1. Takes a user query
2. Searches the web (simulated tool call)
3. Reads the results (simulated tool call)
4. Summarizes findings (LLM call — use OpenAI or Anthropic based on env var)
5. Stores a memory about the user's interest
6. Generates a final report (LLM call)

**Requirements for the demo:**
- Must work with `OPENAI_API_KEY` env var if present, otherwise fall back to simulated responses
- If using simulated responses, create realistic mock data that exercises all AgentLens features
- Intentionally introduce one hallucination (e.g., the LLM changes a number from the tool output) so the hallucination detector has something to find
- Include memory operations so the Memory tab has data
- Include at least 8 trace events to make the graph visually interesting
- Print clear instructions: "Open http://localhost:5173 to see the AgentLens dashboard"

### 8.2 Demo: Simple OpenAI Agent

**File: `examples/demo_openai_agent.py`**

Minimal agent: takes a question, calls OpenAI, returns answer. Shows the simplest possible AgentLens integration (just the `@trace` decorator). Must work with simulated responses if no API key.

### 8.3 Demo: Simple Anthropic Agent

**File: `examples/demo_anthropic_agent.py`**

Same as above but with Anthropic client. Shows `auto_instrument()` usage.

---

## 9. Configuration Files

### 9.1 Root Makefile

```makefile
.PHONY: install dev build test clean

install:
	cd dashboard && npm install
	cd server && pip install -e ".[dev]" --break-system-packages
	cd sdk-python && pip install -e ".[dev]" --break-system-packages
	cd sdk-typescript && npm install
	cd mcp-server && pip install -e . --break-system-packages

dev:
	@echo "Starting AgentLens development servers..."
	@echo "Dashboard: http://localhost:5173"
	@echo "Server API: http://localhost:8766"
	@echo "Server WS: ws://localhost:8765"
	cd server && uvicorn src.main:app --host 0.0.0.0 --port 8766 --reload &
	cd dashboard && npm run dev &
	wait

server:
	cd server && uvicorn src.main:app --host 0.0.0.0 --port 8766 --reload

dashboard:
	cd dashboard && npm run dev

demo:
	cd examples && python demo_multi_step.py

test:
	cd sdk-python && pytest
	cd server && pytest
	cd dashboard && npm test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name node_modules -exec rm -rf {} +
	find . -type d -name dist -exec rm -rf {} +
	rm -f server/agentlens.db
```

### 9.2 docker-compose.yml

```yaml
version: '3.8'

services:
  server:
    build:
      context: ./server
      dockerfile: Dockerfile
    ports:
      - "8766:8766"
      - "8765:8765"
    volumes:
      - ./server/data:/app/data
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/agentlens.db

  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      - VITE_WS_URL=ws://localhost:8765
      - VITE_API_URL=http://localhost:8766
    depends_on:
      - server
```

### 9.3 Dashboard: vite.config.ts

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8766',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8765',
        ws: true,
      },
    },
  },
});
```

### 9.4 Dashboard: tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        display: ['JetBrains Mono', 'monospace'],
        body: ['IBM Plex Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        surface: {
          primary: 'var(--bg-primary)',
          secondary: 'var(--bg-secondary)',
          tertiary: 'var(--bg-tertiary)',
          elevated: 'var(--bg-elevated)',
        },
        border: {
          subtle: 'var(--border-subtle)',
          DEFAULT: 'var(--border-default)',
          focus: 'var(--border-focus)',
        },
        content: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          tertiary: 'var(--text-tertiary)',
        },
        accent: {
          indigo: 'var(--accent-indigo)',
          emerald: 'var(--accent-emerald)',
          amber: 'var(--accent-amber)',
          red: 'var(--accent-red)',
          cyan: 'var(--accent-cyan)',
          purple: 'var(--accent-purple)',
        },
        event: {
          llm: 'var(--event-llm)',
          tool: 'var(--event-tool)',
          decision: 'var(--event-decision)',
          memory: 'var(--event-memory)',
          error: 'var(--event-error)',
          user: 'var(--event-user)',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'slide-in': 'slideIn 0.25s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateX(20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
```

### 9.5 Server: pyproject.toml

```toml
[project]
name = "agentlens-server"
version = "0.1.0"
description = "AgentLens observability server for AI agents"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "websockets>=12.0",
    "sqlalchemy[asyncio]>=2.0.35",
    "aiosqlite>=0.20.0",
    "alembic>=1.13.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "sentence-transformers>=3.1.0",
    "numpy>=1.26.0",
    "python-ulid>=2.7.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 9.6 SDK Python: pyproject.toml

```toml
[project]
name = "agentlens"
version = "0.1.0"
description = "Python SDK for AgentLens — observability for AI agents"
requires-python = ">=3.10"
dependencies = [
    "websockets>=12.0",
    "aiohttp>=3.10.0",
    "python-ulid>=2.7.0",
]

[project.optional-dependencies]
openai = ["openai>=1.0.0"]
anthropic = ["anthropic>=0.34.0"]
langchain = ["langchain-core>=0.3.0"]
all = ["openai>=1.0.0", "anthropic>=0.34.0", "langchain-core>=0.3.0"]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.23.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## 10. TypeScript Types (Complete)

**File: `dashboard/src/types/index.ts`**

```typescript
// ===== TRACE TYPES =====

export type EventType = 'llm_call' | 'tool_call' | 'decision' | 'memory_read' | 'memory_write' | 'user_input' | 'error';
export type EventStatus = 'success' | 'error' | 'pending';
export type Severity = 'critical' | 'warning' | 'info';
export type SessionStatus = 'active' | 'completed' | 'error';

export interface TraceEvent {
  id: string;
  session_id: string;
  parent_event_id: string | null;
  event_type: EventType;
  event_name: string;
  timestamp: string;              // ISO 8601
  duration_ms: number;
  input_data: Record<string, any> | null;
  output_data: Record<string, any> | null;
  model: string | null;
  tokens_input: number;
  tokens_output: number;
  cost_usd: number;
  status: EventStatus;
  error_message: string | null;
  metadata: Record<string, any> | null;
}

export interface TraceEventNode extends TraceEvent {
  children: TraceEventNode[];
}

// ===== SESSION TYPES =====

export interface Session {
  id: string;
  agent_name: string;
  started_at: string;
  ended_at: string | null;
  total_events: number;
  total_cost_usd: number;
  total_tokens_input: number;
  total_tokens_output: number;
  status: SessionStatus;
  metadata: Record<string, any> | null;
}

export interface SessionSummary {
  session_id: string;
  total_events: number;
  total_cost_usd: number;
  total_tokens: number;
  event_type_counts: Record<EventType, number>;
  models_used: string[];
  duration_ms: number;
  error_count: number;
}

// ===== COST TYPES =====

export interface CostBreakdown {
  total_usd: number;
  by_model: Record<string, { cost: number; tokens_input: number; tokens_output: number; call_count: number }>;
  by_step: Array<{ event_id: string; event_name: string; model: string; cost: number; tokens: number; percentage: number }>;
  timeline: Array<{ timestamp: string; cumulative_cost: number; event_name: string }>;
}

export interface CostHotspot {
  event_id: string;
  event_name: string;
  model: string;
  tokens_input: number;
  tokens_output: number;
  cost_usd: number;
  percentage_of_total: number;
}

export interface CostSuggestion {
  event_id: string;
  current_model: string;
  suggested_model: string;
  current_cost: number;
  estimated_savings: number;
  reason: string;
}

// ===== HALLUCINATION TYPES =====

export interface HallucinationAlert {
  id: string;
  session_id: string;
  trace_event_id: string;
  source_event_id: string;
  severity: Severity;
  description: string;
  expected_value: string;
  actual_value: string;
  similarity_score: number;
  detected_at: string;
}

export interface HallucinationSummary {
  total: number;
  critical: number;
  warning: number;
  info: number;
}

// ===== MEMORY TYPES =====

export type MemoryAction = 'created' | 'updated' | 'accessed' | 'deleted';

export interface MemoryEntry {
  id: string;
  session_id: string;
  agent_id: string;
  memory_key: string;
  content: string;
  action: MemoryAction;
  version: number;
  timestamp: string;
  influenced_events: string[] | null;
  metadata: Record<string, any> | null;
}

// ===== WEBSOCKET TYPES =====

export type WSMessageType =
  | 'trace_event'
  | 'session_start'
  | 'session_end'
  | 'hallucination_detected'
  | 'memory_update'
  | 'get_sessions'
  | 'get_session_events'
  | 'clear_session';

export interface WSMessage {
  type: WSMessageType;
  data?: any;
  session_id?: string;
}

// ===== UI STATE TYPES =====

export interface ReplayState {
  session_id: string;
  events: TraceEvent[];
  current_step: number;
  is_playing: boolean;
  playback_speed: number;       // 0.5, 1, 2, 5
  total_steps: number;
}

export interface FilterState {
  event_types: EventType[];
  search_query: string;
  session_id: string | null;
}
```

---

## 11. Pydantic Schemas (Server)

**File: `server/src/schemas/trace.py`**

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any

class TraceEventCreate(BaseModel):
    id: Optional[str] = None  # Auto-generated if not provided
    session_id: str
    parent_event_id: Optional[str] = None
    event_type: str  # 'llm_call', 'tool_call', 'decision', 'memory_read', 'memory_write', 'user_input', 'error'
    event_name: str
    timestamp: Optional[datetime] = None
    duration_ms: float = 0.0
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    model: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: Optional[float] = None  # Auto-calculated if not provided
    status: str = "success"
    error_message: Optional[str] = None
    metadata: Optional[dict] = None

class TraceEventResponse(BaseModel):
    id: str
    session_id: str
    parent_event_id: Optional[str]
    event_type: str
    event_name: str
    timestamp: datetime
    duration_ms: float
    input_data: Optional[Any]
    output_data: Optional[Any]
    model: Optional[str]
    tokens_input: int
    tokens_output: int
    cost_usd: float
    status: str
    error_message: Optional[str]
    metadata: Optional[dict]

class TraceIngestRequest(BaseModel):
    session_id: str
    events: list[TraceEventCreate]

class TraceIngestResponse(BaseModel):
    ingested: int
    session_id: str
```

---

## 12. Error Handling Strategy

Every component must follow these error handling rules:

**SDK (Python & TypeScript):**
- NEVER raise/throw exceptions to the user's code
- Wrap all operations in try/except (try/catch)
- On connection failure: silently buffer, then drop if buffer exceeds limit
- Log warnings to stderr (not stdout) using `logging.warning()` / `console.warn()`

**Server:**
- Return proper HTTP status codes: 400 for bad request, 404 for not found, 500 for server error
- All 500 errors include a JSON body: `{ "error": "message", "detail": "stack trace in dev mode" }`
- WebSocket errors: send `{ "type": "error", "message": "..." }` and keep connection alive
- Database errors: log full traceback, return 500 to client

**Dashboard:**
- API call failures: show toast notification with error message, do not crash
- WebSocket disconnect: show "Disconnected" indicator in TopBar, auto-retry every 5 seconds
- Empty states: every page has a friendly empty state component with instructions
- All pages wrapped in error boundary component

---

## 13. Testing Requirements

### 13.1 Server Tests

```
server/tests/
├── test_trace_ingestion.py     # Test POST /traces with valid/invalid data
├── test_sessions.py            # Test session CRUD
├── test_cost_calculation.py    # Test pricing engine accuracy
├── test_hallucination.py       # Test hallucination detection with known mismatches
├── test_websocket.py           # Test WS connection, broadcast, reconnection
└── conftest.py                 # Fixtures: test database, test client
```

**Required test cases:**
1. Ingest 10 trace events → verify all stored in DB
2. Ingest event with unknown model → verify cost = 0.0 (not error)
3. Ingest event with missing optional fields → verify defaults applied
4. Cost calculation for each model in pricing table → verify correct to 6 decimal places
5. Hallucination detection: tool returns "$2.3M", LLM reports "$3.2M" → verify CRITICAL alert generated
6. Hallucination detection: tool and LLM match → verify no alert
7. WebSocket: connect, send event, verify broadcast received
8. Session: create, list, delete → verify lifecycle

### 13.2 SDK Python Tests

```
sdk-python/tests/
├── test_trace_decorator.py      # Test @trace captures events correctly
├── test_client.py               # Test buffering, flushing, graceful degradation
├── test_interceptors.py         # Test monkey-patching (mock OpenAI/Anthropic)
└── conftest.py
```

**Required test cases:**
1. `@trace` decorator on async function → verify event captured with correct input/output
2. `@trace` decorator when server is down → verify no exception raised, function returns normally
3. OpenAI interceptor with mock client → verify LLM call event captured with tokens
4. Buffer exceeds max size → verify flush is triggered
5. Sensitive data redaction → verify api_key fields are replaced with "[REDACTED]"

---

## 14. README.md Specification

The root README.md must follow this exact structure for maximum GitHub impact:

```markdown
<div align="center">

# 🔍 AgentLens

### Chrome DevTools for AI Agents

**See every decision, trace every tool call, catch every hallucination.**

[Demo Video GIF here — 800px wide, showing dashboard in action]

[![GitHub Stars](badge)](link)
[![License: MIT](badge)](link)
[![PyPI](badge)](link)
[![npm](badge)](link)

[Quick Start](#quick-start) · [Documentation](#documentation) · [Examples](#examples) · [Contributing](#contributing)

</div>

---

## Why AgentLens?

(3 sentences max explaining the problem and solution)

## Quick Start

### 1. Install & run the server

\`\`\`bash
pip install agentlens-server
agentlens-server
\`\`\`

### 2. Install the SDK

\`\`\`bash
pip install agentlens
\`\`\`

### 3. Add two lines to your agent

\`\`\`python
from agentlens import auto_instrument
auto_instrument()

# That's it. Open http://localhost:5173
\`\`\`

## Features

(Screenshot of each tab with 1-sentence description)

## Supported Frameworks

(Table of frameworks with checkmarks)

## MCP Integration

(3-line setup for MCP)

## Contributing

(Brief guidelines + link to CONTRIBUTING.md)

## License

MIT
```

---

## 15. Build Order (Critical)

**Claude Code must build the project in this exact order to avoid dependency issues:**

### Step 1: Initialize Repository
- Create root directory structure
- Create all configuration files (Makefile, docker-compose.yml, .gitignore, LICENSE, README.md)

### Step 2: Build Server (Backend)
- Create pyproject.toml and requirements.txt
- Implement config.py (pydantic-settings)
- Implement database.py (SQLAlchemy async engine, create_all_tables function)
- Implement ORM models (session.py, trace_event.py, memory_entry.py, hallucination alert model)
- Implement Pydantic schemas
- Implement utils (pricing.py, text_similarity.py)
- Implement services (trace_service.py, cost_service.py, hallucination_service.py, memory_service.py, replay_service.py)
- Implement WebSocket manager and handlers
- Implement REST routers (traces, sessions, costs, hallucinations, memory)
- Implement main.py (FastAPI app with CORS, routers, WebSocket endpoint, startup event for DB init)
- Alembic setup and initial migration
- Write server tests

### Step 3: Build Python SDK
- Create pyproject.toml
- Implement types.py and config.py
- Implement client.py (WebSocket + HTTP transport)
- Implement trace.py (@trace decorator, TracerContext, init(), auto_instrument())
- Implement interceptors (openai, anthropic, langchain, generic)
- Implement __init__.py with clean public API exports
- Write SDK tests

### Step 4: Build TypeScript SDK
- Create package.json, tsconfig.json
- Implement types.ts, config.ts
- Implement client.ts
- Implement trace.ts
- Implement interceptors (openai.ts, anthropic.ts, generic.ts)
- Implement index.ts exports

### Step 5: Build Dashboard (Frontend)
- Create package.json, vite.config.ts, tsconfig.json, tailwind.config.js, postcss.config.js
- Create index.html with font imports (Google Fonts: JetBrains Mono, IBM Plex Sans)
- Create index.css with CSS variables (full color palette from Section 3.2)
- Implement TypeScript types (copy from Section 10)
- Implement Zustand stores (traceStore, sessionStore, settingsStore, websocketStore)
- Implement hooks (useWebSocket, useTraceGraph, useCostCalculator, useReplay)
- Implement shared components (JsonViewer, CodeBlock, EmptyState, LoadingSpinner, Badge, Tooltip, Modal, Toast)
- Implement layout components (Sidebar, TopBar, MainLayout)
- Implement Traces page components (TraceGraph with D3, TraceTimeline, TraceDetail, EventNode, EventBadge)
- Implement Costs page components (CostOverview, CostBreakdown, CostTimeline, CostHotspots)
- Implement Hallucinations page components (HallucinationPanel, DiffViewer, SeverityBadge)
- Implement Memory page components (MemoryTimeline, MemoryDetail, MemorySearch, MemoryInfluence)
- Implement Replay page components (ReplayPlayer, ReplayTimeline, ReplayState)
- Implement Settings page
- Implement App.tsx with React Router and all routes
- Implement main.tsx

### Step 6: Build MCP Server
- Create pyproject.toml
- Implement tools.py (tool definitions)
- Implement server.py (MCP server with tool handlers)

### Step 7: Build Example Agents
- demo_openai_agent.py
- demo_anthropic_agent.py
- demo_multi_step.py (the showcase demo with intentional hallucination + memory ops)
- demo_langchain_agent.py

### Step 8: Integration Testing
- Run server + dashboard + demo agent together
- Verify full flow: agent → SDK → server → WebSocket → dashboard
- Fix any issues

---

## 16. Critical Implementation Notes

1. **CORS:** The FastAPI server MUST include CORS middleware allowing `http://localhost:5173` (dashboard dev server). Add `allow_origins=["*"]` for development.

2. **Startup:** The server must auto-create the SQLite database and tables on first run. No manual migration step required for getting started.

3. **WebSocket + REST Coexistence:** The server runs both a WebSocket server (port 8765) and an HTTP REST server (port 8766). Use FastAPI's built-in WebSocket support OR run them on the same port with different paths. Recommended: single FastAPI app on port 8766 with WebSocket at `/ws` and REST at `/api/v1/*`.

4. **Dashboard Empty State:** When the dashboard first opens and no agent has connected yet, it must show a beautiful empty state on the Traces page with:
   - The AgentLens logo
   - "Waiting for agent connection..."
   - Code snippet showing how to install and connect the SDK
   - Animated subtle pulse on the "waiting" indicator

5. **JSON Serialization:** All JSON fields in the database (input_data, output_data, metadata, influenced_events) must be stored as TEXT and serialized/deserialized in the service layer. Use `json.dumps()` on write and `json.loads()` on read.

6. **Timestamp Handling:** All timestamps use ISO 8601 format with timezone (UTC). The server generates timestamps if the SDK doesn't provide them.

7. **ID Generation:** Use ULIDs (not UUIDs) for all IDs. ULIDs are sortable by time, which makes database queries more efficient and trace ordering natural.

8. **Hot Reload:** Both the server (uvicorn --reload) and dashboard (vite dev server) must support hot reload for development.

9. **Single Port Alternative:** If running both WebSocket and HTTP on the same port is complex, the simpler approach is: FastAPI on port 8766 handles both REST endpoints AND the WebSocket endpoint at `ws://localhost:8766/ws`. The dashboard connects to this single port. Update all documentation and configuration accordingly.

10. **Graceful Shutdown:** The server must handle SIGINT/SIGTERM gracefully — flush any pending writes, close WebSocket connections cleanly, and exit.

---

## 17. Quality Standards

- **TypeScript:** Strict mode enabled. No `any` types except in JSON data fields. All components have proper type annotations.
- **Python:** Type hints on all function signatures. Pydantic models for all data boundaries.
- **Code Style:** Consistent formatting. Python: follow PEP 8. TypeScript: use Prettier defaults.
- **Comments:** Each file has a module-level docstring/comment explaining its purpose. Complex functions have inline comments explaining non-obvious logic.
- **Error Messages:** All user-facing error messages are clear and actionable. Never show raw stack traces in the dashboard.
- **Performance:** Dashboard renders 100+ trace nodes at 60fps. Server handles 1000 events/second ingestion. SDK adds <5ms overhead per traced call.
- **Accessibility:** Dashboard has proper ARIA labels, keyboard navigation for all interactive elements, and sufficient color contrast.

---

*End of PRD. Claude Code: build all of the above. Start with Step 1 from Section 15 and proceed sequentially. Do not skip any component. Every file described in this document must exist in the final output.*
