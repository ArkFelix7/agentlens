"""Tests for OpenAI/Anthropic interceptors using mock clients."""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.mark.asyncio
async def test_openai_interceptor_captures_tokens():
    """OpenAI interceptor captures model, token counts, and output."""
    import types
    captured = []

    class MockClient:
        _session_id = "interceptor-test"
        async def send_event(self, event):
            captured.append(event)

    # Create mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello world"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 10
    mock_response.model = "gpt-4o"

    # Import and test patching
    import openai.resources.chat.completions as completions_module
    original = completions_module.AsyncCompletions.create

    import sys; import agentlens_sdk.trace; trace_mod = sys.modules['agentlens_sdk.trace']
    with patch.object(trace_mod, "_global_client", MockClient()):
        with patch.object(trace_mod, "_global_session_id", "interceptor-test"):
            from agentlens_sdk.interceptors.openai_interceptor import patch_openai
            with patch.object(completions_module.AsyncCompletions, "create", new=AsyncMock(return_value=mock_response)):
                patch_openai()

    # Restore
    completions_module.Completions.create = original
