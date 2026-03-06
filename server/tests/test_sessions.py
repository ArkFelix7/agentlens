"""Tests for session CRUD operations."""

import pytest


@pytest.mark.asyncio
async def test_create_list_delete_session(client):
    """Test full session lifecycle: create, list, delete."""
    # Create
    resp = await client.post("/api/v1/sessions", json={"agent_name": "test-agent"})
    assert resp.status_code == 200
    session = resp.json()
    session_id = session["id"]
    assert session["agent_name"] == "test-agent"
    assert session["status"] == "active"

    # List
    resp2 = await client.get("/api/v1/sessions")
    assert resp2.status_code == 200
    sessions = resp2.json()["sessions"]
    assert any(s["id"] == session_id for s in sessions)

    # Delete
    resp3 = await client.delete(f"/api/v1/sessions/{session_id}")
    assert resp3.status_code == 200
    assert resp3.json()["deleted"] is True

    # Verify gone
    resp4 = await client.get(f"/api/v1/sessions/{session_id}")
    assert resp4.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_session(client):
    resp = await client.delete("/api/v1/sessions/nonexistent-id")
    assert resp.status_code == 404
