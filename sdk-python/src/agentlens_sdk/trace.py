"""@trace decorator, TracerContext, and auto_instrument for AgentLens Python SDK.

Never raises exceptions to user code.
"""

import asyncio
import atexit
import functools
import json
import logging
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Optional

import uuid as _uuid


def _new_ulid() -> str:
    """Generate a new ULID string, compatible with both python-ulid and ulid-py packages."""
    try:
        import ulid as _ulid
        obj = _ulid.ULID()
        return str(obj)
    except (TypeError, AttributeError):
        try:
            import ulid as _ulid
            return str(_ulid.new())
        except Exception:
            pass
    except Exception:
        pass
    return _uuid.uuid4().hex[:26].upper()

from agentlens_sdk.client import AgentLensClient
from agentlens_sdk.config import get_config, set_config, SDKConfig, SENSITIVE_KEYS

logger = logging.getLogger(__name__)

# Thread-local/task-local current tracer
_current_tracer: Optional["Tracer"] = None
_global_client: Optional[AgentLensClient] = None
_global_session_id: Optional[str] = None


def _redact(data: Any) -> Any:
    """Recursively redact sensitive fields from dict data."""
    if not isinstance(data, dict):
        return data
    result = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_KEYS:
            result[k] = "[REDACTED]"
        elif isinstance(v, dict):
            result[k] = _redact(v)
        else:
            result[k] = v
    return result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_current_tracer() -> Optional["Tracer"]:
    return _current_tracer


def get_client() -> Optional[AgentLensClient]:
    return _global_client


def get_session_id() -> Optional[str]:
    return _global_session_id


def init(
    server_url: str | None = None,
    http_url: str | None = None,
    agent_name: str | None = None,
    session_id: str | None = None,
    agent_id: str | None = None,
    agent_role: str | None = None,
    parent_session_id: str | None = None,
) -> None:
    """Initialize the AgentLens SDK. Call once before using @trace or auto_instrument.

    Args:
        server_url: WebSocket URL of the AgentLens server.
        http_url: HTTP URL of the AgentLens server (fallback).
        agent_name: Human-readable agent name shown in the dashboard.
        session_id: Override the auto-generated ULID session ID.
        agent_id: Unique agent identifier for multi-agent topology (F9).
        agent_role: Role label for this agent in the topology (e.g. "planner").
        parent_session_id: Session ID of the parent agent for topology edges (F9).
    """
    global _global_client, _global_session_id

    config = SDKConfig(
        server_url=server_url,
        http_url=http_url,
        agent_name=agent_name,
    )
    set_config(config)

    _global_client = AgentLensClient(
        server_url=config.server_url,
        http_url=config.http_url,
    )
    _global_session_id = session_id or _new_ulid()
    _global_client._session_id = _global_session_id
    _global_client._agent_name = agent_name or "agent"
    _global_client._agent_id = agent_id
    _global_client._agent_role = agent_role
    _global_client._parent_session_id = parent_session_id

    # Connect asynchronously (non-blocking)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_global_client.connect())
        else:
            loop.run_until_complete(_global_client.connect())
    except Exception:
        pass

    # Register cleanup on process exit
    atexit.register(_on_exit)


def _on_exit() -> None:
    """Flush remaining events on process exit."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_global_client.close())
        else:
            loop.run_until_complete(_global_client.close())
    except Exception:
        pass


class SpanContext:
    """Represents an in-progress trace event span."""

    def __init__(
        self,
        event_type: str,
        event_name: str,
        session_id: str,
        parent_event_id: Optional[str] = None,
        client: Optional[AgentLensClient] = None,
    ):
        self.id = _new_ulid()
        self.event_type = event_type
        self.event_name = event_name
        self.session_id = session_id
        self.parent_event_id = parent_event_id
        self._client = client
        self._start_time = time.perf_counter()
        self._timestamp = _now_iso()
        self._input_data: Any = None
        self._output_data: Any = None
        self._model: Optional[str] = None
        self._tokens_input: int = 0
        self._tokens_output: int = 0
        self._status: str = "success"
        self._error: Optional[str] = None
        self._metadata: Optional[dict] = None

    def set_input(self, data: Any) -> None:
        try:
            self._input_data = _redact(data) if isinstance(data, dict) else data
        except Exception:
            pass

    def set_output(self, data: Any) -> None:
        try:
            self._output_data = _redact(data) if isinstance(data, dict) else data
        except Exception:
            pass

    def set_model(self, model: str) -> None:
        self._model = model

    def set_tokens(self, input_tokens: int, output_tokens: int) -> None:
        self._tokens_input = input_tokens
        self._tokens_output = output_tokens

    def set_error(self, error: str) -> None:
        self._status = "error"
        self._error = error

    def set_attribute(self, key: str, value: Any) -> None:
        if self._metadata is None:
            self._metadata = {}
        self._metadata[key] = value

    def _build_event(self) -> dict:
        duration_ms = (time.perf_counter() - self._start_time) * 1000
        return {
            "id": self.id,
            "session_id": self.session_id,
            "parent_event_id": self.parent_event_id,
            "event_type": self.event_type,
            "event_name": self.event_name,
            "timestamp": self._timestamp,
            "duration_ms": duration_ms,
            "input_data": self._input_data,
            "output_data": self._output_data,
            "model": self._model,
            "tokens_input": self._tokens_input,
            "tokens_output": self._tokens_output,
            "status": self._status,
            "error_message": self._error,
            "metadata": self._metadata,
        }

    async def async_end(self) -> None:
        """Finalize the span and await the send — use from async contexts."""
        try:
            event = self._build_event()
            if self._client:
                await self._client.send_event(event)
        except Exception:
            pass

    def end(self) -> None:
        """Finalize the span and send to AgentLens server (sync context)."""
        try:
            event = self._build_event()
            if self._client:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(self._client.send_event(event))
                    else:
                        loop.run_until_complete(self._client.send_event(event))
                except Exception:
                    pass
        except Exception:
            pass


class Tracer:
    """Tracer object for manual span creation."""

    def __init__(self, session_id: str, client: Optional[AgentLensClient] = None):
        self.session_id = session_id
        self._client = client
        self._current_span: Optional[SpanContext] = None

    def start_event(
        self,
        event_type: str,
        event_name: str,
        input_data: Any = None,
        parent_event_id: Optional[str] = None,
    ) -> SpanContext:
        """Start a new trace event span."""
        try:
            span = SpanContext(
                event_type=event_type,
                event_name=event_name,
                session_id=self.session_id,
                parent_event_id=parent_event_id or (self._current_span.id if self._current_span else None),
                client=self._client,
            )
            if input_data is not None:
                span.set_input(input_data)
            self._current_span = span
            return span
        except Exception:
            return SpanContext("unknown", event_name, self.session_id)

    @contextmanager
    def span(self, event_name: str, event_type: str = "decision"):
        """Context manager for manual span creation."""
        s = self.start_event(event_type, event_name)
        try:
            yield s
        except Exception as e:
            s.set_error(str(e))
            raise
        finally:
            s.end()


def trace(
    func: Callable | None = None,
    *,
    name: str | None = None,
    event_type: str = "decision",
    prompt_name: str | None = None,
    prompt_version: str | None = None,
):
    """Decorator that traces a function execution as a trace event.

    Usage:
        @trace
        async def my_func(): ...

        @trace(name="custom_name", event_type="llm_call", prompt_name="my_prompt", prompt_version="v2")
        async def my_func(): ...
    """
    def decorator(fn: Callable) -> Callable:
        event_name = name or fn.__name__
        _prompt_meta: dict = {}
        if prompt_name:
            _prompt_meta["prompt_name"] = prompt_name
        if prompt_version:
            _prompt_meta["prompt_version"] = prompt_version

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            client = get_client()
            session_id = get_session_id() or _new_ulid()
            if client and not client._session_id:
                client._session_id = session_id

            span = SpanContext(
                event_type=event_type,
                event_name=event_name,
                session_id=session_id,
                client=client,
            )
            if _prompt_meta:
                span._metadata = {**(_prompt_meta)}
            try:
                result = await fn(*args, **kwargs)
                span.set_output(result if not isinstance(result, (bytes, type(None))) else str(result))
                return result
            except Exception as e:
                span.set_error(str(e))
                raise
            finally:
                await span.async_end()

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            client = get_client()
            session_id = get_session_id() or _new_ulid()
            if client and not client._session_id:
                client._session_id = session_id

            span = SpanContext(
                event_type=event_type,
                event_name=event_name,
                session_id=session_id,
                client=client,
            )
            if _prompt_meta:
                span._metadata = {**(_prompt_meta)}
            try:
                result = fn(*args, **kwargs)
                span.set_output(result if not isinstance(result, (bytes, type(None))) else str(result))
                return result
            except Exception as e:
                span.set_error(str(e))
                raise
            finally:
                span.end()

        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    if func is not None:
        return decorator(func)
    return decorator


def get_prompt(name: str, version: Optional[int] = None) -> str:
    """Fetch a prompt from the AgentLens server prompt registry (F10).

    Returns the prompt text, or an empty string if unavailable.
    Never raises — fails silently so agent code is not disrupted.

    Args:
        name: Prompt name (e.g. "system_prompt").
        version: Specific version number. If None, fetches the current/promoted version.
    """
    try:
        config = get_config()
        import urllib.request
        base = config.http_url.rstrip("/")
        if version is not None:
            url = f"{base}/api/v1/prompts/{name}/versions/{version}"
            with urllib.request.urlopen(url, timeout=2) as resp:
                import json as _json
                data = _json.loads(resp.read())
                return data.get("content", "")
        else:
            url = f"{base}/api/v1/prompts/{name}/current"
            with urllib.request.urlopen(url, timeout=2) as resp:
                return resp.read().decode("utf-8")
    except Exception:
        return ""


def auto_instrument() -> None:
    """Auto-instrument supported AI frameworks.

    Automatically patches: OpenAI, Anthropic.
    Manual instrumentation required for:
      - LangChain: use AgentLensCallbackHandler
      - CrewAI: use instrument_crewai()
      - AutoGen: use instrument_autogen()
      - Semantic Kernel: use instrument_semantic_kernel(kernel)
    """
    try:
        from agentlens_sdk.interceptors.openai_interceptor import patch_openai
        patch_openai()
        logger.info("AgentLens: OpenAI auto-instrumented.")
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"AgentLens: OpenAI instrumentation failed: {e}")

    try:
        from agentlens_sdk.interceptors.anthropic_interceptor import patch_anthropic
        patch_anthropic()
        logger.info("AgentLens: Anthropic auto-instrumented.")
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"AgentLens: Anthropic instrumentation failed: {e}")
