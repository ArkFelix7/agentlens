"""ORM model for named prompt registry."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import relationship

from agentlens_server.database import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    current_version = Column(Integer, nullable=False, default=1)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    versions = relationship(
        "PromptVersion", back_populates="prompt", cascade="all, delete-orphan"
    )
