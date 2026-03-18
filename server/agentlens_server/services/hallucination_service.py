"""Hallucination detection engine.

Compares tool call outputs (ground truth) against subsequent LLM outputs.
Detects number transpositions, factual mismatches, and semantic drift.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from agentlens_server.utils import new_ulid

from agentlens_server.models.trace_event import TraceEvent
from agentlens_server.models.hallucination_alert import HallucinationAlert
from agentlens_server.schemas.hallucination import HallucinationAlertResponse, HallucinationSummary, HallucinationListResponse
from agentlens_server.utils.text_similarity import extract_numbers, normalize_number, semantic_similarity

logger = logging.getLogger(__name__)


def _extract_text(data_json: Optional[str]) -> str:
    """Extract plain text from a JSON field for comparison."""
    if not data_json:
        return ""
    try:
        data = json.loads(data_json)
        if isinstance(data, str):
            return data
        return json.dumps(data)
    except (json.JSONDecodeError, TypeError):
        return str(data_json)


def _detect_number_hallucinations(
    tool_text: str,
    llm_text: str,
    tool_event_id: str,
    llm_event_id: str,
    session_id: str,
) -> list[HallucinationAlert]:
    """Detect number transpositions between tool output and LLM output."""
    alerts = []
    tool_numbers = extract_numbers(tool_text)
    llm_numbers = extract_numbers(llm_text)

    # Check if any numbers in LLM output are NOT in tool output
    tool_normalized = set()
    for n in tool_numbers:
        val = normalize_number(n)
        if val is not None:
            tool_normalized.add(val)

    for n in llm_numbers:
        val = normalize_number(n)
        if val is not None and val not in tool_normalized and tool_normalized:
            # Check if it's a transposition of any tool number
            for tool_val in tool_normalized:
                # e.g., 2.3M vs 3.2M — digit transposition heuristic
                str_tool = str(tool_val).replace('.', '').replace('0', '')
                str_llm = str(val).replace('.', '').replace('0', '')
                if sorted(str_tool) == sorted(str_llm) and str_tool != str_llm:
                    severity = "critical"
                else:
                    severity = "warning"

                alerts.append(HallucinationAlert(
                    id=new_ulid(),
                    session_id=session_id,
                    trace_event_id=llm_event_id,
                    source_event_id=tool_event_id,
                    severity=severity,
                    description=f"Number mismatch: tool reported {tool_val}, LLM reported {val}",
                    expected_value=str(tool_val),
                    actual_value=str(val),
                    similarity_score=0.5 if severity == "warning" else 0.3,
                    detected_at=datetime.now(timezone.utc),
                ))
            break  # Only flag first mismatch per LLM call to avoid noise

    return alerts


async def run_hallucination_detection(
    db: AsyncSession,
    session_id: str,
) -> list[HallucinationAlertResponse]:
    """Run full hallucination detection for a session. Saves new alerts to DB."""
    result = await db.execute(
        select(TraceEvent)
        .where(TraceEvent.session_id == session_id)
        .order_by(TraceEvent.timestamp)
    )
    events = result.scalars().all()

    # Clear existing alerts for this session to avoid duplicates
    existing = await db.execute(
        select(HallucinationAlert).where(HallucinationAlert.session_id == session_id)
    )
    for alert in existing.scalars().all():
        await db.delete(alert)

    new_alerts = []
    # Pair each llm_call with the most recent preceding tool_call
    last_tool: Optional[TraceEvent] = None
    for event in events:
        if event.event_type == "tool_call" and event.status == "success":
            last_tool = event
        elif event.event_type == "llm_call" and last_tool is not None:
            tool_text = _extract_text(last_tool.output_data)
            llm_text = _extract_text(event.output_data)

            if tool_text and llm_text:
                # Number-based detection (fast, no model needed)
                number_alerts = _detect_number_hallucinations(
                    tool_text, llm_text, last_tool.id, event.id, session_id
                )
                new_alerts.extend(number_alerts)

                # Semantic similarity check — runs sentence-transformers in thread pool
                if not number_alerts:
                    score = await semantic_similarity(tool_text, llm_text)
                    if score < 0.40:
                        new_alerts.append(HallucinationAlert(
                            id=new_ulid(),
                            session_id=session_id,
                            trace_event_id=event.id,
                            source_event_id=last_tool.id,
                            severity="info",
                            description=f"Low similarity between tool output and LLM response (score: {score:.2f})",
                            expected_value=tool_text[:500],
                            actual_value=llm_text[:500],
                            similarity_score=score,
                            detected_at=datetime.now(timezone.utc),
                        ))

    for alert in new_alerts:
        db.add(alert)

    await db.commit()

    return [
        HallucinationAlertResponse(
            id=a.id,
            session_id=a.session_id,
            trace_event_id=a.trace_event_id,
            source_event_id=a.source_event_id,
            severity=a.severity,
            description=a.description,
            expected_value=a.expected_value,
            actual_value=a.actual_value,
            similarity_score=a.similarity_score,
            detected_at=a.detected_at,
        )
        for a in new_alerts
    ]


async def get_hallucinations(db: AsyncSession, session_id: str) -> HallucinationListResponse:
    """Get existing hallucination alerts for a session."""
    result = await db.execute(
        select(HallucinationAlert)
        .where(HallucinationAlert.session_id == session_id)
        .order_by(HallucinationAlert.detected_at)
    )
    alerts = result.scalars().all()

    alert_responses = [
        HallucinationAlertResponse(
            id=a.id,
            session_id=a.session_id,
            trace_event_id=a.trace_event_id,
            source_event_id=a.source_event_id,
            severity=a.severity,
            description=a.description,
            expected_value=a.expected_value,
            actual_value=a.actual_value,
            similarity_score=a.similarity_score,
            detected_at=a.detected_at,
        )
        for a in alerts
    ]

    counts = {"critical": 0, "warning": 0, "info": 0}
    for a in alerts:
        if a.severity in counts:
            counts[a.severity] += 1

    return HallucinationListResponse(
        alerts=alert_responses,
        summary=HallucinationSummary(
            total=len(alerts),
            critical=counts["critical"],
            warning=counts["warning"],
            info=counts["info"],
        ),
    )
