"""AgentLens MCP server implementation.

Exposes three tools that MCP-native agents (Claude Desktop, Cursor, etc.)
can call to send trace events to the AgentLens server.
"""

import asyncio
import json
import os
import logging

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from ulid import ULID

from agentlens_mcp.tools import TOOLS

logger = logging.getLogger(__name__)

AGENTLENS_HTTP_URL = os.getenv("AGENTLENS_HTTP_URL", "http://localhost:8766/api/v1")

server = Server("agentlens")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            if name == "agentlens_start_session":
                session_id = str(ULID())
                await client.post(f"{AGENTLENS_HTTP_URL}/sessions", json={
                    "id": session_id,
                    "agent_name": arguments.get("agent_name", "mcp-agent"),
                })
                return [TextContent(type="text", text=f"Session started. Use this session_id: {session_id}")]

            elif name == "agentlens_report_trace":
                event = {
                    "id": str(ULID()),
                    "session_id": arguments["session_id"],
                    "event_type": arguments["event_type"],
                    "event_name": arguments["event_name"],
                    "input_data": arguments.get("input_data"),
                    "output_data": arguments.get("output_data"),
                    "duration_ms": arguments.get("duration_ms", 0),
                    "model": arguments.get("model"),
                    "tokens_input": arguments.get("tokens_input", 0),
                    "tokens_output": arguments.get("tokens_output", 0),
                    "status": arguments.get("status", "success"),
                    "error_message": arguments.get("error_message"),
                }
                resp = await client.post(f"{AGENTLENS_HTTP_URL}/traces", json={
                    "session_id": arguments["session_id"],
                    "events": [event],
                })
                if resp.status_code == 200:
                    return [TextContent(type="text", text="Trace event recorded successfully.")]
                return [TextContent(type="text", text=f"Trace recorded (status: {resp.status_code}).")]

            elif name == "agentlens_report_memory":
                resp = await client.post(f"{AGENTLENS_HTTP_URL}/memory", json={
                    "session_id": arguments["session_id"],
                    "memory_key": arguments["memory_key"],
                    "content": arguments["content"],
                    "action": arguments["action"],
                })
                return [TextContent(type="text", text="Memory state updated.")]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except httpx.ConnectError:
            return [TextContent(type="text", text="AgentLens server not reachable. Is it running on http://localhost:8766?")]
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
