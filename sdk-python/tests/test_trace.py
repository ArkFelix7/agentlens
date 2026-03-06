"""Tests for the @trace decorator."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_trace_decorator_captures_output():
    """@trace on async function captures input/output correctly."""
    import sys; import agentlens_sdk.trace; trace_mod = sys.modules['agentlens_sdk.trace']
    from agentlens_sdk.trace import trace

    captured_events = []

    class MockClient:
        _session_id = "test-session"

        async def send_event(self, event):
            captured_events.append(event)

        async def connect(self):
            pass

    with patch.object(trace_mod, "_global_client", MockClient()):
        with patch.object(trace_mod, "_global_session_id", "test-session"):
            @trace(name="test_func")
            async def my_func(x: int) -> str:
                return f"result_{x}"

            result = await my_func(42)

    assert result == "result_42"
    assert len(captured_events) == 1
    assert captured_events[0]["event_name"] == "test_func"


@pytest.mark.asyncio
async def test_trace_no_exception_when_server_down():
    """@trace must not raise when server is unavailable."""
    import sys; import agentlens_sdk.trace; trace_mod = sys.modules['agentlens_sdk.trace']
    from agentlens_sdk.trace import trace

    with patch.object(trace_mod, "_global_client", None):
        @trace
        async def risky_func():
            return "ok"

        # Must not raise even with no client
        result = await risky_func()
    assert result == "ok"


@pytest.mark.asyncio
async def test_trace_captures_error():
    """@trace records error status when function raises."""
    import sys; import agentlens_sdk.trace; trace_mod = sys.modules['agentlens_sdk.trace']
    from agentlens_sdk.trace import trace

    captured_events = []

    class MockClient:
        _session_id = "err-session"
        async def send_event(self, event):
            captured_events.append(event)

    with patch.object(trace_mod, "_global_client", MockClient()):
        with patch.object(trace_mod, "_global_session_id", "err-session"):
            @trace
            async def failing_func():
                raise ValueError("test error")

            with pytest.raises(ValueError):
                await failing_func()

    assert len(captured_events) == 1
    assert captured_events[0]["status"] == "error"
    assert "test error" in captured_events[0]["error_message"]
