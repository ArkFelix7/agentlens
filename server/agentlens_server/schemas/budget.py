"""Pydantic schemas for budget guardrail API."""

from typing import Optional, Literal
from pydantic import BaseModel


class BudgetRuleCreate(BaseModel):
    rule_name: str
    rule_type: Literal["session_total", "per_model_call", "daily_total", "loop_detection"]
    threshold_usd: Optional[float] = None
    loop_max_calls: Optional[int] = None
    loop_window_seconds: int = 60
    webhook_url: Optional[str] = None


class BudgetRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    threshold_usd: Optional[float] = None
    loop_max_calls: Optional[int] = None
    loop_window_seconds: Optional[int] = None
    webhook_url: Optional[str] = None
    is_active: Optional[bool] = None


class BudgetRuleResponse(BaseModel):
    id: str
    rule_name: str
    rule_type: str
    threshold_usd: Optional[float]
    loop_max_calls: Optional[int]
    loop_window_seconds: Optional[int]
    webhook_url: Optional[str]
    is_active: bool
    created_at: str


class BudgetAlertOut(BaseModel):
    rule_id: str
    rule_name: str
    rule_type: str
    session_id: str
    alert_type: str
    current_value: float
    threshold: float
    message: str
    triggered_at: str
