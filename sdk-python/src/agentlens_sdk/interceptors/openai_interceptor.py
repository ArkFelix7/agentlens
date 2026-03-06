"""OpenAI interceptor — monkey-patches the OpenAI async and sync clients to auto-trace all completions."""

import logging
from agentlens_sdk.trace import get_client, get_session_id, SpanContext
from ulid import ULID

logger = logging.getLogger(__name__)

_patched = False


def patch_openai() -> None:
    """Monkey-patch the OpenAI client to auto-trace all chat completions."""
    global _patched
    if _patched:
        return
    try:
        import openai
        import openai.resources.chat.completions as completions_module

        original_create = completions_module.Completions.create
        original_acreate = completions_module.AsyncCompletions.create

        def traced_create(self, *args, **kwargs):
            client = get_client()
            session_id = get_session_id() or str(ULID())
            span = SpanContext(
                event_type="llm_call",
                event_name=f"openai:{kwargs.get('model', 'unknown')}",
                session_id=session_id,
                client=client,
            )
            span.set_input({
                "messages": _safe_messages(kwargs.get("messages", [])),
                "model": kwargs.get("model"),
            })
            try:
                result = original_create(self, *args, **kwargs)
                span.set_output({"content": result.choices[0].message.content})
                span.set_tokens(
                    input_tokens=result.usage.prompt_tokens,
                    output_tokens=result.usage.completion_tokens,
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
            span = SpanContext(
                event_type="llm_call",
                event_name=f"openai:{kwargs.get('model', 'unknown')}",
                session_id=session_id,
                client=client,
            )
            span.set_input({
                "messages": _safe_messages(kwargs.get("messages", [])),
                "model": kwargs.get("model"),
            })
            try:
                result = await original_acreate(self, *args, **kwargs)
                span.set_output({"content": result.choices[0].message.content})
                span.set_tokens(
                    input_tokens=result.usage.prompt_tokens,
                    output_tokens=result.usage.completion_tokens,
                )
                span.set_model(result.model)
                return result
            except Exception as e:
                span.set_error(str(e))
                raise
            finally:
                span.end()

        completions_module.Completions.create = traced_create
        completions_module.AsyncCompletions.create = traced_acreate
        _patched = True
    except ImportError:
        raise  # Caller handles ImportError


def _safe_messages(messages: list) -> list:
    """Return messages with sensitive content preserved but API keys redacted."""
    from agentlens_sdk.trace import _redact
    return [_redact(m) if isinstance(m, dict) else m for m in messages]
