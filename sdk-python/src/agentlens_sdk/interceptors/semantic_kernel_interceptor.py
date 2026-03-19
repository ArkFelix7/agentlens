"""Semantic Kernel integration for AgentLens.

Instruments Semantic Kernel function calls by registering a filter on the kernel.

Usage:
    from agentlens_sdk.interceptors.semantic_kernel_interceptor import instrument_semantic_kernel
    instrument_semantic_kernel(kernel)  # pass your Kernel instance
"""

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def instrument_semantic_kernel(kernel: Any) -> None:
    """Attach an AgentLens filter to a Semantic Kernel instance.

    Traces every function invocation (plugin functions, prompt functions, etc.)
    as a trace event sent to the AgentLens dashboard.

    Args:
        kernel: A semantic_kernel.Kernel instance.
    """
    try:
        from semantic_kernel.filters.filter_types import FilterTypes
        from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext
    except ImportError:
        logger.warning(
            "semantic-kernel not installed. "
            "Install with: pip install semantic-kernel"
        )
        return

    from agentlens_sdk.trace import get_client, get_session_id, SpanContext

    @kernel.filter(FilterTypes.FUNCTION_INVOCATION)
    async def agentlens_function_filter(
        context: FunctionInvocationContext,
        next: Callable,
    ) -> None:
        client = get_client()
        session_id = get_session_id()
        if client is None or session_id is None:
            await next(context)
            return

        fn = context.function
        plugin_name = getattr(fn, "plugin_name", "unknown")
        fn_name = getattr(fn, "name", "unknown")
        event_name = f"sk:{plugin_name}.{fn_name}"

        # Determine event type
        is_llm = hasattr(fn, "prompt_template") or "prompt" in fn_name.lower()
        event_type = "llm_call" if is_llm else "tool_call"

        # Capture input arguments
        try:
            input_data = {
                k: str(v)
                for k, v in context.arguments.items()
            }
        except Exception:
            input_data = {}

        span = SpanContext(
            event_type=event_type,
            event_name=event_name,
            session_id=session_id,
            client=client,
        )
        span.set_input(input_data)

        try:
            await next(context)

            # Capture output
            try:
                result = context.result
                output_data = {"result": str(result)} if result is not None else {}
            except Exception:
                output_data = {}

            # Extract token usage if available (prompt functions)
            tokens_input = 0
            tokens_output = 0
            model = None
            try:
                metadata = getattr(context.result, "metadata", {}) or {}
                usage = metadata.get("usage")
                if usage:
                    tokens_input = getattr(usage, "prompt_tokens", 0) or 0
                    tokens_output = getattr(usage, "completion_tokens", 0) or 0
                model = metadata.get("model_id")
            except Exception:
                pass

            span.set_output(output_data)
            span.set_tokens(tokens_input, tokens_output)
            if model:
                span.set_model(model)
            await span.async_end()

        except Exception as exc:
            try:
                span.set_error(str(exc))
                await span.async_end()
            except Exception:
                pass
            raise

    logger.info("AgentLens: Semantic Kernel filter attached.")
