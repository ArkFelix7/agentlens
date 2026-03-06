"""MCP tool definitions for AgentLens.

Three tools:
  agentlens_start_session  — create a new debugging session
  agentlens_report_trace   — report a trace event
  agentlens_report_memory  — report a memory state change
"""

from mcp.types import Tool

TOOLS = [
    Tool(
        name="agentlens_start_session",
        description=(
            "Start a new AgentLens debugging session. "
            "Call once at the beginning of a task to get a session_id."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Name of the agent",
                    "default": "mcp-agent",
                }
            },
        },
    ),
    Tool(
        name="agentlens_report_trace",
        description=(
            "Report an agent execution trace event to AgentLens for debugging and observability. "
            "Call this after completing a tool call, LLM request, or decision to enable real-time debugging."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session ID from agentlens_start_session"},
                "event_type": {
                    "type": "string",
                    "enum": ["llm_call", "tool_call", "decision", "memory_read", "memory_write", "error"],
                    "description": "Type of event",
                },
                "event_name": {"type": "string", "description": "Human-readable name for this event"},
                "input_data": {"type": "string", "description": "JSON string of input to this step"},
                "output_data": {"type": "string", "description": "JSON string of output from this step"},
                "duration_ms": {"type": "number", "description": "Duration in milliseconds"},
                "model": {"type": "string", "description": "Model name if LLM call (e.g., 'gpt-4o')"},
                "tokens_input": {"type": "integer", "description": "Input token count"},
                "tokens_output": {"type": "integer", "description": "Output token count"},
                "status": {"type": "string", "enum": ["success", "error"], "default": "success"},
                "error_message": {"type": "string", "description": "Error details if status is error"},
            },
            "required": ["session_id", "event_type", "event_name"],
        },
    ),
    Tool(
        name="agentlens_report_memory",
        description=(
            "Report a memory state change to AgentLens. "
            "Call when agent creates, updates, reads, or deletes a memory."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "memory_key": {"type": "string", "description": "Identifier for this memory"},
                "content": {"type": "string", "description": "Memory content"},
                "action": {
                    "type": "string",
                    "enum": ["created", "updated", "accessed", "deleted"],
                },
            },
            "required": ["session_id", "memory_key", "content", "action"],
        },
    ),
]
