"""demo_recording.py — Purpose-built demo for AgentLens screen recording.

Scenario: A VC research agent preparing a board deck on TechVenture AI.

Event flow (11 events, ~40 seconds):
  1.  user_input      — analyst query
  2.  tool_call       — web_search (returns $2.3M ground truth)
  3.  tool_call       — fetch_company_profile (confirms $2.3M)
  4.  llm_call        — assess_investment_thesis (REAL Claude Haiku)
  5.  decision        — analysis_depth
  6.  memory_write    — save_research_context (v1)
  7.  llm_call        — summarize_financials (mock, labeled claude-sonnet-4-6)
                        ← INTENTIONAL HALLUCINATION: $2.3M → $3.2M
  8.  tool_call       — fetch_market_data
  9.  llm_call        — write_investment_memo (REAL OpenAI gpt-4o-mini)
  10. memory_write    — save_recommendation (v2)
  11. memory_read     — recall_research_context

Cost breakdown shows 3 models: claude-haiku, claude-sonnet-4-6, gpt-4o-mini
Hallucination detector flags event 7 (critical: $3.2M vs $2.3M)
Memory tab shows analyst_focus key with 2-version history

Usage:
    # With real APIs (recommended for recording):
    ANTHROPIC_API_KEY=sk-ant-... OPENAI_API_KEY=sk-... python examples/demo_recording.py

    # Without API keys (all mocked, hallucination still works):
    python examples/demo_recording.py

Requirements:
    pip install agentlens-sdk anthropic openai
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

# Local dev fallback (not needed if `pip install agentlens-sdk` was run)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk-python", "src"))

from agentlens_sdk import init
from agentlens_sdk.client import AgentLensClient
from agentlens_sdk.trace import SpanContext, get_client
from ulid import ULID

# ── Config ────────────────────────────────────────────────────────────────────
WS_URL        = os.getenv("AGENTLENS_WS_URL",  "ws://localhost:8766/ws")
HTTP_URL      = os.getenv("AGENTLENS_HTTP_URL", "http://localhost:8766")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY")

# ── Ground-truth data (tool outputs = the facts) ─────────────────────────────
SEARCH_RESULTS = {
    "query": "TechVenture AI funding 2025",
    "results": [
        {
            "title": "TechVenture AI closes $2.3M seed round",
            "snippet": (
                "TechVenture AI announced a $2.3M seed round led by Sequoia Capital. "
                "The startup reports 1,450 enterprise customers and 12% MoM growth."
            ),
            "url": "https://techcrunch.example.com/techventure-ai-seed-2025",
            "published": "2025-11-14",
        }
    ],
}

COMPANY_PROFILE = {
    "company": "TechVenture AI",
    "funding_total": "$2.3M",          # ← canonical ground truth
    "lead_investor": "Sequoia Capital",
    "customers": 1450,
    "growth_mom": "12%",
    "arr": "$690K",
    "nps_score": 72,
    "founded": 2023,
    "focus": "enterprise workflow automation",
    "hq": "San Francisco, CA",
}

MARKET_DATA = {
    "tam": "$18.4B",
    "segment": "enterprise AI automation",
    "cagr_5yr": "34%",
    "competitors": ["WorkflowAI", "AutomatePro", "FlowMind"],
    "market_leader_share": "22%",
    "deals_q1_2025": 203,
    "total_invested_q1_2025": "$847M",
}


# ── Real LLM callers ──────────────────────────────────────────────────────────
async def call_claude(prompt: str, system: str = "") -> tuple[str, int, int]:
    """Call claude-haiku-4-5-20251001. Falls back to mock if key missing."""
    if not ANTHROPIC_KEY:
        return _mock_claude(), 285, 98
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)
        kwargs: dict = dict(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            kwargs["system"] = system
        resp = await client.messages.create(**kwargs)
        return resp.content[0].text, resp.usage.input_tokens, resp.usage.output_tokens
    except Exception as exc:
        print(f"  [warn] Claude call failed ({exc}), using mock")
        return _mock_claude(), 285, 98


async def call_openai(prompt: str) -> tuple[str, int, int]:
    """Call gpt-4o-mini. Falls back to mock if key missing."""
    if not OPENAI_KEY:
        return _mock_openai(), 530, 145
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=OPENAI_KEY)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        text = resp.choices[0].message.content
        return text, resp.usage.prompt_tokens, resp.usage.completion_tokens
    except Exception as exc:
        print(f"  [warn] OpenAI call failed ({exc}), using mock")
        return _mock_openai(), 530, 145


def _mock_claude() -> str:
    return (
        "TechVenture AI presents a compelling seed-stage opportunity: strong Sequoia backing, "
        "1,450 enterprise customers at an NPS of 72, and 12% MoM growth on $690K ARR. "
        "Recommend advancing to diligence."
    )


def _mock_openai() -> str:
    return (
        "TechVenture AI is a Sequoia-backed enterprise AI automation startup with strong "
        "early traction (1,450 customers, 12% MoM growth) operating in a $18.4B TAM growing "
        "at 34% CAGR — a high-conviction addition to our Q4 watchlist."
    )


# ── The intentional hallucination (guaranteed) ────────────────────────────────
def _mock_financial_summary() -> tuple[str, int, int]:
    """Simulates a model that transposes $2.3M → $3.2M.

    This is the hallucination the detector will flag. In real deployments, models
    sometimes confuse funding figures with other rounds they've seen in training.
    The number-transposition detector (sorted digit comparison) catches this class
    of error reliably.
    """
    text = (
        "TechVenture AI closed a $3.2M seed round led by Sequoia Capital, "  # ← hallucinated
        "with 1,450 enterprise customers and 12% month-over-month growth. "
        "ARR is approximately $690K and NPS stands at 72. Founded 2023, "
        "focused on enterprise workflow automation out of San Francisco."
    )
    return text, 418, 109


# ── Main demo ─────────────────────────────────────────────────────────────────
async def run_demo() -> None:
    api_status = (
        "Claude Haiku + OpenAI gpt-4o-mini"
        if (ANTHROPIC_KEY and OPENAI_KEY)
        else "Claude Haiku (OpenAI mocked)"
        if ANTHROPIC_KEY
        else "OpenAI gpt-4o-mini (Claude mocked)"
        if OPENAI_KEY
        else "All mocked  (no API keys set)"
    )

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          AgentLens — VC Research Agent Demo                  ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Dashboard  →  http://localhost:5173                         ║")
    print(f"║  Server     →  {HTTP_URL:<46}║")
    print(f"║  LLM APIs   →  {api_status:<46}║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Init SDK
    session_id = str(ULID())
    init(
        server_url=WS_URL,
        http_url=HTTP_URL,
        agent_name="vc-research-agent",
        session_id=session_id,
    )
    client = get_client()
    await asyncio.sleep(0.6)  # WS handshake

    if client:
        await client.send_message({
            "type": "session_start",
            "data": {
                "session_id": session_id,
                "agent_name": "vc-research-agent",
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        })

    # ── Span helper ───────────────────────────────────────────────────────────
    async def span(
        etype: str,
        ename: str,
        inp=None,
        out=None,
        model: str | None = None,
        tin: int = 0,
        tout: int = 0,
        dur_ms: int = 0,
        parent: str | None = None,
    ) -> str:
        s = SpanContext(
            event_type=etype,
            event_name=ename,
            session_id=session_id,
            parent_event_id=parent,
            client=client,
        )
        if inp is not None:
            s.set_input(inp)
        if out is not None:
            s.set_output(out)
        if model:
            s.set_model(model)
        if tin or tout:
            s.set_tokens(tin, tout)
        s._start_time = time.perf_counter() - dur_ms / 1000
        s.end()
        await asyncio.sleep(0.65)  # pacing — lets dashboard animate node appearance
        return s.id

    # ── Memory helper ─────────────────────────────────────────────────────────
    async def write_memory(key: str, content: str, action: str, version: int = 1) -> None:
        payload = {
            "session_id": session_id,
            "memory_key": key,
            "content": content,
            "action": action,
        }
        if client:
            await client.send_message({"type": "memory_update", "data": payload})
        try:
            import aiohttp
            async with aiohttp.ClientSession() as sess:
                await sess.post(
                    f"{HTTP_URL}/api/v1/memory",
                    json={**payload, "version": version},
                    timeout=aiohttp.ClientTimeout(total=3),
                )
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 1 — User query
    # ═════════════════════════════════════════════════════════════════════════
    print("  [1/11]  Received analyst query")
    e1 = await span(
        "user_input", "analyst_query",
        inp={"query": "Research TechVenture AI — funding, traction, competitive position for Q4 board deck"},
        dur_ms=4,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 2 — Web search (ground truth: $2.3M)
    # ═════════════════════════════════════════════════════════════════════════
    print("  [2/11]  Web search → TechVenture AI funding")
    await asyncio.sleep(0.3)
    e2 = await span(
        "tool_call", "web_search",
        inp={"query": "TechVenture AI funding round 2025", "sources": ["techcrunch", "crunchbase", "pitchbook"]},
        out=SEARCH_RESULTS,
        dur_ms=412,
        parent=e1,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 3 — Fetch company profile (confirms $2.3M — this becomes last_tool
    #           for the hallucination detector when it processes event 7)
    # ═════════════════════════════════════════════════════════════════════════
    print("  [3/11]  Fetching company profile from Crunchbase")
    await asyncio.sleep(0.3)
    e3 = await span(
        "tool_call", "fetch_company_profile",
        inp={"company": "TechVenture AI", "fields": ["funding", "investors", "metrics", "team"]},
        out=COMPANY_PROFILE,            # ← ground truth anchor: $2.3M
        dur_ms=538,
        parent=e2,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 4 — REAL Claude Haiku: assess investment thesis
    # ═════════════════════════════════════════════════════════════════════════
    print("  [4/11]  Claude Haiku → assessing investment thesis")
    await asyncio.sleep(0.4)
    thesis_prompt = (
        "You are a VC analyst at a top-tier fund. Based on the following company profile, "
        "write a single concise sentence stating whether this company is worth advancing to "
        "full diligence. Be specific about the key signal.\n\n"
        f"Company data:\n{json.dumps(COMPANY_PROFILE, indent=2)}"
    )
    thesis_text, thesis_in, thesis_out = await call_claude(
        thesis_prompt,
        system="You are a senior VC analyst. Be concise and decisive.",
    )
    e4 = await span(
        "llm_call", "assess_investment_thesis",
        inp={"messages": [{"role": "user", "content": thesis_prompt[:350] + "..."}]},
        out={"thesis": thesis_text},
        model="claude-haiku-4-5-20251001",
        tin=thesis_in,
        tout=thesis_out,
        dur_ms=920,
        parent=e3,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 5 — Decision: analysis depth
    # ═════════════════════════════════════════════════════════════════════════
    print("  [5/11]  Decision → deep analysis selected")
    await asyncio.sleep(0.2)
    e5 = await span(
        "decision", "analysis_depth",
        inp={"options": ["quick_summary", "deep_analysis", "pass"], "thesis_signal": thesis_text[:120]},
        out={"selected": "deep_analysis", "rationale": "Sequoia signal + NPS 72 + 12% MoM growth"},
        dur_ms=42,
        parent=e4,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 6 — Memory write v1: save research context
    # ═════════════════════════════════════════════════════════════════════════
    print("  [6/11]  Memory write → saving research context (v1)")
    await asyncio.sleep(0.2)
    await write_memory(
        key="analyst_focus",
        content=(
            "Focus: TechVenture AI deep analysis for Q4 board deck. "
            "Sequoia-backed, enterprise AI automation. Strong thesis confirmed. "
            f"Analyst assessment: {thesis_text[:150]}"
        ),
        action="created",
        version=1,
    )
    e6 = await span(
        "memory_write", "save_research_context",
        inp={"key": "analyst_focus", "action": "created"},
        out={"stored": True, "version": 1},
        dur_ms=11,
        parent=e5,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 7 — MOCK LLM (labeled claude-sonnet-4-6): summarize financials
    #           Intentional hallucination: outputs $3.2M instead of $2.3M
    #           Detector pairs this with event 3 (last tool_call) → CRITICAL flag
    # ═════════════════════════════════════════════════════════════════════════
    print("  [7/11]  Claude Sonnet → summarizing financials")
    await asyncio.sleep(0.7)
    fin_summary, fin_in, fin_out = _mock_financial_summary()
    e7 = await span(
        "llm_call", "summarize_financials",
        inp={"messages": [{"role": "user", "content": f"Summarize financial profile: {json.dumps(COMPANY_PROFILE)[:300]}"}]},
        out={"summary": fin_summary},      # ← contains $3.2M (hallucinated)
        model="claude-sonnet-4-6",         # premium model label for cost breakdown
        tin=fin_in,
        tout=fin_out,
        dur_ms=1720,
        parent=e6,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 8 — Tool: fetch market sizing data
    #           (becomes new last_tool — isolates event 9 from the $2.3M conflict)
    # ═════════════════════════════════════════════════════════════════════════
    print("  [8/11]  Fetching market sizing data")
    await asyncio.sleep(0.3)
    e8 = await span(
        "tool_call", "fetch_market_data",
        inp={"segment": "enterprise AI automation", "year": 2025, "source": "pitchbook"},
        out=MARKET_DATA,
        dur_ms=319,
        parent=e7,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 9 — REAL OpenAI gpt-4o-mini: write investment memo
    # ═════════════════════════════════════════════════════════════════════════
    print("  [9/11]  GPT-4o-mini → writing investment memo")
    await asyncio.sleep(0.5)
    memo_prompt = (
        "Write a concise 3-sentence investment memo for a VC board deck. "
        "Focus on why this is (or isn't) a strong investment opportunity.\n\n"
        f"Company: {json.dumps(COMPANY_PROFILE)}\n"
        f"Market: {json.dumps(MARKET_DATA)}\n"
        f"Analyst thesis: {thesis_text[:200]}"
    )
    memo_text, memo_in, memo_out = await call_openai(memo_prompt)
    e9 = await span(
        "llm_call", "write_investment_memo",
        inp={"messages": [{"role": "user", "content": memo_prompt[:400] + "..."}]},
        out={"memo": memo_text},
        model="gpt-4o-mini",
        tin=memo_in,
        tout=memo_out,
        dur_ms=1310,
        parent=e8,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 10 — Memory write v2: update with final recommendation
    # ═════════════════════════════════════════════════════════════════════════
    print("  [10/11] Memory write → updating with recommendation (v2)")
    await asyncio.sleep(0.2)
    await write_memory(
        key="analyst_focus",
        content=(
            "Focus: TechVenture AI — STRONG BUY signal. Deep analysis complete. "
            f"Investment memo: {memo_text[:200]} "
            "Status: Advancing to partner meeting."
        ),
        action="updated",
        version=2,
    )
    e10 = await span(
        "memory_write", "save_recommendation",
        inp={"key": "analyst_focus", "action": "updated"},
        out={"stored": True, "version": 2, "updated_fields": ["recommendation", "status", "memo"]},
        dur_ms=9,
        parent=e9,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # EVENT 11 — Memory read: recall for final report
    # ═════════════════════════════════════════════════════════════════════════
    print("  [11/11] Memory read → recalling research context")
    await asyncio.sleep(0.2)
    e11 = await span(
        "memory_read", "recall_research_context",
        inp={"key": "analyst_focus"},
        out={
            "content": "Focus: TechVenture AI — STRONG BUY signal. Deep analysis complete.",
            "version": 2,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        },
        dur_ms=7,
        parent=e10,
    )

    # ── Flush and trigger hallucination detection ─────────────────────────────
    if client:
        await client._flush()
        await asyncio.sleep(0.8)

    print()
    print("  ──────────────────────────────────────────────────────────────")
    print(f"  Session complete  ·  ID: {session_id}")
    print("  ──────────────────────────────────────────────────────────────")
    print()

    # Auto-trigger hallucination check
    try:
        import aiohttp
        async with aiohttp.ClientSession() as sess:
            resp = await sess.post(
                f"{HTTP_URL}/api/v1/hallucinations/check",
                json={"session_id": session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            )
            result = await resp.json()
            summary = result.get("summary", {})
            total = summary.get("total", 0)
            if total:
                print(f"  Hallucination detector: {total} issue(s) found.")
                print(f"    Critical : {summary.get('critical', 0)}")
                print(f"    Warning  : {summary.get('warning',  0)}")
                print(f"    Info     : {summary.get('info',     0)}")
            else:
                print("  Hallucination detector: no issues auto-detected (run manually on the Hallucinations tab).")
    except Exception as exc:
        print(f"  [warn] Could not auto-run hallucination check: {exc}")

    print()
    print("  Dashboard walkthrough:")
    print("  ① Traces tab → click 'summarize_financials' node → see $3.2M in output")
    print("  ② Cost tab   → three models: claude-haiku / claude-sonnet / gpt-4o-mini")
    print("  ③ Hallucinations → Run Check → critical: $2.3M (tool) vs $3.2M (LLM)")
    print("  ④ Memory tab → analyst_focus key → v1 and v2 entries in timeline")
    print("  ⑤ Replay tab → Press Play → scrub through all 11 events")
    print()

    if client:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
