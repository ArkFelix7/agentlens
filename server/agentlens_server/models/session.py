"""ORM model for agent sessions."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from sqlalchemy.orm import relationship

from agentlens_server.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    agent_name = Column(String, nullable=False, default="unnamed")
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)
    total_events = Column(Integer, nullable=False, default=0)
    total_cost_usd = Column(Float, nullable=False, default=0.0)
    total_tokens_input = Column(Integer, nullable=False, default=0)
    total_tokens_output = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="active")  # active, completed, error
    metadata_ = Column("metadata", Text, nullable=True)

    # Relationships
    trace_events = relationship("TraceEvent", back_populates="session", cascade="all, delete-orphan")
    memory_entries = relationship("MemoryEntry", back_populates="session", cascade="all, delete-orphan")
    hallucination_alerts = relationship("HallucinationAlert", back_populates="session", cascade="all, delete-orphan")
