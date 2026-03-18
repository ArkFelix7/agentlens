"""Model comparison service — re-runs a session's LLM calls against a different model."""

import json
import logging
import time
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from sqlalchemy import select

from agentlens_server.models.trace_event import TraceEvent
from agentlens_server.models.session import Session

logger = logging.getLogger(__name__)


def _extract_output_text(output_data: Optional[str]) -> str:
    """Extract text content from a trace event's output JSON."""
    if not output_data:
        return ""
    try:
        out = json.loads(output_data)
        # Handle various output shapes
        if isinstance(out, str):
            return out
        if isinstance(out, dict):
            for key in ("content", "text", "output", "result", "message", "answer"):
                if key in out:
                    val = out[key]
                    if isinstance(val, str):
                        return val
                    if isinstance(val, list) and val:
                        item = val[0]
                        if isinstance(item, dict):
                            return item.get("text", str(item))
                        return str(item)
            return json.dumps(out)[:500]
    except Exception:
        return str(output_data)[:500]
    return ""


def _extract_messages(input_data: Optional[str]) -> list:
    """Extract messages list from a trace event's input JSON."""
    if not input_data:
        return [{"role": "user", "content": "Hello"}]
    try:
        inp = json.loads(input_data)
        if isinstance(inp, dict):
            # Look for messages array
            for key in ("messages", "inputs", "prompt"):
                if key in inp and isinstance(inp[key], list):
                    return inp[key]
            # Maybe it IS the messages format
            if "role" in inp:
                return [inp]
            # Try to build a user message from content
            content = inp.get("content") or inp.get("text") or json.dumps(inp)[:500]
            return [{"role": "user", "content": str(content)}]
        elif isinstance(inp, list):
            return inp
        elif isinstance(inp, str):
            return [{"role": "user", "content": inp}]
    except Exception:
        pass
    return [{"role": "user", "content": str(input_data)[:500]}]


def _keyword_diff_score(a: str, b: str) -> float:
    """Simple keyword-based output difference score (0=identical, 1=completely different)."""
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a and not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    jaccard = intersection / union if union else 0.0
    return round(1.0 - jaccard, 3)


async def _call_openai_compat(
    base_url: str,
    api_key: str,
    model: str,
    messages: list,
) -> tuple[str, float, float]:
    """Call an OpenAI-compatible API. Returns (output_text, cost_usd, latency_ms)."""
    import aiohttp

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages, "max_tokens": 1024}

    start = time.monotonic()
    try:
        async with aiohttp.ClientSession() as http:
            async with http.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                latency_ms = (time.monotonic() - start) * 1000
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning("Compare API error HTTP %d: %s", resp.status, text[:200])
                    return f"[API error {resp.status}]", 0.0, latency_ms

                data = await resp.json()
                content = ""
                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    content = choice.get("message", {}).get("content", "") or \
                              choice.get("text", "")

                # Estimate cost from usage (rough)
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                # Generic pricing estimate (will be inaccurate — display as estimate)
                cost = (input_tokens * 0.000001) + (output_tokens * 0.000002)
                return content, cost, latency_ms
    except Exception as exc:
        latency_ms = (time.monotonic() - start) * 1000
        logger.warning("Compare call failed: %s", exc)
        return f"[Call failed: {exc}]", 0.0, latency_ms


_PROVIDER_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",  # anthropic uses OpenAI compat via beta header
    "google": "https://generativelanguage.googleapis.com/v1beta/openai",
}


async def run_comparison(
    session_id: str,
    target_model: str,
    provider: str,
    api_key: str,
    max_steps: int,
    db: DBSession,
) -> Optional[dict]:
    """
    Re-run a session's LLM calls against a different model.
    Returns comparison result dict or None if session not found.
    The api_key is NEVER stored or logged.
    """
    # Load session
    sess_result = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_result.scalar_one_or_none()
    if not session:
        return None

    # Load LLM call events
    events_result = await db.execute(
        select(TraceEvent)
        .where(
            TraceEvent.session_id == session_id,
            TraceEvent.event_type == "llm_call",
        )
        .order_by(TraceEvent.timestamp)
        .limit(max_steps)
    )
    llm_events = events_result.scalars().all()
    if not llm_events:
        return None

    base_url = _PROVIDER_BASE_URLS.get(provider, _PROVIDER_BASE_URLS["openai"])

    steps = []
    total_comparison_cost = 0.0
    total_comparison_hallucinations = 0

    for event in llm_events:
        messages = _extract_messages(event.input_data)
        original_output = _extract_output_text(event.output_data)

        comparison_output, comp_cost, comp_latency = await _call_openai_compat(
            base_url=base_url,
            api_key=api_key,  # never stored
            model=target_model,
            messages=messages,
        )

        total_comparison_cost += comp_cost
        diff_score = _keyword_diff_score(original_output, comparison_output)

        # Hallucination scoring for comparison output is not available
        # without a reference source event — defaulting to 0
        comp_hallucinations = 0

        if comp_hallucinations > 0:
            total_comparison_hallucinations += comp_hallucinations

        steps.append({
            "event_id": event.id,
            "event_name": event.event_name,
            "original_model": event.model or "unknown",
            "original_output": original_output[:1000],
            "original_cost_usd": float(event.cost_usd or 0),
            "original_latency_ms": float(event.duration_ms or 0),
            "original_hallucinations": 0,
            "comparison_model": target_model,
            "comparison_output": comparison_output[:1000],
            "comparison_cost_usd": comp_cost,
            "comparison_latency_ms": comp_latency,
            "comparison_hallucinations": comp_hallucinations,
            "output_diff_score": diff_score,
        })

    total_original_cost = float(session.total_cost_usd or 0)
    cost_delta_pct = (
        ((total_comparison_cost - total_original_cost) / total_original_cost * 100)
        if total_original_cost > 0 else 0.0
    )

    # Build recommendation
    recommendations = []
    if cost_delta_pct < -20:
        recommendations.append(f"Switch to {target_model} for {abs(cost_delta_pct):.0f}% cost savings")
    elif cost_delta_pct > 20:
        recommendations.append(f"{target_model} costs {cost_delta_pct:.0f}% more than original")

    original_models = {e.model for e in llm_events if e.model}
    original_hallucinations = sum(s["original_hallucinations"] for s in steps)

    if total_comparison_hallucinations < original_hallucinations:
        recommendations.append(f"fewer hallucinations ({total_comparison_hallucinations} vs {original_hallucinations})")
    elif total_comparison_hallucinations > original_hallucinations:
        recommendations.append(f"more hallucinations ({total_comparison_hallucinations} vs {original_hallucinations})")

    recommendation = (" + ".join(recommendations) + ".").capitalize() if recommendations else \
        f"{target_model} shows similar performance to the original."

    return {
        "session_id": session_id,
        "original_model": ", ".join(original_models) or "unknown",
        "comparison_model": target_model,
        "total_original_cost_usd": total_original_cost,
        "total_comparison_cost_usd": total_comparison_cost,
        "cost_delta_pct": round(cost_delta_pct, 2),
        "original_hallucination_count": original_hallucinations,
        "comparison_hallucination_count": total_comparison_hallucinations,
        "steps": steps,
        "recommendation": recommendation,
    }
