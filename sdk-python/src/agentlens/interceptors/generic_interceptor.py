"""Generic interceptor for tracing any callable."""

import asyncio
import functools
import logging
from typing import Any, Callable

from agentlens.trace import get_client, get_session_id, SpanContext
from ulid import ULID

logger = logging.getLogger(__name__)


def trace_callable(
    fn: Callable,
    name: str | None = None,
    event_type: str = "tool_call",
) -> Callable:
    """Wrap any callable to trace its execution."""
    event_name = name or fn.__name__

    @functools.wraps(fn)
    async def async_wrapper(*args, **kwargs):
        client = get_client()
        session_id = get_session_id() or str(ULID())
        span = SpanContext(
            event_type=event_type,
            event_name=event_name,
            session_id=session_id,
            client=client,
        )
        try:
            result = await fn(*args, **kwargs)
            span.set_output(result if not isinstance(result, bytes) else str(result))
            return result
        except Exception as e:
            span.set_error(str(e))
            raise
        finally:
            span.end()

    @functools.wraps(fn)
    def sync_wrapper(*args, **kwargs):
        client = get_client()
        session_id = get_session_id() or str(ULID())
        span = SpanContext(
            event_type=event_type,
            event_name=event_name,
            session_id=session_id,
            client=client,
        )
        try:
            result = fn(*args, **kwargs)
            span.set_output(result if not isinstance(result, bytes) else str(result))
            return result
        except Exception as e:
            span.set_error(str(e))
            raise
        finally:
            span.end()

    if asyncio.iscoroutinefunction(fn):
        return async_wrapper
    return sync_wrapper
