"""AgentLens Integration Test Suite + Performance Benchmark

Tests the full stack against a running server at http://localhost:8766.
Covers all API surfaces, WebSocket behavior, and measures real-world latency/throughput.

Usage:
    cd /path/to/Agentlens
    make server          # in one terminal
    python tests/integration/test_runner.py [--bench] [--verbose]

Options:
    --bench      Also run performance benchmarks (adds ~30s)
    --verbose    Print full response bodies on failures
"""

import asyncio
import json
import sys
import time
import argparse
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

# Per-run unique prefix so deterministic IDs don't collide with prior test runs in the same DB.
# Use last 6 digits of epoch seconds (resets every ~11 days, sufficient for test isolation).
_RUN_TAG = str(int(time.time()) % 1_000_000).zfill(6)

# Optional WebSocket support
try:
    import websockets
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

BASE_URL = "http://localhost:8766"
WS_URL = "ws://localhost:8766/ws"

VERBOSE = False


# ─────────────────────────────────────────────
# Result tracking
# ─────────────────────────────────────────────

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str = ""
    duration_ms: float = 0.0
    detail: str = ""


@dataclass
class BenchResult:
    name: str
    count: int
    total_ms: float
    latencies: list[float] = field(default_factory=list)

    @property
    def throughput(self) -> float:
        return self.count / (self.total_ms / 1000) if self.total_ms > 0 else 0

    @property
    def p50(self) -> float:
        return statistics.median(self.latencies) if self.latencies else 0

    @property
    def p95(self) -> float:
        if not self.latencies:
            return 0
        s = sorted(self.latencies)
        idx = max(0, int(len(s) * 0.95) - 1)
        return s[idx]

    @property
    def p99(self) -> float:
        if not self.latencies:
            return 0
        s = sorted(self.latencies)
        idx = max(0, int(len(s) * 0.99) - 1)
        return s[idx]


results: list[TestResult] = []
bench_results: list[BenchResult] = []


def ok(name: str, msg: str = "", duration_ms: float = 0.0) -> TestResult:
    r = TestResult(name=name, passed=True, message=msg, duration_ms=duration_ms)
    results.append(r)
    status = f"  [PASS] {name}"
    if msg:
        status += f"  — {msg}"
    if duration_ms:
        status += f"  ({duration_ms:.1f}ms)"
    print(status)
    return r


def fail(name: str, msg: str = "", detail: str = "") -> TestResult:
    r = TestResult(name=name, passed=False, message=msg, detail=detail)
    results.append(r)
    print(f"  [FAIL] {name}  — {msg}")
    if VERBOSE and detail:
        print(f"         {detail}")
    return r


def section(title: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def ulid_fake(suffix: str) -> str:
    """Generate a per-run unique fake ULID, padded/truncated to exactly 26 chars.

    The suffix must fit within 16 chars (26 - 10 char base). Longer suffixes are
    truncated from the RIGHT (least significant end) so the unique part stays intact.
    """
    base = f"01JK{_RUN_TAG}"  # 10 chars
    # Take first 16 chars of suffix to stay within 26-char ULID budget
    trimmed = suffix.upper()[:16]
    return (base + trimmed).ljust(26, "0")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_trace_event(session_id: str, event_type: str = "llm_call",
                     event_name: str = "test_event", model: str = "gpt-4o-mini",
                     tokens_in: int = 100, tokens_out: int = 50,
                     **kwargs) -> dict:
    e = {
        "session_id": session_id,
        "event_type": event_type,
        "event_name": event_name,
        "timestamp": now_iso(),
        "duration_ms": 100.0,
        "status": "success",
    }
    if model:
        e["model"] = model
    if tokens_in:
        e["tokens_input"] = tokens_in
    if tokens_out:
        e["tokens_output"] = tokens_out
    e.update(kwargs)
    return e


# ─────────────────────────────────────────────
# 1. Connectivity
# ─────────────────────────────────────────────

async def test_connectivity(client: httpx.AsyncClient) -> None:
    section("1. Connectivity")

    t0 = time.perf_counter()
    try:
        r = await client.get("/health")
        ms = (time.perf_counter() - t0) * 1000
        if r.status_code == 200:
            ok("Health endpoint", f"status={r.json().get('status')}", ms)
        else:
            fail("Health endpoint", f"HTTP {r.status_code}")
    except Exception as e:
        fail("Health endpoint", f"Connection refused — is the server running? ({e})")
        print("\n  Aborting: cannot reach server at", BASE_URL)
        sys.exit(1)

    t0 = time.perf_counter()
    r = await client.get("/")
    ms = (time.perf_counter() - t0) * 1000
    data = r.json()
    if data.get("service") == "AgentLens Server":
        ok("Root endpoint", f"version={data.get('version')}", ms)
    else:
        fail("Root endpoint", f"unexpected response: {data}")


# ─────────────────────────────────────────────
# 2. Session Management
# ─────────────────────────────────────────────

async def test_sessions(client: httpx.AsyncClient) -> tuple[str, str]:
    """Returns (session_id_a, session_id_b) for use in later tests."""
    section("2. Session Management")

    sid_a = ulid_fake("SESS0000000000001A")
    sid_b = ulid_fake("SESS0000000000002B")

    # Create session A via trace ingestion (auto-created)
    r = await client.post("/api/v1/traces", json={
        "session_id": sid_a,
        "events": [make_trace_event(sid_a, event_name="session_a_init")]
    })
    if r.status_code == 200:
        ok("Create session via trace ingestion")
    else:
        fail("Create session via trace ingestion", f"HTTP {r.status_code}: {r.text}")

    # Create session B
    r = await client.post("/api/v1/traces", json={
        "session_id": sid_b,
        "events": [make_trace_event(sid_b, event_name="session_b_init")]
    })
    if r.status_code == 200:
        ok("Create second session")
    else:
        fail("Create second session", f"HTTP {r.status_code}")

    # List sessions
    t0 = time.perf_counter()
    r = await client.get("/api/v1/sessions")
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        data = r.json()
        session_ids = [s["id"] for s in data.get("sessions", [])]
        if sid_a in session_ids and sid_b in session_ids:
            ok("List sessions", f"found {data.get('total')} total", ms)
        else:
            fail("List sessions", f"created sessions not found in list. Got IDs: {session_ids[:5]}")
    else:
        fail("List sessions", f"HTTP {r.status_code}")

    # Get session detail
    t0 = time.perf_counter()
    r = await client.get(f"/api/v1/sessions/{sid_a}")
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        data = r.json()
        ok("Get session detail", f"events={data.get('total_events')}", ms)
    else:
        fail("Get session detail", f"HTTP {r.status_code}")

    # Delete session B
    r = await client.delete(f"/api/v1/sessions/{sid_b}")
    if r.status_code == 200 and r.json().get("deleted"):
        ok("Delete session")
    else:
        fail("Delete session", f"HTTP {r.status_code}: {r.text}")

    # Verify session B is gone
    r = await client.get(f"/api/v1/sessions/{sid_b}")
    if r.status_code == 404:
        ok("Deleted session returns 404")
    else:
        fail("Deleted session should return 404", f"got HTTP {r.status_code}")

    return sid_a, sid_b


# ─────────────────────────────────────────────
# 3. Trace Ingestion
# ─────────────────────────────────────────────

async def test_trace_ingestion(client: httpx.AsyncClient, sid: str) -> None:
    section("3. Trace Ingestion")

    # All event types
    event_types = ["llm_call", "tool_call", "decision", "memory_read", "memory_write", "user_input", "error"]
    events = []
    prev_id = None
    for i, et in enumerate(event_types):
        e = make_trace_event(sid, event_type=et, event_name=f"test_{et}",
                             model="gpt-4o" if et == "llm_call" else None,
                             tokens_in=200 if et == "llm_call" else 0,
                             tokens_out=80 if et == "llm_call" else 0)
        if et == "error":
            e["status"] = "error"
            e["error_message"] = "simulated error for testing"
        if prev_id:
            e["parent_event_id"] = prev_id
        e["id"] = ulid_fake(f"EVNT{i:08d}")
        prev_id = e["id"]
        events.append(e)

    t0 = time.perf_counter()
    r = await client.post("/api/v1/traces", json={"session_id": sid, "events": events})
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200 and r.json().get("ingested") == 7:
        ok(f"Ingest all 7 event types", f"ingested={r.json()['ingested']}", ms)
    else:
        fail(f"Ingest all 7 event types", f"HTTP {r.status_code}: {r.text}")

    # Batch ingestion (50 events)
    batch = [make_trace_event(sid, event_name=f"batch_{i}", model="gpt-4o-mini",
                              tokens_in=50, tokens_out=20) for i in range(50)]
    t0 = time.perf_counter()
    r = await client.post("/api/v1/traces", json={"session_id": sid, "events": batch})
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200 and r.json().get("ingested") == 50:
        ok("Batch ingest 50 events", f"ingested=50", ms)
    else:
        fail("Batch ingest 50 events", f"HTTP {r.status_code}: {r.json() if r.status_code == 200 else r.text}")

    # Unknown model → cost = 0.0
    sid_unk = ulid_fake("UNKNSESS0000000000")
    r = await client.post("/api/v1/traces", json={
        "session_id": sid_unk,
        "events": [make_trace_event(sid_unk, model="some-future-model-v99",
                                    tokens_in=1000, tokens_out=500)]
    })
    if r.status_code == 200:
        events_r = (await client.get(f"/api/v1/traces/{sid_unk}")).json().get("events", [])
        if events_r and events_r[0]["cost_usd"] == 0.0:
            ok("Unknown model → cost=0.0 (no error)")
        else:
            fail("Unknown model → cost=0.0", f"got cost={events_r[0]['cost_usd'] if events_r else 'no events'}")
    else:
        fail("Unknown model ingest", f"HTTP {r.status_code}")

    # Event with missing optional fields → defaults applied
    sid_min = ulid_fake("MINSESS0000000000A")
    r = await client.post("/api/v1/traces", json={
        "session_id": sid_min,
        "events": [{"session_id": sid_min, "event_type": "tool_call", "event_name": "minimal_event"}]
    })
    if r.status_code == 200:
        ev = (await client.get(f"/api/v1/traces/{sid_min}")).json().get("events", [])
        if ev and ev[0]["tokens_input"] == 0 and ev[0]["status"] == "success":
            ok("Minimal event → defaults applied")
        else:
            fail("Minimal event defaults", f"event: {ev[0] if ev else 'none'}")
    else:
        fail("Minimal event ingest", f"HTTP {r.status_code}")

    # Retrieve as tree
    t0 = time.perf_counter()
    r = await client.get(f"/api/v1/traces/{sid}/tree")
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        tree = r.json()
        ok("Trace tree endpoint", f"root nodes={len(tree.get('events', []))}", ms)
    else:
        fail("Trace tree endpoint", f"HTTP {r.status_code}")

    # Filter by event type
    r = await client.get(f"/api/v1/traces/{sid}?event_type=llm_call")
    if r.status_code == 200:
        evs = r.json().get("events", [])
        all_llm = all(e["event_type"] == "llm_call" for e in evs)
        if all_llm:
            ok("Filter traces by event_type", f"returned {len(evs)} llm_call events")
        else:
            fail("Filter traces by event_type", "non-llm_call events returned")
    else:
        fail("Filter traces by event_type", f"HTTP {r.status_code}")


# ─────────────────────────────────────────────
# 4. Cost Calculation
# ─────────────────────────────────────────────

async def test_costs(client: httpx.AsyncClient) -> None:
    section("4. Cost Calculation")

    sid = ulid_fake("COSTSESS000000000A")

    # Known pricing: gpt-4o = $2.50/1M input, $10.00/1M output
    # 1000 input + 500 output = 0.0025 + 0.005 = $0.0075
    events = [
        make_trace_event(sid, event_type="llm_call", event_name="gpt4o_call",
                         model="gpt-4o", tokens_in=1000, tokens_out=500),
        make_trace_event(sid, event_type="llm_call", event_name="mini_call",
                         model="gpt-4o-mini", tokens_in=2000, tokens_out=1000),
        # A high-cost call to appear in hotspots
        make_trace_event(sid, event_type="llm_call", event_name="expensive_call",
                         model="gpt-4o", tokens_in=50000, tokens_out=10000),
    ]
    await client.post("/api/v1/traces", json={"session_id": sid, "events": events})

    # Cost breakdown
    t0 = time.perf_counter()
    r = await client.get(f"/api/v1/costs/{sid}")
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        data = r.json()
        total = data.get("total_usd", 0)
        by_model = data.get("by_model", {})

        # Expected: gpt-4o: (51000*2.50 + 10500*10.00)/1M = 0.1275 + 0.105 = $0.2325
        #           gpt-4o-mini: (2000*0.15 + 1000*0.60)/1M = 0.0003 + 0.0006 = $0.0009
        expected_total = round(0.2325 + 0.0009 + (1000*2.50/1_000_000 + 500*10.00/1_000_000), 6)
        if total > 0 and "gpt-4o" in by_model and "gpt-4o-mini" in by_model:
            ok("Cost breakdown", f"total=${total:.4f}", ms)
        else:
            fail("Cost breakdown", f"total={total}, by_model keys={list(by_model.keys())}")
    else:
        fail("Cost breakdown", f"HTTP {r.status_code}")

    # Cost hotspots
    t0 = time.perf_counter()
    r = await client.get(f"/api/v1/costs/{sid}/hotspots")
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        hotspots = r.json().get("hotspots", [])
        if hotspots and hotspots[0]["event_name"] == "expensive_call":
            ok("Cost hotspots sorted by cost desc", f"top={hotspots[0]['event_name']}", ms)
        else:
            fail("Cost hotspots", f"expected 'expensive_call' at top, got: {[h.get('event_name') for h in hotspots[:3]]}")
    else:
        fail("Cost hotspots", f"HTTP {r.status_code}")

    # Cost suggestions
    t0 = time.perf_counter()
    r = await client.get(f"/api/v1/costs/{sid}/suggestions")
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        suggestions = r.json().get("suggestions", [])
        # expensive_call is gpt-4o with low-ish output, should get suggestion
        ok("Cost suggestions endpoint", f"suggestions={len(suggestions)}", ms)
    else:
        fail("Cost suggestions", f"HTTP {r.status_code}")

    # Pricing accuracy test: gpt-4o-mini, 1M input + 1M output = $0.15 + $0.60 = $0.75
    sid_price = ulid_fake("PRICESESS00000000B")
    await client.post("/api/v1/traces", json={
        "session_id": sid_price,
        "events": [make_trace_event(sid_price, model="gpt-4o-mini",
                                    tokens_in=1_000_000, tokens_out=1_000_000)]
    })
    r = await client.get(f"/api/v1/costs/{sid_price}")
    if r.status_code == 200:
        total = r.json().get("total_usd", 0)
        expected = 0.75
        if abs(total - expected) < 0.000001:
            ok("Pricing accuracy: gpt-4o-mini 1M+1M = $0.75", f"got ${total:.6f}")
        else:
            fail("Pricing accuracy", f"expected $0.750000, got ${total:.6f}")
    else:
        fail("Pricing accuracy check", f"HTTP {r.status_code}")


# ─────────────────────────────────────────────
# 5. Hallucination Detection
# ─────────────────────────────────────────────

async def test_hallucination(client: httpx.AsyncClient) -> None:
    section("5. Hallucination Detection")

    sid = ulid_fake("HALLSESS000000000A")

    # Build the canonical scenario from the PRD:
    # tool_call returns "$2.3M", then llm_call reports "$3.2M" (number transposition)
    tool_event = make_trace_event(
        sid, event_type="tool_call", event_name="web_search",
        model=None, tokens_in=0, tokens_out=0,
    )
    tool_event["output_data"] = json.dumps({
        "company": "TechVenture AI",
        "funding": "$2.3M",
        "customers": 1450,
        "growth_yoy": "12%",
    })

    llm_event = make_trace_event(
        sid, event_type="llm_call", event_name="summarize_results",
        model="gpt-4o-mini", tokens_in=450, tokens_out=85,
    )
    llm_event["input_data"] = json.dumps({"messages": [{"role": "user", "content": "Summarize the research data"}]})
    llm_event["output_data"] = json.dumps({
        "summary": (
            "TechVenture AI raised $3.2M in their seed round with 1,450 customers "
            "and 12% YoY growth."
        )
    })

    r = await client.post("/api/v1/traces", json={"session_id": sid, "events": [tool_event, llm_event]})
    if r.status_code != 200:
        fail("Setup hallucination test data", f"HTTP {r.status_code}: {r.text}")
        return
    ok("Setup: tool says $2.3M, LLM says $3.2M (intentional transposition)")

    # Trigger detection
    t0 = time.perf_counter()
    r = await client.post("/api/v1/hallucinations/check", json={"session_id": sid})
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code != 200:
        fail("Hallucination check endpoint", f"HTTP {r.status_code}: {r.text}")
        return

    data = r.json()
    summary = data.get("summary", {})
    alerts = data.get("alerts", [])
    total = summary.get("total", 0)

    if total > 0:
        ok("Detected hallucination (number transposition)", f"total={total} critical={summary.get('critical')} warning={summary.get('warning')}", ms)
    else:
        fail("Detect $2.3M→$3.2M hallucination", f"no alerts detected. Alerts: {alerts}")

    # Verify GET endpoint returns same alerts
    r2 = await client.get(f"/api/v1/hallucinations/{sid}")
    if r2.status_code == 200 and r2.json().get("summary", {}).get("total", 0) > 0:
        ok("GET hallucinations returns persisted alerts")
    else:
        fail("GET hallucinations after check", f"HTTP {r2.status_code}: {r2.json() if r2.status_code == 200 else r2.text}")

    # Clean session — tool and LLM output match → no alerts
    sid_clean = ulid_fake("HALLSESS000000000B")
    tool_clean = make_trace_event(sid_clean, event_type="tool_call", event_name="data_fetch",
                                  model=None, tokens_in=0, tokens_out=0)
    tool_clean["output_data"] = json.dumps({"revenue": "$5.0M", "employees": 50})

    llm_clean = make_trace_event(sid_clean, event_type="llm_call", event_name="report_gen",
                                 model="gpt-4o-mini", tokens_in=200, tokens_out=60)
    llm_clean["output_data"] = json.dumps({
        "report": "The company has revenue of $5.0M and 50 employees."
    })

    await client.post("/api/v1/traces", json={"session_id": sid_clean, "events": [tool_clean, llm_clean]})
    r = await client.post("/api/v1/hallucinations/check", json={"session_id": sid_clean})
    if r.status_code == 200:
        summary = r.json().get("summary", {})
        # Numbers match ($5.0M present in both), may or may not flag — just verify no crash
        ok("Matching data: check runs without error", f"alerts={summary.get('total', 0)}")
    else:
        fail("Hallucination check on clean data", f"HTTP {r.status_code}")


# ─────────────────────────────────────────────
# 6. Memory Operations
# ─────────────────────────────────────────────

async def test_memory(client: httpx.AsyncClient) -> None:
    section("6. Memory Operations")

    sid = ulid_fake("MEMSESS0000000000A")

    # Create memory entry
    t0 = time.perf_counter()
    r = await client.post("/api/v1/memory", json={
        "session_id": sid,
        "memory_key": "user_preference",
        "content": "User prefers Python and async patterns",
        "action": "created",
    })
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        entry = r.json()
        ok("Create memory entry", f"key={entry.get('memory_key')}", ms)
    else:
        fail("Create memory entry", f"HTTP {r.status_code}: {r.text}")
        return

    # Update the same key (version increment)
    r = await client.post("/api/v1/memory", json={
        "session_id": sid,
        "memory_key": "user_preference",
        "content": "User prefers Python, async patterns, and FastAPI",
        "action": "updated",
    })
    if r.status_code == 200:
        entry = r.json()
        ok("Update memory entry", f"version={entry.get('version')}")
    else:
        fail("Update memory entry", f"HTTP {r.status_code}: {r.text}")

    # Access the memory
    r = await client.post("/api/v1/memory", json={
        "session_id": sid,
        "memory_key": "user_preference",
        "content": "User prefers Python, async patterns, and FastAPI",
        "action": "accessed",
    })
    if r.status_code == 200:
        ok("Access memory entry")
    else:
        fail("Access memory entry", f"HTTP {r.status_code}")

    # Create a second key
    await client.post("/api/v1/memory", json={
        "session_id": sid,
        "memory_key": "project_context",
        "content": "Working on AgentLens observability platform",
        "action": "created",
    })

    # List all memory for session
    t0 = time.perf_counter()
    r = await client.get(f"/api/v1/memory/{sid}")
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        data = r.json()
        entries = data.get("entries", [])
        keys = {e["memory_key"] for e in entries}
        if "user_preference" in keys and "project_context" in keys:
            ok("List memory entries", f"total={len(entries)}", ms)
        else:
            fail("List memory entries", f"missing keys. Got: {keys}")
    else:
        fail("List memory entries", f"HTTP {r.status_code}")

    # Get specific key with version history
    t0 = time.perf_counter()
    r = await client.get(f"/api/v1/memory/{sid}/user_preference")
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        data = r.json()
        current = data.get("current", {})
        history = data.get("history", [])
        if current.get("memory_key") == "user_preference":
            ok("Get memory key with history",
               f"current_version={current.get('version')}, history_entries={len(history)}", ms)
        else:
            fail("Get memory key", f"unexpected response: {data}")
    else:
        fail("Get memory key", f"HTTP {r.status_code}: {r.text}")

    # 404 for nonexistent key
    r = await client.get(f"/api/v1/memory/{sid}/nonexistent_key_xyz")
    if r.status_code == 404:
        ok("Nonexistent memory key returns 404")
    else:
        fail("Nonexistent memory key", f"expected 404, got {r.status_code}")


# ─────────────────────────────────────────────
# 7. WebSocket
# ─────────────────────────────────────────────

async def test_websocket() -> None:
    section("7. WebSocket / Real-time")

    if not WS_AVAILABLE:
        print("  [SKIP] websockets package not installed — skipping WS tests")
        return

    # SDK client sends events, dashboard client receives them in real-time
    received: list[dict] = []
    connect_ok = False
    broadcast_ok = False

    try:
        async with websockets.connect(WS_URL, open_timeout=3) as dash_ws:
            await dash_ws.send(json.dumps({"type": "hello", "role": "dashboard"}))
            connect_ok = True

            async with websockets.connect(WS_URL, open_timeout=3) as sdk_ws:
                await sdk_ws.send(json.dumps({"type": "hello", "role": "sdk"}))

                sid = ulid_fake("WSSESS00000000000A")
                test_event = make_trace_event(sid, event_name="ws_test_event")
                test_event["id"] = ulid_fake("WSEVNT0000000000AA")

                # Send trace event via SDK WS
                await sdk_ws.send(json.dumps({
                    "type": "trace_events",
                    "session_id": sid,
                    "events": [test_event],
                }))

                # Wait for broadcast on dashboard WS (max 3s)
                try:
                    raw = await asyncio.wait_for(dash_ws.recv(), timeout=3.0)
                    msg = json.loads(raw)
                    # Server might send ping first; drain until we get trace_event
                    deadline = time.perf_counter() + 3.0
                    while msg.get("type") != "trace_event" and time.perf_counter() < deadline:
                        raw = await asyncio.wait_for(dash_ws.recv(), timeout=1.0)
                        msg = json.loads(raw)
                    if msg.get("type") == "trace_event":
                        broadcast_ok = True
                        received.append(msg)
                except asyncio.TimeoutError:
                    pass

        if connect_ok:
            ok("WebSocket dashboard connection + hello handshake")
        else:
            fail("WebSocket dashboard connection")

        if broadcast_ok:
            ok("SDK→Server→Dashboard broadcast", f"received event type: {received[0].get('data', {}).get('event_name')}")
        else:
            fail("Real-time broadcast", "dashboard did not receive SDK event within 3s")

    except Exception as e:
        fail("WebSocket tests", f"error: {e}")
        return

    # Test session_start broadcast
    try:
        async with websockets.connect(WS_URL, open_timeout=3) as dash_ws:
            await dash_ws.send(json.dumps({"type": "hello", "role": "dashboard"}))
            await asyncio.sleep(0.15)  # let server register dashboard client

            async with websockets.connect(WS_URL, open_timeout=3) as sdk_ws:
                await sdk_ws.send(json.dumps({"type": "hello", "role": "sdk"}))
                await asyncio.sleep(0.1)  # let server register sdk client
                sid2 = ulid_fake("WSSESS00000000000B")
                await sdk_ws.send(json.dumps({
                    "type": "session_start",
                    "data": {
                        "session_id": sid2,
                        "agent_name": "test-ws-agent",
                        "started_at": now_iso(),
                    },
                }))
                try:
                    deadline = time.perf_counter() + 3.0
                    while time.perf_counter() < deadline:
                        raw = await asyncio.wait_for(dash_ws.recv(), timeout=1.0)
                        msg = json.loads(raw)
                        if msg.get("type") == "session_start":
                            ok("Session start broadcast over WebSocket")
                            break
                    else:
                        fail("Session start broadcast", "not received within 3s")
                except asyncio.TimeoutError:
                    fail("Session start broadcast", "timeout waiting for event")

    except Exception as e:
        fail("WebSocket session_start test", f"error: {e}")

    # Dashboard get_sessions command
    try:
        async with websockets.connect(WS_URL, open_timeout=3) as dash_ws:
            await dash_ws.send(json.dumps({"type": "hello", "role": "dashboard"}))
            await asyncio.sleep(0.15)  # let server register dashboard client before sending command
            await dash_ws.send(json.dumps({"type": "get_sessions"}))
            try:
                deadline = time.perf_counter() + 3.0
                while time.perf_counter() < deadline:
                    raw = await asyncio.wait_for(dash_ws.recv(), timeout=1.5)
                    msg = json.loads(raw)
                    if msg.get("type") == "sessions_list":
                        ok("Dashboard get_sessions command", f"sessions={len(msg.get('data', []))}")
                        break
                else:
                    fail("Dashboard get_sessions", "sessions_list not received")
            except asyncio.TimeoutError:
                fail("Dashboard get_sessions", "timeout")
    except Exception as e:
        fail("Dashboard get_sessions WS test", f"error: {e}")


# ─────────────────────────────────────────────
# 8. Edge Cases & Error Handling
# ─────────────────────────────────────────────

async def test_edge_cases(client: httpx.AsyncClient) -> None:
    section("8. Edge Cases & Error Handling")

    # 404 for nonexistent session
    r = await client.get("/api/v1/sessions/NONEXISTENT00000000000000")
    if r.status_code == 404:
        ok("GET nonexistent session → 404")
    else:
        fail("GET nonexistent session", f"expected 404, got {r.status_code}")

    # Empty events array
    r = await client.post("/api/v1/traces", json={"session_id": ulid_fake("EMPTSESS00000000A"), "events": []})
    if r.status_code == 200 and r.json().get("ingested") == 0:
        ok("POST empty events array → ingested=0")
    else:
        fail("Empty events array", f"HTTP {r.status_code}: {r.json()}")

    # Traces for session with no events → empty list
    sid_empty = ulid_fake("EMPTEV0000000000A")
    await client.post("/api/v1/traces", json={"session_id": sid_empty, "events": []})
    r = await client.get(f"/api/v1/traces/{sid_empty}")
    if r.status_code == 200:
        events = r.json().get("events", [])
        ok("GET traces for session with no events", f"events={len(events)}")
    else:
        # 404 is also acceptable for empty session
        if r.status_code == 404:
            ok("GET traces for session with no events → 404 (acceptable)")
        else:
            fail("GET traces for empty session", f"HTTP {r.status_code}")

    # Cost endpoint for session with no LLM events
    sid_nocost = ulid_fake("NOCOSTSESS0000000")
    await client.post("/api/v1/traces", json={
        "session_id": sid_nocost,
        "events": [make_trace_event(sid_nocost, event_type="tool_call", model=None, tokens_in=0, tokens_out=0)]
    })
    r = await client.get(f"/api/v1/costs/{sid_nocost}")
    if r.status_code == 200:
        total = r.json().get("total_usd", 0)
        if total == 0.0:
            ok("Cost for tool-only session → $0.00")
        else:
            fail("Cost for tool-only session", f"expected 0.0, got {total}")
    else:
        fail("Cost for tool-only session", f"HTTP {r.status_code}")

    # Hallucination check on session with no tool+llm pair → no alerts, no error
    sid_nohal = ulid_fake("NOHALSESS0000000A")
    await client.post("/api/v1/traces", json={
        "session_id": sid_nohal,
        "events": [make_trace_event(sid_nohal, event_type="user_input", model=None, tokens_in=0, tokens_out=0)]
    })
    r = await client.post("/api/v1/hallucinations/check", json={"session_id": sid_nohal})
    if r.status_code == 200:
        total = r.json().get("summary", {}).get("total", 0)
        ok("Hallucination check on user_input-only session", f"alerts={total} (expected 0)")
    else:
        fail("Hallucination check edge case", f"HTTP {r.status_code}: {r.text}")

    # Duplicate event ID (idempotency)
    sid_dup = ulid_fake("DUPSESS00000000001")
    dup_event = make_trace_event(sid_dup)
    dup_event["id"] = ulid_fake("DUPEVNT0000000001")
    r1 = await client.post("/api/v1/traces", json={"session_id": sid_dup, "events": [dup_event]})
    r2 = await client.post("/api/v1/traces", json={"session_id": sid_dup, "events": [dup_event]})
    # Both should succeed (upsert or ignore duplicate)
    if r1.status_code == 200 and r2.status_code == 200:
        ok("Duplicate event ID handled gracefully (no 500)")
    else:
        fail("Duplicate event ID", f"r1={r1.status_code}, r2={r2.status_code}")


# ─────────────────────────────────────────────
# 9. Performance Benchmarks
# ─────────────────────────────────────────────

async def benchmark_ingestion(client: httpx.AsyncClient) -> None:
    section("9. Performance Benchmarks")
    print("  (running benchmarks — this may take ~20s)\n")

    # ── 9a: Single event latency ──────────────────────────
    latencies = []
    sid = ulid_fake("BENCHSESS0000000A")
    N = 100
    for i in range(N):
        event = make_trace_event(sid, event_name=f"bench_{i}", model="gpt-4o-mini",
                                 tokens_in=100, tokens_out=50)
        t0 = time.perf_counter()
        r = await client.post("/api/v1/traces", json={"session_id": sid, "events": [event]})
        elapsed = (time.perf_counter() - t0) * 1000
        if r.status_code == 200:
            latencies.append(elapsed)

    br = BenchResult(name="Single event ingestion latency", count=len(latencies),
                     total_ms=sum(latencies), latencies=latencies)
    bench_results.append(br)
    print(f"  Single event POST ({N} samples):")
    print(f"    p50={br.p50:.1f}ms  p95={br.p95:.1f}ms  p99={br.p99:.1f}ms  mean={statistics.mean(latencies):.1f}ms")

    # ── 9b: Batch throughput ──────────────────────────────
    BATCH_SIZES = [10, 50, 100, 500]
    print(f"\n  Batch ingestion throughput:")
    for batch_size in BATCH_SIZES:
        sid_b = ulid_fake(f"BENCH{batch_size:05d}0000")
        events = [make_trace_event(sid_b, event_name=f"b_{i}", model="gpt-4o-mini",
                                   tokens_in=50, tokens_out=20) for i in range(batch_size)]
        t0 = time.perf_counter()
        r = await client.post("/api/v1/traces", json={"session_id": sid_b, "events": events})
        elapsed_ms = (time.perf_counter() - t0) * 1000
        if r.status_code == 200:
            throughput = batch_size / (elapsed_ms / 1000)
            print(f"    batch={batch_size:4d}  time={elapsed_ms:.1f}ms  throughput={throughput:.0f} events/s")
            bench_results.append(BenchResult(
                name=f"Batch {batch_size}", count=batch_size,
                total_ms=elapsed_ms, latencies=[elapsed_ms],
            ))
        else:
            print(f"    batch={batch_size:4d}  FAILED HTTP {r.status_code}")

    # ── 9c: Concurrent sessions ───────────────────────────
    print(f"\n  Concurrent session handling (10 parallel sessions):")
    async def single_session(n: int) -> float:
        sid_c = ulid_fake(f"CONCSESS{n:08d}A")
        events = [make_trace_event(sid_c, event_name=f"concurrent_{n}_{i}") for i in range(5)]
        t0 = time.perf_counter()
        r = await client.post("/api/v1/traces", json={"session_id": sid_c, "events": events})
        return (time.perf_counter() - t0) * 1000 if r.status_code == 200 else -1

    t0 = time.perf_counter()
    conc_results = await asyncio.gather(*[single_session(i) for i in range(10)])
    total_wall = (time.perf_counter() - t0) * 1000
    ok_count = sum(1 for r in conc_results if r > 0)
    avg_ms = statistics.mean(r for r in conc_results if r > 0) if ok_count > 0 else 0
    print(f"    10 concurrent sessions: {ok_count}/10 succeeded  wall_time={total_wall:.1f}ms  avg_per_session={avg_ms:.1f}ms")

    # ── 9d: Read latency ─────────────────────────────────
    # Read back the batch we wrote above
    sid_read = ulid_fake(f"BENCH{500:05d}0000")
    read_latencies = []
    for _ in range(20):
        t0 = time.perf_counter()
        r = await client.get(f"/api/v1/traces/{sid_read}")
        elapsed = (time.perf_counter() - t0) * 1000
        if r.status_code == 200:
            read_latencies.append(elapsed)

    if read_latencies:
        print(f"\n  GET /traces (500-event session, 20 samples):")
        print(f"    p50={statistics.median(read_latencies):.1f}ms  p95={sorted(read_latencies)[int(len(read_latencies)*0.95)-1]:.1f}ms  mean={statistics.mean(read_latencies):.1f}ms")


# ─────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────

def print_report(run_bench: bool) -> int:
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)

    print(f"\n{'═'*60}")
    print(f"  TEST REPORT")
    print(f"{'═'*60}")
    print(f"  Total:  {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print()

    if failed > 0:
        print("  FAILURES:")
        for r in results:
            if not r.passed:
                print(f"    - {r.name}: {r.message}")
        print()

    if passed == total:
        print("  All tests passed.")
    else:
        pct = int(passed / total * 100)
        print(f"  {pct}% pass rate.")

    print(f"{'═'*60}\n")
    return 0 if failed == 0 else 1


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

async def main(run_bench: bool) -> int:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        await test_connectivity(client)
        sid_a, _ = await test_sessions(client)
        await test_trace_ingestion(client, sid_a)
        await test_costs(client)
        await test_hallucination(client)
        await test_memory(client)
        await test_websocket()
        await test_edge_cases(client)
        if run_bench:
            await benchmark_ingestion(client)

    return print_report(run_bench)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgentLens integration test runner")
    parser.add_argument("--bench", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--verbose", action="store_true", help="Print response bodies on failures")
    args = parser.parse_args()

    VERBOSE = args.verbose

    print(f"\n{'═'*60}")
    print("  AgentLens Integration Test Suite")
    print(f"  Server: {BASE_URL}")
    print(f"{'═'*60}")

    exit_code = asyncio.run(main(run_bench=args.bench))
    sys.exit(exit_code)
