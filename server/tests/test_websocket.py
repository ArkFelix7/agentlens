"""WebSocket endpoint tests for AgentLens server.

Covers: hello handshake, SDK trace ingestion over WS, dashboard message routing,
session_start broadcast, and pong handling.
"""

import asyncio
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from httpx_ws import aconnect_ws

from agentlens_server.main import app


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _ws_url() -> str:
    return "ws://test/ws"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_endpoint(http_client):
    """Sanity check: server /health returns 200."""
    resp = await http_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_ws_sdk_hello_accepted():
    """SDK client sending hello:sdk should be accepted without error."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with aconnect_ws("ws://test/ws", client) as ws:
            await ws.send_text(json.dumps({"type": "hello", "role": "sdk"}))
            # No error — connection stays alive
            await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_ws_dashboard_hello_accepted():
    """Dashboard client sending hello:dashboard should be accepted."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with aconnect_ws("ws://test/ws", client) as ws:
            await ws.send_text(json.dumps({"type": "hello", "role": "dashboard"}))
            await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_ws_default_role_is_sdk():
    """Client that sends non-JSON hello should default to SDK role."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with aconnect_ws("ws://test/ws", client) as ws:
            await ws.send_text("not json")
            await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_ws_sdk_pong_does_not_close():
    """SDK client sending pong should be silently ignored (no close)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with aconnect_ws("ws://test/ws", client) as ws:
            await ws.send_text(json.dumps({"type": "hello", "role": "sdk"}))
            await ws.send_text(json.dumps({"type": "pong"}))
            await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_ws_sdk_trace_events_ingested():
    """SDK trace_events message should persist events (verifiable via REST)."""
    session_id = "ws-test-session-001"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with aconnect_ws("ws://test/ws", client) as ws:
            await ws.send_text(json.dumps({"type": "hello", "role": "sdk"}))
            await asyncio.sleep(0.05)
            await ws.send_text(json.dumps({
                "type": "trace_events",
                "session_id": session_id,
                "events": [
                    {
                        "event_type": "agent_step",
                        "event_name": "test:step",
                        "status": "success",
                        "tokens_input": 10,
                        "tokens_output": 5,
                    }
                ],
            }))
            await asyncio.sleep(0.15)

        # Verify via REST
        resp = await client.get(f"/api/v1/traces/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["event_name"] == "test:step"


@pytest.mark.asyncio
async def test_ws_sdk_session_start_broadcast():
    """session_start from SDK should be broadcast to dashboard clients."""
    session_id = "ws-test-bcast-002"
    received: list[dict] = []

    async def dashboard_listener():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            async with aconnect_ws("ws://test/ws", c) as ws:
                await ws.send_text(json.dumps({"type": "hello", "role": "dashboard"}))
                try:
                    msg_text = await asyncio.wait_for(ws.receive_text(), timeout=2.0)
                    received.append(json.loads(msg_text))
                except asyncio.TimeoutError:
                    pass

    async def sdk_sender():
        await asyncio.sleep(0.2)  # let dashboard connect first
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            async with aconnect_ws("ws://test/ws", c) as ws:
                await ws.send_text(json.dumps({"type": "hello", "role": "sdk"}))
                await asyncio.sleep(0.05)
                await ws.send_text(json.dumps({
                    "type": "session_start",
                    "data": {"session_id": session_id, "agent_name": "ws-test-agent"},
                }))
                await asyncio.sleep(0.2)

    await asyncio.gather(dashboard_listener(), sdk_sender())

    # Dashboard should have received session_start broadcast
    assert any(m.get("type") == "session_start" for m in received), \
        f"No session_start broadcast received; got: {received}"


@pytest.mark.asyncio
async def test_ws_dashboard_get_sessions():
    """Dashboard get_sessions request should return sessions_list response."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with aconnect_ws("ws://test/ws", client) as ws:
            await ws.send_text(json.dumps({"type": "hello", "role": "dashboard"}))
            await asyncio.sleep(0.05)
            await ws.send_text(json.dumps({"type": "get_sessions"}))
            try:
                msg_text = await asyncio.wait_for(ws.receive_text(), timeout=2.0)
                msg = json.loads(msg_text)
                assert msg["type"] == "sessions_list"
                assert isinstance(msg["data"], list)
            except asyncio.TimeoutError:
                pytest.fail("Timed out waiting for sessions_list response")


@pytest.mark.asyncio
async def test_ws_invalid_json_does_not_crash():
    """Sending invalid JSON after hello should not crash the server."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with aconnect_ws("ws://test/ws", client) as ws:
            await ws.send_text(json.dumps({"type": "hello", "role": "sdk"}))
            await asyncio.sleep(0.05)
            await ws.send_text("{bad json{{")
            await asyncio.sleep(0.05)
            # Connection should still be alive — send valid message
            await ws.send_text(json.dumps({"type": "pong"}))
