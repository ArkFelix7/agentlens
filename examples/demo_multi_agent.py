"""Multi-agent topology demo for AgentLens F9.

Simulates an orchestrator agent that spawns a researcher and a writer,
forming a parent-child session topology visible in the dashboard.

Run: python examples/demo_multi_agent.py
Requires: pip install agentlens-sdk
"""

import asyncio
import time
import random
from agentlens_sdk import init, trace

# ── Shared helpers ────────────────────────────────────────────────────────────

def _fake_latency(lo: float = 0.1, hi: float = 0.6) -> None:
    time.sleep(random.uniform(lo, hi))


# ── Orchestrator agent ────────────────────────────────────────────────────────

ORCHESTRATOR_SESSION = "demo-orchestrator-001"

def run_orchestrator() -> None:
    init(
        agent_name="orchestrator",
        session_id=ORCHESTRATOR_SESSION,
        agent_id="orch-001",
        agent_role="orchestrator",
    )
    print("[orchestrator] starting session:", ORCHESTRATOR_SESSION)
    _plan()
    _delegate()
    _synthesize()
    print("[orchestrator] done")


@trace(event_type="decision", name="plan_tasks")
def _plan() -> str:
    _fake_latency(0.2, 0.5)
    return "Planned 2 sub-tasks: research + write"


@trace(event_type="tool_call", name="delegate_to_workers")
def _delegate() -> str:
    _fake_latency(0.1, 0.3)
    return "Dispatched researcher and writer"


@trace(event_type="decision", name="synthesize_results")
def _synthesize() -> str:
    _fake_latency(0.3, 0.6)
    return "Final report: research confirmed, article drafted"


# ── Researcher sub-agent ──────────────────────────────────────────────────────

RESEARCHER_SESSION = "demo-researcher-001"

def run_researcher() -> None:
    init(
        agent_name="researcher",
        session_id=RESEARCHER_SESSION,
        agent_id="rsrch-001",
        agent_role="researcher",
        parent_session_id=ORCHESTRATOR_SESSION,   # links to parent in topology
    )
    print("[researcher] starting session:", RESEARCHER_SESSION)
    _search_web()
    _analyze_sources()
    _compile_notes()
    print("[researcher] done")


@trace(event_type="tool_call", name="search_web")
def _search_web() -> dict:
    _fake_latency(0.3, 0.7)
    return {
        "query": "latest LLM observability tools 2025",
        "results": [
            "Langfuse: open-source, 21K stars",
            "Arize Phoenix: 8K stars, strong evals",
            "AgentLens: real-time, air-gap, ULID-based",
        ],
    }


@trace(event_type="decision", name="analyze_sources")
def _analyze_sources() -> str:
    _fake_latency(0.2, 0.4)
    return "AgentLens differentiates on: air-gap, real-time topology, budget guardrails"


@trace(event_type="llm_call", name="compile_research_notes")
def _compile_notes() -> str:
    _fake_latency(0.4, 0.8)
    return (
        "Research complete. Key finding: no other tool combines "
        "air-gap privacy + multi-agent topology + budget guardrails in one package."
    )


# ── Writer sub-agent ──────────────────────────────────────────────────────────

WRITER_SESSION = "demo-writer-001"

def run_writer() -> None:
    init(
        agent_name="writer",
        session_id=WRITER_SESSION,
        agent_id="wrtr-001",
        agent_role="writer",
        parent_session_id=ORCHESTRATOR_SESSION,   # links to parent in topology
    )
    print("[writer] starting session:", WRITER_SESSION)
    _draft_article()
    _revise_draft()
    _finalize()
    print("[writer] done")


@trace(event_type="llm_call", name="draft_article")
def _draft_article() -> str:
    _fake_latency(0.5, 1.0)
    return (
        "## Why AgentLens is the Developer's Choice\n\n"
        "In a world of black-box AI agents, observability is your superpower. "
        "AgentLens gives you real-time traces, budget guardrails, and hallucination detection "
        "— all without sending your data anywhere."
    )


@trace(event_type="decision", name="revise_draft")
def _revise_draft() -> str:
    _fake_latency(0.2, 0.5)
    return "Revised: added code snippet, shortened intro"


@trace(event_type="llm_call", name="finalize_article")
def _finalize() -> str:
    _fake_latency(0.3, 0.6)
    return "Article finalized. Word count: 320. Ready for publish."


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("  AgentLens Multi-Agent Demo")
    print("  Topology: orchestrator → researcher + writer")
    print()

    # Run orchestrator first to create the parent session
    run_orchestrator()
    time.sleep(0.5)   # let WS flush

    # Run sub-agents concurrently (simulated sequentially for simplicity)
    run_researcher()
    time.sleep(0.3)
    run_writer()
    time.sleep(0.5)   # final flush

    print()
    print("  Done! Open the dashboard → Topology page to see the agent graph.")
    print("  Sessions:")
    print(f"    Orchestrator: {ORCHESTRATOR_SESSION}")
    print(f"    Researcher:   {RESEARCHER_SESSION}")
    print(f"    Writer:       {WRITER_SESSION}")
    print()


if __name__ == "__main__":
    main()
