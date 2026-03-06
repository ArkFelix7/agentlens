"""Tests for hallucination detection."""

import pytest


@pytest.mark.asyncio
async def test_number_transposition_detected(client):
    """Tool returns $2.3M, LLM reports $3.2M — should detect CRITICAL hallucination."""
    session_id = "01JKTEST00000000000000010"

    # Create session
    await client.post("/api/v1/sessions", json={"id": session_id, "agent_name": "test"})

    # Ingest a tool_call with $2.3M in output
    tool_event = {
        "session_id": session_id,
        "event_type": "tool_call",
        "event_name": "get_financials",
        "output_data": {"revenue": "$2.3M", "growth": "12% YoY"},
        "status": "success",
    }
    # Ingest an llm_call that transpositions the number to $3.2M
    llm_event = {
        "session_id": session_id,
        "event_type": "llm_call",
        "event_name": "summarize",
        "model": "gpt-4o",
        "output_data": {"summary": "Revenue was $3.2M with 12% YoY growth"},
        "tokens_input": 200,
        "tokens_output": 50,
        "status": "success",
    }

    resp = await client.post("/api/v1/traces", json={
        "session_id": session_id,
        "events": [tool_event, llm_event],
    })
    assert resp.status_code == 200

    # Run hallucination check
    check_resp = await client.post("/api/v1/hallucinations/check", json={"session_id": session_id})
    assert check_resp.status_code == 200
    data = check_resp.json()
    assert data["summary"]["total"] > 0


@pytest.mark.asyncio
async def test_no_hallucination_when_matching(client):
    """When tool and LLM outputs match, no hallucination should be detected."""
    session_id = "01JKTEST00000000000000011"
    await client.post("/api/v1/sessions", json={"id": session_id, "agent_name": "test"})

    tool_event = {
        "session_id": session_id,
        "event_type": "tool_call",
        "event_name": "get_data",
        "output_data": {"value": "42"},
        "status": "success",
    }
    llm_event = {
        "session_id": session_id,
        "event_type": "llm_call",
        "event_name": "process",
        "model": "gpt-4o-mini",
        "output_data": {"result": "The value is 42"},
        "tokens_input": 50,
        "tokens_output": 20,
        "status": "success",
    }

    await client.post("/api/v1/traces", json={"session_id": session_id, "events": [tool_event, llm_event]})
    check_resp = await client.post("/api/v1/hallucinations/check", json={"session_id": session_id})
    data = check_resp.json()
    # No critical alerts for exact number match
    assert data["summary"]["critical"] == 0
