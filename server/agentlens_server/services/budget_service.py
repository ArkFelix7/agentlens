"""Budget guardrail service — monitors session costs and detects loops."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from sqlalchemy import select, func

from agentlens_server.models.budget_rule import BudgetRule
from agentlens_server.models.trace_event import TraceEvent
from agentlens_server.models.session import Session
from agentlens_server.schemas.budget import BudgetAlertOut

logger = logging.getLogger(__name__)


async def check_budget_rules(
    session_id: str,
    new_event: TraceEvent,
    db: DBSession,
) -> list[BudgetAlertOut]:
    """Check all active budget rules after a new trace event is ingested.

    Returns list of triggered BudgetAlertOut (may be empty).
    Fires webhooks in background for each triggered alert.
    """
    # Load active rules
    rules_result = await db.execute(
        select(BudgetRule).where(BudgetRule.is_active == True)  # noqa: E712
    )
    rules = rules_result.scalars().all()
    if not rules:
        return []

    # Load current session
    session_result = await db.execute(select(Session).where(Session.id == session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        return []

    alerts: list[BudgetAlertOut] = []
    now_str = datetime.now(timezone.utc).isoformat()

    for rule in rules:
        alert: Optional[BudgetAlertOut] = None

        if rule.rule_type == "session_total" and rule.threshold_usd is not None:
            current_cost = float(session.total_cost_usd or 0.0)
            if current_cost > rule.threshold_usd:
                alert = BudgetAlertOut(
                    rule_id=rule.id,
                    rule_name=rule.rule_name,
                    rule_type=rule.rule_type,
                    session_id=session_id,
                    alert_type="threshold_breached",
                    current_value=current_cost,
                    threshold=rule.threshold_usd,
                    message=(
                        f"Session cost ${current_cost:.4f} exceeded threshold "
                        f"${rule.threshold_usd:.4f}"
                    ),
                    triggered_at=now_str,
                )

        elif rule.rule_type == "per_model_call" and rule.threshold_usd is not None:
            event_cost = float(new_event.cost_usd or 0.0)
            if event_cost > rule.threshold_usd:
                alert = BudgetAlertOut(
                    rule_id=rule.id,
                    rule_name=rule.rule_name,
                    rule_type=rule.rule_type,
                    session_id=session_id,
                    alert_type="threshold_breached",
                    current_value=event_cost,
                    threshold=rule.threshold_usd,
                    message=(
                        f"Single call '{new_event.event_name}' cost ${event_cost:.4f} "
                        f"exceeded per-call threshold ${rule.threshold_usd:.4f}"
                    ),
                    triggered_at=now_str,
                )

        elif rule.rule_type == "daily_total" and rule.threshold_usd is not None:
            daily_cost = await _get_daily_cost(db)
            if daily_cost > rule.threshold_usd:
                alert = BudgetAlertOut(
                    rule_id=rule.id,
                    rule_name=rule.rule_name,
                    rule_type=rule.rule_type,
                    session_id=session_id,
                    alert_type="threshold_breached",
                    current_value=daily_cost,
                    threshold=rule.threshold_usd,
                    message=(
                        f"Daily spend ${daily_cost:.4f} exceeded threshold "
                        f"${rule.threshold_usd:.4f}"
                    ),
                    triggered_at=now_str,
                )

        elif rule.rule_type == "loop_detection":
            max_calls = rule.loop_max_calls or 5
            window_s = rule.loop_window_seconds or 60
            is_loop = await _detect_loop(
                session_id, new_event.event_name, window_s, max_calls, db
            )
            if is_loop:
                alert = BudgetAlertOut(
                    rule_id=rule.id,
                    rule_name=rule.rule_name,
                    rule_type=rule.rule_type,
                    session_id=session_id,
                    alert_type="loop_detected",
                    current_value=float(max_calls),
                    threshold=float(max_calls),
                    message=(
                        f"Loop detected: '{new_event.event_name}' called >{max_calls} "
                        f"times in {window_s}s"
                    ),
                    triggered_at=now_str,
                )

        if alert:
            alerts.append(alert)
            if rule.webhook_url:
                asyncio.create_task(
                    _fire_webhook(rule.webhook_url, alert)
                )

    return alerts


async def _get_daily_cost(db: DBSession) -> float:
    """Return total cost_usd across all events created today (UTC)."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.coalesce(func.sum(TraceEvent.cost_usd), 0.0)).where(
            TraceEvent.timestamp >= today_start,
        )
    )
    return float(result.scalar() or 0.0)


async def _detect_loop(
    session_id: str,
    event_name: str,
    window_s: int,
    max_calls: int,
    db: DBSession,
) -> bool:
    """Return True if event_name called > max_calls times in last window_s seconds."""
    window_start = datetime.now(timezone.utc) - timedelta(seconds=window_s)
    result = await db.execute(
        select(func.count(TraceEvent.id)).where(
            TraceEvent.session_id == session_id,
            TraceEvent.event_name == event_name,
            TraceEvent.timestamp >= window_start,
        )
    )
    count = result.scalar() or 0
    return count > max_calls


async def _fire_webhook(webhook_url: str, alert: BudgetAlertOut) -> None:
    """POST alert payload to webhook_url. Never raises."""
    try:
        import aiohttp
        payload = {
            "text": (
                f"AgentLens Budget Alert: {alert.rule_name}\n"
                f"Session: {alert.session_id}\n"
                f"Type: {alert.alert_type}\n"
                f"Current: {alert.current_value:.4f} / Threshold: {alert.threshold:.4f}\n"
                f"{alert.message}"
            ),
            "alert": alert.model_dump(mode="json"),
        }
        async with aiohttp.ClientSession() as http:
            async with http.post(
                webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status >= 400:
                    logger.warning("Webhook %s returned HTTP %d", webhook_url, resp.status)
    except Exception as exc:
        logger.warning("Budget webhook failed: %s", exc)
