"""WebSocket connection manager.

Tracks all connected dashboard clients and SDK clients.
Broadcasts trace events to all dashboard clients in real-time.
"""

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections from dashboard clients and SDK clients."""

    def __init__(self):
        # Dashboard browser clients — receive real-time broadcasts
        self.dashboard_clients: set[WebSocket] = set()
        # SDK/agent clients — send trace events
        self.sdk_clients: set[WebSocket] = set()
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect_dashboard(self, ws: WebSocket) -> None:
        await ws.accept()
        self.dashboard_clients.add(ws)
        logger.info(f"Dashboard client connected. Total: {len(self.dashboard_clients)}")

    async def connect_sdk(self, ws: WebSocket) -> None:
        await ws.accept()
        self.sdk_clients.add(ws)
        logger.info(f"SDK client connected. Total: {len(self.sdk_clients)}")

    def disconnect(self, ws: WebSocket) -> None:
        self.dashboard_clients.discard(ws)
        self.sdk_clients.discard(ws)

    async def broadcast_to_dashboards(self, message: dict[str, Any]) -> None:
        """Send a message to all connected dashboard clients."""
        if not self.dashboard_clients:
            return
        data = json.dumps(message)
        dead = set()
        for client in self.dashboard_clients:
            try:
                await client.send_text(data)
            except Exception as e:
                logger.warning(f"Failed to send to dashboard client: {e}")
                dead.add(client)
        self.dashboard_clients -= dead

    async def send_to_client(self, ws: WebSocket, message: dict[str, Any]) -> None:
        """Send a message to a specific client."""
        try:
            await ws.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send to client: {e}")

    async def start_heartbeat(self) -> None:
        """Send periodic pings to detect stale connections."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            return
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(30)
            dead = set()
            for client in self.dashboard_clients | self.sdk_clients:
                try:
                    await client.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    dead.add(client)
            self.dashboard_clients -= dead
            self.sdk_clients -= dead


# Singleton instance shared across the application
manager = ConnectionManager()
