"""Transport layer for the AgentLens Python SDK.

Buffers events and sends them via WebSocket (preferred) or HTTP POST (fallback).
Never raises exceptions to user code — all failures are silent.
"""

import asyncio
import json
import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class AgentLensClient:
    """Non-blocking WebSocket/HTTP client for sending trace events to AgentLens server."""

    def __init__(
        self,
        server_url: str = "ws://localhost:8766/ws",
        http_url: str = "http://localhost:8766",
    ):
        self.ws_url = server_url
        self.http_url = http_url
        self._ws = None
        self._buffer: list[dict] = []
        self._flush_interval = 1.0
        self._max_buffer_size = 20
        self._connected = False
        self._session_id: Optional[str] = None
        self._agent_name: Optional[str] = None
        self._flush_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Attempt WebSocket connection. Fails silently if server is unavailable."""
        try:
            import websockets
            self._ws = await websockets.connect(
                self.ws_url,
                open_timeout=3,
                close_timeout=3,
            )
            self._connected = True
            # Identify as SDK client
            await self._ws.send(json.dumps({"type": "hello", "role": "sdk"}))
            # Announce session with agent_name so server can create it properly
            if self._session_id:
                await self._ws.send(json.dumps({
                    "type": "session_start",
                    "data": {
                        "session_id": self._session_id,
                        "agent_name": self._agent_name or "agent",
                    },
                }))
            self._flush_task = asyncio.create_task(self._flush_loop())
            logger.info(f"AgentLens SDK connected to {self.ws_url}")
        except Exception as e:
            logger.warning(f"AgentLens SDK could not connect to server: {e}. Events will be sent via HTTP.")
            self._connected = False
            # Still start the flush loop to drain the buffer via HTTP
            if not self._flush_task or self._flush_task.done():
                self._flush_task = asyncio.create_task(self._flush_loop())

    async def send_event(self, event: dict) -> None:
        """Buffer event for batch sending. Never blocks or raises."""
        try:
            self._buffer.append(event)
            if len(self._buffer) >= self._max_buffer_size:
                await self._flush()
        except Exception as e:
            logger.warning(f"AgentLens SDK: failed to buffer event: {e}")

    async def send_message(self, message: dict) -> None:
        """Send a non-event WebSocket message (e.g., session_start)."""
        try:
            if self._connected and self._ws:
                await self._ws.send(json.dumps(message))
            else:
                await self._flush_via_http([message] if message.get("type") == "trace_events" else [])
        except Exception as e:
            logger.warning(f"AgentLens SDK: failed to send message: {e}")

    async def _flush(self) -> None:
        """Send buffered events to the server."""
        if not self._buffer or not self._session_id:
            return

        events = list(self._buffer)
        self._buffer.clear()

        if self._connected and self._ws:
            try:
                await self._ws.send(json.dumps({
                    "type": "trace_events",
                    "session_id": self._session_id,
                    "events": events,
                }))
                return
            except Exception as e:
                logger.warning(f"AgentLens SDK: WebSocket send failed: {e}")
                self._connected = False

        # Fallback to HTTP POST
        await self._flush_via_http(events)

    async def _flush_via_http(self, events: list[dict]) -> None:
        """Send events via HTTP POST as a fallback."""
        if not events or not self._session_id:
            return
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{self.http_url}/api/v1/traces",
                    json={"session_id": self._session_id, "events": events},
                    timeout=aiohttp.ClientTimeout(total=5),
                )
        except Exception as e:
            logger.warning(f"AgentLens SDK: HTTP fallback failed: {e}")

    async def _flush_loop(self) -> None:
        """Periodically flush the event buffer."""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush()
            except asyncio.CancelledError:
                # Final flush on shutdown
                await self._flush()
                break
            except Exception:
                pass

    async def close(self) -> None:
        """Flush remaining events and close connection."""
        try:
            if self._flush_task and not self._flush_task.done():
                self._flush_task.cancel()
                try:
                    await self._flush_task
                except asyncio.CancelledError:
                    pass
            await self._flush()
            if self._ws:
                await self._ws.close()
        except Exception:
            pass
