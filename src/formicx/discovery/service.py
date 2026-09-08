"""High-level Formicx Node Discovery Service."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from formicx.communication.peer import PeerRegistry
from formicx.discovery.network_utils import get_lan_ip
from formicx.discovery.protocol import DiscoveryMessage, DiscoveryMessageType
from formicx.discovery.transport import UDPDiscoveryTransport

logger = logging.getLogger("formicx.discovery.service")


class DiscoveryService:
    """Manages automatic LAN node discovery, periodic announcements, and peer expiration."""

    def __init__(
        self,
        local_node_name: str,
        local_node_host: str,
        local_node_port: int,
        peer_registry: PeerRegistry,
        discovery_port: int = 9999,
        announce_interval: float = 15.0,
        peer_timeout: float = 60.0,
        enabled: bool = True,
    ) -> None:
        self.node_name = local_node_name
        # If bound to 0.0.0.0, resolve the advertised host to the actual LAN IP for remote peers
        self.node_host = get_lan_ip() if (local_node_host == "0.0.0.0" or not local_node_host) else local_node_host
        self.node_port = local_node_port
        self.peer_registry = peer_registry
        self.discovery_port = discovery_port
        self.announce_interval = announce_interval
        self.peer_timeout = peer_timeout
        self.enabled = enabled

        self.transport = UDPDiscoveryTransport(port=self.discovery_port)
        self._announce_task: Optional[asyncio.Task] = None
        self._expiration_task: Optional[asyncio.Task] = None
        self._running = False

    def _is_self(self, msg: DiscoveryMessage) -> bool:
        """Check if received discovery message originated from this node."""
        if msg.node_name.strip().lower() == self.node_name.strip().lower():
            return True
        if msg.host == self.node_host and msg.port == self.node_port:
            return True
        return False

    def _on_message_received(self, msg: DiscoveryMessage, addr: tuple[str, int]) -> None:
        """Process incoming UDP discovery datagrams."""
        if self._is_self(msg):
            logger.debug(f"Ignoring self discovery message from '{msg.node_name}'")
            return

        logger.debug(f"Received discovery '{msg.message_type.value}' from node '{msg.node_name}' @ {msg.host}:{msg.port}")

        if msg.message_type in (DiscoveryMessageType.ANNOUNCE, DiscoveryMessageType.RESPONSE):
            self.peer_registry.update_discovered_peer(
                name=msg.node_name,
                host=msg.host,
                port=msg.port,
                source="discovered",
            )
        elif msg.message_type == DiscoveryMessageType.DISCOVER:
            # Register sender if known or valid
            self.peer_registry.update_discovered_peer(
                name=msg.node_name,
                host=msg.host,
                port=msg.port,
                source="discovered",
            )
            # Immediately respond with an ANNOUNCE response
            reply = DiscoveryMessage(
                message_type=DiscoveryMessageType.RESPONSE,
                node_name=self.node_name,
                host=self.node_host,
                port=self.node_port,
            )
            self.transport.send_broadcast(reply)

    async def _announce_loop(self) -> None:
        """Periodically broadcast ANNOUNCE datagrams."""
        while self._running:
            try:
                msg = DiscoveryMessage(
                    message_type=DiscoveryMessageType.ANNOUNCE,
                    node_name=self.node_name,
                    host=self.node_host,
                    port=self.node_port,
                )
                self.transport.send_broadcast(msg)
            except Exception as exc:
                logger.warning(f"Error sending discovery announcement: {exc}")

            await asyncio.sleep(self.announce_interval)

    async def _expiration_loop(self) -> None:
        """Periodically check peer registry for expired discovered peers."""
        # Check expirations twice as frequently as peer_timeout
        check_interval = max(5.0, self.peer_timeout / 4.0)
        while self._running:
            try:
                self.peer_registry.check_expirations(self.peer_timeout)
            except Exception as exc:
                logger.error(f"Error checking peer expirations: {exc}")

            await asyncio.sleep(check_interval)

    async def start(self) -> None:
        """Start discovery listening, send initial discovery request, and launch background tasks."""
        if not self.enabled:
            logger.info("Formicx discovery service is disabled.")
            return

        if self._running:
            return

        self._running = True
        await self.transport.start_listening(self._on_message_received)

        # Broadcast initial DISCOVER request to find peers immediately
        self.send_discovery_request()

        # Start periodic background loops
        loop = asyncio.get_running_loop()
        self._announce_task = loop.create_task(self._announce_loop())
        self._expiration_task = loop.create_task(self._expiration_loop())
        logger.info(f"Discovery service started for node '{self.node_name}' ({self.node_host}:{self.node_port})")

    def send_discovery_request(self) -> None:
        """Broadcast an immediate DISCOVER message to request announcements from active peers."""
        if not self.enabled:
            return

        msg = DiscoveryMessage(
            message_type=DiscoveryMessageType.DISCOVER,
            node_name=self.node_name,
            host=self.node_host,
            port=self.node_port,
        )
        self.transport.send_broadcast(msg)
        logger.info(f"Broadcasted immediate node discovery request from '{self.node_name}'")

    async def stop(self) -> None:
        """Stop background tasks and close UDP transport gracefully."""
        if not self._running:
            return

        self._running = False

        if self._announce_task is not None:
            self._announce_task.cancel()
            try:
                await self._announce_task
            except asyncio.CancelledError:
                pass
            self._announce_task = None

        if self._expiration_task is not None:
            self._expiration_task.cancel()
            try:
                await self._expiration_task
            except asyncio.CancelledError:
                pass
            self._expiration_task = None

        self.transport.close()
        logger.info("Discovery service stopped cleanly.")
