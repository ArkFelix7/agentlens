"""LangChain callback handler for AgentLens tracing."""

import logging
from typing import Any, Optional
from uuid import UUID

from agentlens_sdk.trace import get_client, get_session_id, SpanContext
from ulid import ULID

logger = logging.getLogger(__name__)


class AgentLensCallbackHandler:
    """LangChain BaseCallbackHandler that forwards events to AgentLens."""

    def __init__(self):
        self._spans: dict[str, SpanContext] = {}

    def _get_span(self, run_id: UUID) -> Optional[SpanContext]:
        return self._spans.get(str(run_id))

    def on_llm_start(self, serialized: dict, prompts: list, run_id: UUID, **kwargs) -> None:
        try:
            client = get_client()
            session_id = get_session_id() or str(ULID())
            model_name = serialized.get("name", "unknown")
            span = SpanContext(
                event_type="llm_call",
                event_name=f"langchain:{model_name}",
                session_id=session_id,
                client=client,
            )
            span.set_input({"prompts": prompts})
            self._spans[str(run_id)] = span
        except Exception:
            pass

    def on_llm_end(self, response: Any, run_id: UUID, **kwargs) -> None:
        try:
            span = self._get_span(run_id)
            if span:
                generations = response.generations
                if generations and generations[0]:
                    text = generations[0][0].text if hasattr(generations[0][0], "text") else str(generations[0][0])
                    span.set_output({"content": text})
                if hasattr(response, "llm_output") and response.llm_output:
                    usage = response.llm_output.get("token_usage", {})
                    span.set_tokens(
                        input_tokens=usage.get("prompt_tokens", 0),
                        output_tokens=usage.get("completion_tokens", 0),
                    )
                span.end()
                del self._spans[str(run_id)]
        except Exception:
            pass

    def on_tool_start(self, serialized: dict, input_str: str, run_id: UUID, **kwargs) -> None:
        try:
            client = get_client()
            session_id = get_session_id() or str(ULID())
            tool_name = serialized.get("name", "unknown_tool")
            span = SpanContext(
                event_type="tool_call",
                event_name=tool_name,
                session_id=session_id,
                client=client,
            )
            span.set_input({"input": input_str})
            self._spans[str(run_id)] = span
        except Exception:
            pass

    def on_tool_end(self, output: str, run_id: UUID, **kwargs) -> None:
        try:
            span = self._get_span(run_id)
            if span:
                span.set_output({"output": output})
                span.end()
                del self._spans[str(run_id)]
        except Exception:
            pass

    def on_chain_start(self, serialized: dict, inputs: dict, run_id: UUID, **kwargs) -> None:
        try:
            client = get_client()
            session_id = get_session_id() or str(ULID())
            chain_name = serialized.get("name", "chain")
            span = SpanContext(
                event_type="decision",
                event_name=chain_name,
                session_id=session_id,
                client=client,
            )
            span.set_input(inputs)
            self._spans[str(run_id)] = span
        except Exception:
            pass

    def on_chain_end(self, outputs: dict, run_id: UUID, **kwargs) -> None:
        try:
            span = self._get_span(run_id)
            if span:
                span.set_output(outputs)
                span.end()
                del self._spans[str(run_id)]
        except Exception:
            pass

    def on_llm_error(self, error: Exception, run_id: UUID, **kwargs) -> None:
        try:
            span = self._get_span(run_id)
            if span:
                span.set_error(str(error))
                span.end()
                del self._spans[str(run_id)]
        except Exception:
            pass

    def on_tool_error(self, error: Exception, run_id: UUID, **kwargs) -> None:
        try:
            span = self._get_span(run_id)
            if span:
                span.set_error(str(error))
                span.end()
                del self._spans[str(run_id)]
        except Exception:
            pass
