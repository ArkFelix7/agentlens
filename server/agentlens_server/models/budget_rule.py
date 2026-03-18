"""ORM model for budget guardrail rules."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text

from agentlens_server.database import Base


class BudgetRule(Base):
    __tablename__ = "budget_rules"

    id = Column(String, primary_key=True)
    rule_name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)
    # Types: "session_total", "per_model_call", "daily_total", "loop_detection"

    threshold_usd = Column(Float, nullable=True)
    loop_max_calls = Column(Integer, nullable=True)
    loop_window_seconds = Column(Integer, nullable=True, default=60)

    webhook_url = Column(Text, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
