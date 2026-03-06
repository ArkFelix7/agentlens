"""Tests for trace event ingestion."""

import pytest
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_ingest_events(client):
    """Ingest 10 trace events and verify all are stored."""
    session_id = "01JKTEST00000000000000001"
    events = [
        {
            "session_id": session_id,
            "event_type": "llm_call",
            "event_name": f"call_{i}",
            "model": "gpt-4o-mini",
            "tokens_input": 100,
            "tokens_output": 50,
            "status": "success",
        }
        for i in range(10)
    ]
    resp = await client.post("/api/v1/traces", json={"session_id": session_id, "events": events})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ingested"] == 10
    assert data["session_id"] == session_id

    # Verify retrieval
    resp2 = await client.get(f"/api/v1/traces/{session_id}")
    assert resp2.status_code == 200
    assert len(resp2.json()["events"]) == 10


@pytest.mark.asyncio
async def test_ingest_unknown_model(client):
    """Ingest event with unknown model — cost should be 0.0, not an error."""
    session_id = "01JKTEST00000000000000002"
    resp = await client.post("/api/v1/traces", json={
        "session_id": session_id,
        "events": [{
            "session_id": session_id,
            "event_type": "llm_call",
            "event_name": "unknown_model_call",
            "model": "some-unknown-model-v9",
            "tokens_input": 500,
            "tokens_output": 200,
            "status": "success",
        }]
    })
    assert resp.status_code == 200
    events = (await client.get(f"/api/v1/traces/{session_id}")).json()["events"]
    assert events[0]["cost_usd"] == 0.0


@pytest.mark.asyncio
async def test_ingest_missing_optional_fields(client):
    """Ingest event with only required fields — defaults should be applied."""
    session_id = "01JKTEST00000000000000003"
    resp = await client.post("/api/v1/traces", json={
        "session_id": session_id,
        "events": [{
            "session_id": session_id,
            "event_type": "tool_call",
            "event_name": "web_search",
        }]
    })
    assert resp.status_code == 200
    events = (await client.get(f"/api/v1/traces/{session_id}")).json()["events"]
    assert events[0]["tokens_input"] == 0
    assert events[0]["cost_usd"] == 0.0
    assert events[0]["status"] == "success"
