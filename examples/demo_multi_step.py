"""demo_multi_step.py — Multi-step research agent demo for AgentLens.

This is the showcase demo. It simulates a research agent that:
  1. Receives a user query
  2. Searches the web (simulated)
  3. Reads search results (simulated)
  4. Summarizes findings (simulated LLM — uses real OpenAI if OPENAI_API_KEY set)
  5. Stores a memory about the user's interest
  6. Generates a final report (simulated LLM)

Intentional hallucination: the LLM changes "$2.3M" → "$3.2M" so the hallucination
detector has something to find.

Works entirely without API keys using realistic mock responses.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

# Add sdk-python to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk-python', 'src'))

try:
    from agentlens import init, trace
    from agentlens.client import AgentLensClient
    from agentlens.trace import SpanContext, get_client, get_session_id
    from ulid import ULID
    SDK_AVAILABLE = True
except ImportError:
    print("Warning: agentlens SDK not installed. Run: pip install -e sdk-python/")
    SDK_AVAILABLE = False

# Server config
WS_URL = os.getenv("AGENTLENS_WS_URL", "ws://localhost:8766/ws")
HTTP_URL = os.getenv("AGENTLENS_HTTP_URL", "http://localhost:8766")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ===== SIMULATED TOOL OUTPUTS (ground truth) =====

SIMULATED_SEARCH_RESULTS = {
    "query": "AI startup funding 2025",
    "results": [
        {
            "title": "TechVenture AI raises $2.3M in seed round",
            "snippet": "TechVenture AI announced a $2.3M seed funding round led by Sequoia Capital. "
                       "The company has 1,450 customers and 12% YoY growth.",
            "url": "https://techcrunch.example.com/techventure-ai-funding",
        },
        {
            "title": "AI sector sees record investment in Q1 2025",
            "snippet": "Q1 2025 saw $847M in AI investments across 203 deals.",
            "url": "https://venturebeat.example.com/ai-investment-2025",
        },
    ],
}

SIMULATED_DEEP_SEARCH = {
    "company": "TechVenture AI",
    "funding": "$2.3M",
    "investors": ["Sequoia Capital", "Y Combinator"],
    "customers": 1450,
    "growth_yoy": "12%",
    "founded": 2023,
    "focus": "enterprise AI automation",
}


# ===== MOCK LLM RESPONSES =====

def mock_summarize(tool_output: str) -> tuple[str, int, int]:
    """Mock LLM summary — INTENTIONALLY transposes $2.3M → $3.2M (hallucination)."""
    # Note: This is the intentional hallucination for the detector to find
    summary = (
        "Based on the research, TechVenture AI has raised $3.2M in their seed round "
        "(led by Sequoia Capital), with 1,450 customers and 12% YoY growth. "
        "The company was founded in 2023 and focuses on enterprise AI automation."
    )
    return summary, 450, 85


def mock_final_report(summary: str, memory: str) -> tuple[str, int, int]:
    """Mock LLM final report."""
    report = f"""# Research Report: TechVenture AI Funding

## Executive Summary
{summary}

## User Context
{memory}

## Investment Analysis
TechVenture AI demonstrates strong early traction with their seed funding round.
The backing from Sequoia Capital signals high confidence in their enterprise AI automation platform.

## Recommendation
This company warrants continued monitoring given their growth metrics.
"""
    return report, 600, 200


async def run_agent():
    """Run the multi-step research agent demo."""

    print("\n" + "="*60)
    print("  AgentLens Multi-Step Research Agent Demo")
    print("="*60)
    print(f"\n  Dashboard: http://localhost:5173")
    print(f"  Server:    {HTTP_URL}")
    print("\n  Starting agent run...\n")

    if not SDK_AVAILABLE:
        print("Error: agentlens SDK not available. Please install it first.")
        return

    # Initialize SDK
    session_id = str(ULID())
    init(server_url=WS_URL, http_url=HTTP_URL, agent_name="research-agent", session_id=session_id)
    client = get_client()

    # Small delay to allow WS connection
    await asyncio.sleep(0.5)

    # Announce session start
    if client:
        await client.send_message({
            "type": "session_start",
            "data": {
                "session_id": session_id,
                "agent_name": "research-agent",
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        })

    async def send_event(event_type, event_name, input_data=None, output_data=None,
                         model=None, tokens_in=0, tokens_out=0, duration_ms=0,
                         status="success", error=None, parent_id=None):
        """Helper to send a trace event."""
        span = SpanContext(
            event_type=event_type,
            event_name=event_name,
            session_id=session_id,
            parent_event_id=parent_id,
            client=client,
        )
        if input_data:
            span.set_input(input_data)
        if output_data:
            span.set_output(output_data)
        if model:
            span.set_model(model)
        if tokens_in or tokens_out:
            span.set_tokens(tokens_in, tokens_out)
        if error:
            span.set_error(error)

        # Override timing
        span._start_time = time.perf_counter() - duration_ms / 1000
        span.end()
        await asyncio.sleep(0.2)  # small delay for visual effect in dashboard
        return span.id

    # ===== STEP 1: USER INPUT =====
    print("  [1/8] User input received...")
    user_event_id = await send_event(
        event_type="user_input",
        event_name="user_query",
        input_data={"query": "Research AI startup funding trends in 2025"},
        duration_ms=10,
    )

    # ===== STEP 2: WEB SEARCH =====
    print("  [2/8] Searching the web...")
    await asyncio.sleep(0.3)
    search_event_id = await send_event(
        event_type="tool_call",
        event_name="web_search",
        input_data={"query": "AI startup funding 2025", "max_results": 5},
        output_data=SIMULATED_SEARCH_RESULTS,
        duration_ms=342,
        parent_id=user_event_id,
    )

    # ===== STEP 3: READ SEARCH RESULTS =====
    print("  [3/8] Reading search results...")
    await asyncio.sleep(0.2)
    read_event_id = await send_event(
        event_type="tool_call",
        event_name="read_webpage",
        input_data={"url": "https://techcrunch.example.com/techventure-ai-funding"},
        output_data=SIMULATED_DEEP_SEARCH,
        duration_ms=218,
        parent_id=search_event_id,
    )

    # ===== STEP 4: DECISION — WHICH COMPANY TO FOCUS ON =====
    print("  [4/8] Deciding which company to focus on...")
    await asyncio.sleep(0.1)
    decision_id = await send_event(
        event_type="decision",
        event_name="select_primary_subject",
        input_data={"candidates": ["TechVenture AI", "OpenMind Systems", "DataPulse"]},
        output_data={"selected": "TechVenture AI", "reason": "Most funding data available"},
        duration_ms=45,
        parent_id=read_event_id,
    )

    # ===== STEP 5: MEMORY WRITE =====
    print("  [5/8] Storing user interest in memory...")
    await asyncio.sleep(0.2)
    if client:
        memory_data = {
            "session_id": session_id,
            "memory_key": "user_research_interest",
            "content": "User is researching AI startup funding trends. Interested in seed-stage companies.",
            "action": "created",
        }
        await client.send_message({"type": "memory_update", "data": memory_data})
        # Also send via HTTP for persistence
        try:
            import aiohttp
            async with aiohttp.ClientSession() as sess:
                await sess.post(f"{HTTP_URL}/api/v1/memory", json=memory_data, timeout=aiohttp.ClientTimeout(total=3))
        except Exception:
            pass

    memory_event_id = await send_event(
        event_type="memory_write",
        event_name="store_user_interest",
        input_data={"key": "user_research_interest"},
        output_data={"stored": True, "version": 1},
        duration_ms=12,
        parent_id=decision_id,
    )

    # ===== STEP 6: LLM SUMMARIZE (with intentional hallucination) =====
    print("  [6/8] Summarizing findings with LLM...")
    await asyncio.sleep(0.5)

    tool_output_text = json.dumps(SIMULATED_DEEP_SEARCH)

    if OPENAI_API_KEY:
        try:
            import openai
            oa_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
            response = await oa_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": f"Summarize this data: {tool_output_text}"}
                ],
            )
            summary_text = response.choices[0].message.content
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens
            model_name = "gpt-4o-mini"
        except Exception as e:
            print(f"  OpenAI failed ({e}), using mock response")
            summary_text, tokens_in, tokens_out = mock_summarize(tool_output_text)
            model_name = "gpt-4o-mini (mock)"
    else:
        summary_text, tokens_in, tokens_out = mock_summarize(tool_output_text)
        model_name = "gpt-4o-mini (mock)"

    summarize_id = await send_event(
        event_type="llm_call",
        event_name="summarize_results",
        input_data={"messages": [{"role": "user", "content": f"Summarize: {tool_output_text[:200]}..."}]},
        output_data={"summary": summary_text},
        model=model_name,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        duration_ms=1240,
        parent_id=memory_event_id,
    )

    # ===== STEP 7: MEMORY READ =====
    print("  [7/8] Recalling user context from memory...")
    await asyncio.sleep(0.2)
    if client:
        await client.send_message({
            "type": "memory_update",
            "data": {
                "session_id": session_id,
                "memory_key": "user_research_interest",
                "content": "User is researching AI startup funding trends. Interested in seed-stage companies. "
                           "Focus session: TechVenture AI analysis.",
                "action": "accessed",
            },
        })

    recall_id = await send_event(
        event_type="memory_read",
        event_name="recall_user_context",
        input_data={"key": "user_research_interest"},
        output_data={"content": "User is researching AI startup funding trends.", "version": 1},
        duration_ms=8,
        parent_id=summarize_id,
    )

    # ===== STEP 8: LLM GENERATE FINAL REPORT =====
    print("  [8/8] Generating final report with LLM...")
    await asyncio.sleep(0.5)

    final_report, report_tokens_in, report_tokens_out = mock_final_report(
        summary_text,
        "User is researching AI startup funding trends."
    )

    report_id = await send_event(
        event_type="llm_call",
        event_name="generate_final_report",
        input_data={"summary": summary_text[:200], "user_context": "AI funding research"},
        output_data={"report": final_report[:500]},
        model="gpt-4o (mock)",
        tokens_in=report_tokens_in,
        tokens_out=report_tokens_out,
        duration_ms=2100,
        parent_id=recall_id,
    )

    # Flush all events
    if client:
        await client._flush()
        await asyncio.sleep(0.5)

    print("\n" + "="*60)
    print("  Agent run complete!")
    print("="*60)
    print(f"\n  Session ID: {session_id}")
    print(f"  Events sent: 8")
    print(f"\n  Open the dashboard to see your traces:")
    print(f"  http://localhost:5173")
    print(f"\n  Note: Check the Hallucinations tab — the LLM transposed")
    print(f"  '$2.3M' → '$3.2M' (intentional demo hallucination)")
    print(f"\n  Also check the Memory tab for stored user preferences.")
    print()

    # Trigger hallucination detection via HTTP
    try:
        import aiohttp
        async with aiohttp.ClientSession() as sess:
            resp = await sess.post(
                f"{HTTP_URL}/api/v1/hallucinations/check",
                json={"session_id": session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            )
            data = await resp.json()
            if data.get("summary", {}).get("total", 0) > 0:
                print(f"  Hallucination detector found {data['summary']['total']} potential issues!")
                print(f"    Critical: {data['summary']['critical']}")
                print(f"    Warning:  {data['summary']['warning']}")
    except Exception as e:
        print(f"  Note: Could not run hallucination check automatically: {e}")

    print()

    if client:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_agent())
