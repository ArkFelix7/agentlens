"""CrewAI integration for AgentLens — patches Crew and Task execution to emit trace events.

Usage:
    from agentlens_sdk.interceptors.crewai_interceptor import instrument_crewai
    instrument_crewai()   # call once before building your crew
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_patched = False


def instrument_crewai() -> None:
    """Monkey-patch CrewAI's Agent and Task classes to emit AgentLens traces.

    Safe to call multiple times — only patches once. If CrewAI is not installed,
    logs a warning and returns silently.
    """
    global _patched
    if _patched:
        return

    try:
        import crewai  # noqa: F401
        from crewai import Agent, Task
    except ImportError:
        logger.warning("AgentLens: crewai not installed — skipping CrewAI instrumentation")
        return

    try:
        _patch_agent(Agent)
        _patch_task(Task)
        _patched = True
        logger.info("AgentLens: CrewAI instrumentation enabled")
    except Exception as e:
        logger.warning(f"AgentLens: CrewAI instrumentation failed: {e}")


def _patch_agent(Agent: Any) -> None:
    """Wrap Agent.execute_task to emit tool_call traces."""
    original_execute = getattr(Agent, "execute_task", None)
    if original_execute is None or getattr(original_execute, "_agentlens_patched", False):
        return

    def patched_execute_task(self, task: Any, *args, **kwargs) -> Any:
        from agentlens_sdk.trace import get_client, get_session_id, SpanContext
        from ulid import ULID
        try:
            client = get_client()
            session_id = get_session_id() or str(ULID())
            agent_role = getattr(self, "role", "agent")
            task_desc = getattr(task, "description", str(task))
            span = SpanContext(
                event_type="tool_call",
                event_name=f"crewai:agent:{agent_role}",
                session_id=session_id,
                client=client,
            )
            span.set_input({"task": task_desc})
        except Exception:
            span = None

        try:
            result = original_execute(self, task, *args, **kwargs)
            if span:
                span.set_output({"result": str(result)[:2000]})
                span.end()
            return result
        except Exception as exc:
            if span:
                span.set_error(str(exc))
                span.end()
            raise

    patched_execute_task._agentlens_patched = True
    Agent.execute_task = patched_execute_task


def _patch_task(Task: Any) -> None:
    """Wrap Task execution callback to emit decision traces."""
    # CrewAI tasks are data objects; actual execution is via Agent.
    # We instrument the Task's output assignment as a lightweight event.
    original_init = Task.__init__

    def patched_init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        # Emit a decision span when a task is created (planning phase)
        try:
            from agentlens_sdk.trace import get_client, get_session_id, SpanContext
            from ulid import ULID
            client = get_client()
            session_id = get_session_id()
            if client and session_id:
                span = SpanContext(
                    event_type="decision",
                    event_name="crewai:task:created",
                    session_id=session_id,
                    client=client,
                )
                span.set_input({"description": getattr(self, "description", "")})
                span.end()
        except Exception:
            pass

    if not getattr(original_init, "_agentlens_patched", False):
        patched_init._agentlens_patched = True
        Task.__init__ = patched_init
