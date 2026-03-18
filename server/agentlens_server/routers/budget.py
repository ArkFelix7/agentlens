"""Budget guardrail CRUD endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agentlens_server.database import get_db
from agentlens_server.models.budget_rule import BudgetRule
from agentlens_server.schemas.budget import (
    BudgetRuleCreate, BudgetRuleUpdate, BudgetRuleResponse
)
from agentlens_server.utils import new_ulid

router = APIRouter(tags=["budget"])


@router.get("/budget/rules", response_model=List[BudgetRuleResponse])
async def list_rules(db: AsyncSession = Depends(get_db)) -> List[BudgetRuleResponse]:
    """List all budget guardrail rules."""
    result = await db.execute(select(BudgetRule).order_by(BudgetRule.created_at))
    rules = result.scalars().all()
    return [
        BudgetRuleResponse(
            id=r.id,
            rule_name=r.rule_name,
            rule_type=r.rule_type,
            threshold_usd=r.threshold_usd,
            loop_max_calls=r.loop_max_calls,
            loop_window_seconds=r.loop_window_seconds,
            webhook_url=r.webhook_url,
            is_active=r.is_active,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in rules
    ]


@router.post("/budget/rules", response_model=BudgetRuleResponse, status_code=201)
async def create_rule(
    body: BudgetRuleCreate, db: AsyncSession = Depends(get_db)
) -> BudgetRuleResponse:
    """Create a new budget guardrail rule."""
    rule = BudgetRule(
        id=new_ulid(),
        rule_name=body.rule_name,
        rule_type=body.rule_type,
        threshold_usd=body.threshold_usd,
        loop_max_calls=body.loop_max_calls,
        loop_window_seconds=body.loop_window_seconds,
        webhook_url=body.webhook_url,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return BudgetRuleResponse(
        id=rule.id,
        rule_name=rule.rule_name,
        rule_type=rule.rule_type,
        threshold_usd=rule.threshold_usd,
        loop_max_calls=rule.loop_max_calls,
        loop_window_seconds=rule.loop_window_seconds,
        webhook_url=rule.webhook_url,
        is_active=rule.is_active,
        created_at=rule.created_at.isoformat() if rule.created_at else "",
    )


@router.patch("/budget/rules/{rule_id}", response_model=BudgetRuleResponse)
async def update_rule(
    rule_id: str, body: BudgetRuleUpdate, db: AsyncSession = Depends(get_db)
) -> BudgetRuleResponse:
    """Update an existing budget guardrail rule."""
    result = await db.execute(select(BudgetRule).where(BudgetRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(rule, field, val)
    await db.commit()
    await db.refresh(rule)
    return BudgetRuleResponse(
        id=rule.id,
        rule_name=rule.rule_name,
        rule_type=rule.rule_type,
        threshold_usd=rule.threshold_usd,
        loop_max_calls=rule.loop_max_calls,
        loop_window_seconds=rule.loop_window_seconds,
        webhook_url=rule.webhook_url,
        is_active=rule.is_active,
        created_at=rule.created_at.isoformat() if rule.created_at else "",
    )


@router.delete("/budget/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """Delete a budget guardrail rule."""
    result = await db.execute(select(BudgetRule).where(BudgetRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()


@router.get("/budget/alerts/{session_id}")
async def get_budget_alerts(session_id: str, db: AsyncSession = Depends(get_db)) -> list:
    """Re-evaluate all active budget rules against a session and return triggered alerts."""
    from agentlens_server.models.session import Session as SessionModel
    from agentlens_server.models.trace_event import TraceEvent
    from agentlens_server.services.budget_service import _detect_loop
    from datetime import datetime, timezone
    from sqlalchemy import func

    session_result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    rules_result = await db.execute(select(BudgetRule).where(BudgetRule.is_active == True))  # noqa: E712
    rules = rules_result.scalars().all()

    alerts = []
    now_str = datetime.now(timezone.utc).isoformat()
    current_cost = float(session.total_cost_usd or 0.0)

    # Get most recent event name for loop check
    last_event_result = await db.execute(
        select(TraceEvent)
        .where(TraceEvent.session_id == session_id)
        .order_by(TraceEvent.timestamp.desc())
        .limit(1)
    )
    last_event = last_event_result.scalar_one_or_none()

    for rule in rules:
        if rule.rule_type == "session_total" and rule.threshold_usd is not None:
            if current_cost > rule.threshold_usd:
                alerts.append({
                    "rule_id": rule.id, "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type, "session_id": session_id,
                    "alert_type": "threshold_breached",
                    "current_value": current_cost, "threshold": rule.threshold_usd,
                    "message": f"Session cost ${current_cost:.4f} exceeded ${rule.threshold_usd:.4f}",
                    "triggered_at": now_str,
                })
        elif rule.rule_type == "loop_detection" and last_event:
            is_loop = await _detect_loop(
                session_id, last_event.event_name,
                rule.loop_window_seconds or 60, rule.loop_max_calls or 5, db
            )
            if is_loop:
                alerts.append({
                    "rule_id": rule.id, "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type, "session_id": session_id,
                    "alert_type": "loop_detected",
                    "current_value": float(rule.loop_max_calls or 5),
                    "threshold": float(rule.loop_max_calls or 5),
                    "message": f"Loop detected: '{last_event.event_name}' called repeatedly",
                    "triggered_at": now_str,
                })

    return alerts
