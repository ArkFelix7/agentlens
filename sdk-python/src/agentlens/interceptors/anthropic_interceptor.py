"""Anthropic interceptor — monkey-patches anthropic.messages.create to auto-trace completions."""

import logging
from agentlens.trace import get_client, get_session_id, SpanContext
from ulid import ULID

logger = logging.getLogger(__name__)

_patched = False


def patch_anthropic() -> None:
    """Monkey-patch the Anthropic client to auto-trace all message completions."""
    global _patched
    if _patched:
        return
    try:
        import anthropic.resources.messages as messages_module

        original_create = messages_module.Messages.create
        original_acreate = messages_module.AsyncMessages.create

        def traced_create(self, *args, **kwargs):
            client = get_client()
            session_id = get_session_id() or str(ULID())
            model_name = kwargs.get("model", "claude-unknown")
            span = SpanContext(
                event_type="llm_call",
                event_name=f"anthropic:{model_name}",
                session_id=session_id,
                client=client,
            )
            span.set_input({
                "messages": kwargs.get("messages", []),
                "model": model_name,
                "system": kwargs.get("system"),
            })
            try:
                result = original_create(self, *args, **kwargs)
                content = result.content[0].text if result.content else ""
                span.set_output({"content": content})
                span.set_tokens(
                    input_tokens=result.usage.input_tokens,
                    output_tokens=result.usage.output_tokens,
                )
                span.set_model(result.model)
                return result
            except Exception as e:
                span.set_error(str(e))
                raise
            finally:
                span.end()

        async def traced_acreate(self, *args, **kwargs):
            client = get_client()
            session_id = get_session_id() or str(ULID())
            model_name = kwargs.get("model", "claude-unknown")
            span = SpanContext(
                event_type="llm_call",
                event_name=f"anthropic:{model_name}",
                session_id=session_id,
                client=client,
            )
            span.set_input({
                "messages": kwargs.get("messages", []),
                "model": model_name,
                "system": kwargs.get("system"),
            })
            try:
                result = await original_acreate(self, *args, **kwargs)
                content = result.content[0].text if result.content else ""
                span.set_output({"content": content})
                span.set_tokens(
                    input_tokens=result.usage.input_tokens,
                    output_tokens=result.usage.output_tokens,
                )
                span.set_model(result.model)
                return result
            except Exception as e:
                span.set_error(str(e))
                raise
            finally:
                span.end()

        messages_module.Messages.create = traced_create
        messages_module.AsyncMessages.create = traced_acreate
        _patched = True
    except ImportError:
        raise
