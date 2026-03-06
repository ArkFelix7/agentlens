"""ORM model for agent memory entries."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String, nullable=False, default="default")
    memory_key = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    action = Column(String, nullable=False)  # created, updated, accessed, deleted
    version = Column(Integer, nullable=False, default=1)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    influenced_events = Column(Text, nullable=True)  # JSON array of event IDs
    metadata_ = Column("metadata", Text, nullable=True)  # JSON string

    # Relationships
    session = relationship("Session", back_populates="memory_entries")
