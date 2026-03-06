"""ORM model for trace events."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from src.database import Base


class TraceEvent(Base):
    __tablename__ = "trace_events"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    parent_event_id = Column(String, ForeignKey("trace_events.id"), nullable=True)
    event_type = Column(String, nullable=False)
    # llm_call, tool_call, decision, memory_read, memory_write, user_input, error
    event_name = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    duration_ms = Column(Float, nullable=False, default=0.0)
    input_data = Column(Text, nullable=True)   # JSON string
    output_data = Column(Text, nullable=True)  # JSON string
    model = Column(String, nullable=True)
    tokens_input = Column(Integer, nullable=False, default=0)
    tokens_output = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    status = Column(String, nullable=False, default="success")  # success, error, pending
    error_message = Column(Text, nullable=True)
    metadata_ = Column("metadata", Text, nullable=True)  # JSON string

    # Relationships
    session = relationship("Session", back_populates="trace_events")
    # Self-referential parent/children relationship
    parent = relationship(
        "TraceEvent",
        foreign_keys=[parent_event_id],
        back_populates="children",
        uselist=False,
        remote_side="TraceEvent.id",
    )
    children = relationship(
        "TraceEvent",
        foreign_keys=[parent_event_id],
        back_populates="parent",
        uselist=True,
    )

    __table_args__ = (
        Index("ix_trace_events_session_id", "session_id"),
        Index("ix_trace_events_event_type", "event_type"),
        Index("ix_trace_events_timestamp", "timestamp"),
    )
