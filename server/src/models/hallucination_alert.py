"""ORM model for hallucination detection alerts."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base


class HallucinationAlert(Base):
    __tablename__ = "hallucination_alerts"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    trace_event_id = Column(String, ForeignKey("trace_events.id"), nullable=False)
    source_event_id = Column(String, ForeignKey("trace_events.id"), nullable=False)
    severity = Column(String, nullable=False)  # critical, warning, info
    description = Column(Text, nullable=False)
    expected_value = Column(Text, nullable=False)
    actual_value = Column(Text, nullable=False)
    similarity_score = Column(Float, nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("Session", back_populates="hallucination_alerts")
    trace_event = relationship("TraceEvent", foreign_keys=[trace_event_id])
    source_event = relationship("TraceEvent", foreign_keys=[source_event_id])
