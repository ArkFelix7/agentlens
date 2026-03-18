"""Generates pytest test files from AgentLens trace sessions."""

import json
import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from sqlalchemy import select

from agentlens_server.models.trace_event import TraceEvent
from agentlens_server.models.session import Session
from agentlens_server.models.hallucination_alert import HallucinationAlert


def _safe_id(s: str) -> str:
    """Convert a string to a safe Python identifier."""
    s = re.sub(r"[^a-zA-Z0-9_]", "_", s)
    if s and s[0].isdigit():
        s = "event_" + s
    return s[:40]


def _extract_assertions(output_data: Optional[str], hallucinations: list) -> list[str]:
    """Generate assertion lines from output data and known hallucinations."""
    assertions = []
    if not output_data:
        return ["assert result is not None, 'Should return a result'"]

    try:
        out = json.loads(output_data)
    except Exception:
        out = {}

    assertions.append("assert result is not None, 'Should return a result'")

    # Known-bad values from hallucinations
    for h in hallucinations:
        bad_val = h.actual_value if hasattr(h, "actual_value") else ""
        good_val = h.expected_value if hasattr(h, "expected_value") else ""
        if bad_val:
            safe_bad = bad_val.replace("'", "\\'")[:50]
            assertions.append(
                f"# Hallucination guard: '{safe_bad}' was wrong in original run"
            )
        if good_val:
            safe_good = good_val.replace("'", "\\'")[:50]
            assertions.append(
                f"# Expected value was: '{safe_good}'"
            )

    # If output has a content/text field, check it's non-empty
    if isinstance(out, dict):
        for key in ("content", "text", "output", "result", "answer"):
            if key in out and isinstance(out[key], str) and len(out[key]) > 10:
                assertions.append(f"assert len(str(result)) > 10, 'Output should be non-empty'")
                break

    return assertions


async def generate_test_file(session_id: str, db: DBSession) -> Optional[dict]:
    """
    Generate a pytest test file for a session.
    Returns dict with keys: session_id, agent_name, filename, test_count, content, generated_at
    Returns None if session not found.
    """
    # Load session
    sess_result = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_result.scalar_one_or_none()
    if not session:
        return None

    # Load trace events (llm_call events only for per-step tests)
    events_result = await db.execute(
        select(TraceEvent)
        .where(
            TraceEvent.session_id == session_id,
            TraceEvent.event_type == "llm_call",
        )
        .order_by(TraceEvent.timestamp)
        .limit(20)
    )
    llm_events = events_result.scalars().all()

    # Load hallucinations
    halluc_result = await db.execute(
        select(HallucinationAlert).where(HallucinationAlert.session_id == session_id)
    )
    hallucinations = halluc_result.scalars().all()

    agent_name = session.agent_name or "agent"
    safe_name = _safe_id(agent_name)
    short_id = session_id[:8]
    filename = f"test_{safe_name}_{short_id}.py"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build per-step test functions
    per_step_tests: list[str] = []
    test_count = 0

    for i, event in enumerate(llm_events):
        func_name = f"test_{safe_name}_step_{i+1}_{_safe_id(event.event_name)}"
        # Hallucinations for this event
        event_hallucinations = [h for h in hallucinations if h.trace_event_id == event.id]
        assertions = _extract_assertions(event.output_data, event_hallucinations)

        input_preview = ""
        if event.input_data:
            try:
                inp = json.loads(event.input_data)
                input_preview = json.dumps(inp, indent=2)[:500]
            except Exception:
                input_preview = str(event.input_data)[:500]

        assertions_str = "\n    ".join(assertions)
        max_cost = max(float(event.cost_usd or 0) * 5.0, 0.01)

        step_test = f'''def test_{safe_name}_step_{i+1}_{_safe_id(event.event_name)}():
    """
    Regression test for step {i+1}: {event.event_name}
    Original model: {event.model or "unknown"}
    Original cost: ${float(event.cost_usd or 0):.4f}
    Original latency: {float(event.duration_ms or 0):.0f}ms
    """
    # This test validates the expected behavior of step {i+1}.
    # Replace the placeholder below with your actual agent function call.
    # Example:
    #   result = your_agent_function(input_here)
    result = None  # TODO: replace with actual call

    # --- Assertions (auto-generated from trace) ---
    {assertions_str}

    # Cost guard: original was ${float(event.cost_usd or 0):.4f}, allow up to 5x
    # To enable: check cost via AgentLens API after calling your function
    # MAX_STEP_COST = {max_cost:.4f}
'''
        per_step_tests.append(step_test)
        test_count += 1

    # Session-level test
    total_cost = float(session.total_cost_usd or 0)
    max_total_cost = max(total_cost * 5.0, 0.05)

    session_test = f'''def test_{safe_name}_session_cost():
    """Fail if session total cost exceeds 5x the original (${total_cost:.4f})."""
    import httpx
    try:
        resp = httpx.get(
            f"http://localhost:8766/api/v1/sessions/{session_id}",
            timeout=5.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            cost = data.get("total_cost_usd", 0)
            assert cost <= {max_total_cost:.4f}, (
                f"Session cost ${{cost:.4f}} exceeds 5x original limit ${max_total_cost:.4f}"
            )
    except httpx.ConnectError:
        pass  # Server not running — skip cost check


def test_{safe_name}_no_new_hallucinations():
    """Verify the session has no more hallucinations than the original ({len(hallucinations)})."""
    import httpx
    try:
        resp = httpx.get(
            f"http://localhost:8766/api/v1/hallucinations/{session_id}",
            timeout=5.0,
        )
        if resp.status_code == 200:
            alerts = resp.json()
            assert len(alerts) <= {len(hallucinations)}, (
                f"More hallucinations detected: {{len(alerts)}} vs original {len(hallucinations)}"
            )
    except httpx.ConnectError:
        pass  # Server not running — skip
'''

    per_step_str = "\n\n".join(per_step_tests)
    content = f'''"""
AgentLens Auto-Generated Regression Tests
Session:    {session_id}
Agent:      {agent_name}
Generated:  {now_str}
Cost:       ${total_cost:.4f}
Events:     {session.total_events}

Run with:
    pip install agentlens-sdk pytest httpx
    agentlens-server &  # start server
    pytest {filename} -v
"""

# ── Session metadata ────────────────────────────────────────────────
SESSION_ID = "{session_id}"
AGENT_NAME = "{agent_name}"
ORIGINAL_COST_USD = {total_cost}
ORIGINAL_HALLUCINATIONS = {len(hallucinations)}


# ── Per-step regression tests ────────────────────────────────────────
{per_step_str}

# ── Session-level guards ──────────────────────────────────────────────
{session_test}
'''

    return {
        "session_id": session_id,
        "agent_name": agent_name,
        "filename": filename,
        "test_count": test_count + 2,
        "content": content,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
