"""SDK type definitions."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class TraceEventData:
    """Represents a single trace event to be sent to AgentLens."""

    id: str
    session_id: str
    event_type: str
    event_name: str
    timestamp: str
    duration_ms: float = 0.0
    parent_event_id: Optional[str] = None
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    model: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: Optional[float] = None
    status: str = "success"
    error_message: Optional[str] = None
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None or k in {
            "session_id", "event_type", "event_name", "timestamp"
        }}
