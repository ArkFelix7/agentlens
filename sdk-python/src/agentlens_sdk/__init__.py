"""AgentLens Python SDK — real-time observability for AI agents.

Public API:
    init()           — Initialize the SDK with server URL
    trace()          — Decorator to trace a function
    auto_instrument()— Auto-patch OpenAI/Anthropic clients
    get_tracer()     — Get the current tracer for manual spans

Example:
    from agentlens_sdk import init, trace, auto_instrument

    init(server_url="ws://localhost:8766/ws")

    @trace(name="my_agent")
    async def my_agent(query: str) -> str:
        ...
"""

from agentlens_sdk.trace import init, trace, auto_instrument, get_current_tracer as get_tracer, get_prompt, Tracer, SpanContext
from agentlens_sdk.config import get_config

__version__ = "0.1.0"
__all__ = ["init", "trace", "auto_instrument", "get_tracer", "get_prompt", "Tracer", "SpanContext", "get_config"]
