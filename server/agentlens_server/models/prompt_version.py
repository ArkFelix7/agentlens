"""ORM model for prompt version history."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from agentlens_server.database import Base


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(String, primary_key=True)
    prompt_id = Column(String, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    label = Column(String, nullable=True)
    commit_message = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Aggregated metrics (updated lazily)
    total_uses = Column(Integer, nullable=False, default=0)
    avg_cost_usd = Column(Float, nullable=True)
    avg_latency_ms = Column(Float, nullable=True)
    hallucination_rate = Column(Float, nullable=True)

    prompt = relationship("Prompt", back_populates="versions")
