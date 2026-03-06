"""AutoGen integration for AgentLens — patches ConversableAgent to emit trace events.

Usage:
    from agentlens_sdk.interceptors.autogen_interceptor import instrument_autogen
    instrument_autogen()   # call once before creating agents
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_patched = False


def instrument_autogen() -> None:
    """Monkey-patch AutoGen's ConversableAgent to emit AgentLens traces.

    Handles both pyautogen (autogen) and autogen-agentchat (autogen_agentchat).
    Safe to call multiple times — only patches once. If AutoGen is not installed,
    logs a warning and returns silently.
    """
    global _patched
    if _patched:
        return

    agent_cls = _import_agent_class()
    if agent_cls is None:
        logger.warning("AgentLens: autogen not installed — skipping AutoGen instrumentation")
        return

    try:
        _patch_initiate_chat(agent_cls)
        _patch_generate_reply(agent_cls)
        _patched = True
        logger.info("AgentLens: AutoGen instrumentation enabled")
    except Exception as e:
        logger.warning(f"AgentLens: AutoGen instrumentation failed: {e}")


def _import_agent_class() -> Any:
    """Try to import ConversableAgent from either autogen package variant."""
    for module_name in ("autogen", "pyautogen", "autogen_agentchat"):
        try:
            import importlib
            mod = importlib.import_module(module_name)
            cls = getattr(mod, "ConversableAgent", None)
            if cls is not None:
                return cls
        except ImportError:
            continue
    return None


def _patch_initiate_chat(Agent: Any) -> None:
    """Wrap initiate_chat to emit an agent_step span for each conversation."""
    original = getattr(Agent, "initiate_chat", None)
    if original is None or getattr(original, "_agentlens_patched", False):
        return

    def patched_initiate_chat(self, recipient: Any, message: Any = None, **kwargs) -> Any:
        from agentlens_sdk.trace import get_client, get_session_id, SpanContext
        from ulid import ULID
        try:
            client = get_client()
            session_id = get_session_id() or str(ULID())
            sender_name = getattr(self, "name", "agent")
            recipient_name = getattr(recipient, "name", "recipient")
            span = SpanContext(
                event_type="agent_step",
                event_name=f"autogen:chat:{sender_name}->{recipient_name}",
                session_id=session_id,
                client=client,
            )
            span.set_input({"message": str(message)[:2000] if message else None})
        except Exception:
            span = None

        try:
            result = original(self, recipient, message=message, **kwargs)
            if span:
                span.set_output({"summary": str(result)[:2000] if result else None})
                span.end()
            return result
        except Exception as exc:
            if span:
                span.set_error(str(exc))
                span.end()
            raise

    patched_initiate_chat._agentlens_patched = True
    Agent.initiate_chat = patched_initiate_chat


def _patch_generate_reply(Agent: Any) -> None:
    """Wrap generate_reply to emit llm_call traces for each LLM turn."""
    original = getattr(Agent, "generate_reply", None)
    if original is None or getattr(original, "_agentlens_patched", False):
        return

    def patched_generate_reply(self, messages: Any = None, sender: Any = None, **kwargs) -> Any:
        from agentlens_sdk.trace import get_client, get_session_id, SpanContext
        from ulid import ULID
        try:
            client = get_client()
            session_id = get_session_id() or str(ULID())
            agent_name = getattr(self, "name", "agent")
            model = None
            llm_config = getattr(self, "llm_config", None)
            if isinstance(llm_config, dict):
                config_list = llm_config.get("config_list", [])
                if config_list:
                    model = config_list[0].get("model")
            span = SpanContext(
                event_type="llm_call",
                event_name=f"autogen:reply:{agent_name}",
                session_id=session_id,
                client=client,
            )
            if model:
                span.set_model(model)
            last_msg = (messages or [{}])[-1] if messages else {}
            span.set_input({"content": str(last_msg.get("content", ""))[:2000]})
        except Exception:
            span = None

        try:
            result = original(self, messages=messages, sender=sender, **kwargs)
            if span:
                span.set_output({"content": str(result)[:2000] if result else None})
                span.end()
            return result
        except Exception as exc:
            if span:
                span.set_error(str(exc))
                span.end()
            raise

    patched_generate_reply._agentlens_patched = True
    Agent.generate_reply = patched_generate_reply
