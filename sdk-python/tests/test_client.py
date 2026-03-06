"""Tests for the AgentLens client transport layer."""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_buffer_and_flush():
    """Buffer events then flush via HTTP when WS not available."""
    from agentlens_sdk.client import AgentLensClient

    flushed = []

    async def mock_post(*args, **kwargs):
        flushed.append(kwargs.get("json", {}))

    client = AgentLensClient()
    client._session_id = "test-sess"
    client._connected = False

    with patch("aiohttp.ClientSession.post", new_callable=AsyncMock) as mock:
        for i in range(5):
            await client.send_event({"id": str(i), "event_name": f"event_{i}"})
        await client._flush()


@pytest.mark.asyncio
async def test_max_buffer_triggers_flush():
    """When buffer reaches max_buffer_size, flush is triggered automatically."""
    from agentlens_sdk.client import AgentLensClient

    flush_calls = []

    client = AgentLensClient()
    client._session_id = "test-sess"
    client._connected = False
    client._max_buffer_size = 3

    original_flush = client._flush

    async def mock_flush():
        flush_calls.append(True)
        client._buffer.clear()

    client._flush = mock_flush

    # Send exactly max_buffer_size events
    for i in range(3):
        await client.send_event({"id": str(i)})

    assert len(flush_calls) >= 1


@pytest.mark.asyncio
async def test_sensitive_data_redaction():
    """Ensure sensitive fields are redacted in event data."""
    from agentlens_sdk.trace import _redact

    data = {
        "query": "find me flights",
        "api_key": "sk-12345",
        "password": "hunter2",
        "model": "gpt-4o",
    }
    redacted = _redact(data)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["query"] == "find me flights"
    assert redacted["model"] == "gpt-4o"
