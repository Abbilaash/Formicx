"""UDP Transport for Formicx LAN node discovery."""

from __future__ import annotations

import asyncio
import logging
import socket
from typing import Callable, Optional

from formicx.discovery.protocol import DiscoveryMessage, parse_discovery_message

logger = logging.getLogger("formicx.discovery.transport")


class DiscoveryDatagramProtocol(asyncio.DatagramProtocol):
    """Asyncio DatagramProtocol handler for receiving UDP discovery messages."""

    def __init__(self, callback: Callable[[DiscoveryMessage, tuple[str, int]], None]) -> None:
        self.callback = callback
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport
        logger.debug("UDP discovery datagram transport connection established.")

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        msg = parse_discovery_message(data)
        if msg is not None:
            try:
                self.callback(msg, addr)
            except Exception as exc:
                logger.error(f"Error processing discovery message callback from {addr}: {exc}")

    def error_received(self, exc: Exception) -> None:
        logger.warning(f"UDP discovery transport error: {exc}")

    def connection_lost(self, exc: Optional[Exception]) -> None:
        logger.debug(f"UDP discovery transport closed: {exc}")


class UDPDiscoveryTransport:
    """Manages UDP broadcast socket creation, sending, and receiving for Formicx discovery."""

    def __init__(
        self,
        port: int = 9999,
        bind_host: str = "0.0.0.0",
        broadcast_host: str = "<broadcast>",
    ) -> None:
        self.port = port
        self.bind_host = bind_host
        self.broadcast_host = broadcast_host
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.protocol: Optional[DiscoveryDatagramProtocol] = None

    def create_broadcast_socket(self) -> socket.socket:
        """Create and configure a UDP socket with SO_BROADCAST and SO_REUSEADDR."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # On systems that support SO_REUSEPORT (Linux, macOS), enable it for sharing discovery ports
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass

        sock.setblocking(False)
        sock.bind((self.bind_host, self.port))
        return sock

    async def start_listening(
        self, callback: Callable[[DiscoveryMessage, tuple[str, int]], None]
    ) -> None:
        """Start listening for incoming UDP discovery datagrams."""
        loop = asyncio.get_running_loop()
        sock = self.create_broadcast_socket()

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: DiscoveryDatagramProtocol(callback),
            sock=sock,
        )
        self.transport = transport
        self.protocol = protocol
        logger.info(f"UDP discovery listener bound and listening on {self.bind_host}:{self.port}")

    def send_broadcast(self, message: DiscoveryMessage) -> None:
        """Broadcast a DiscoveryMessage over UDP."""
        if self.transport is not None:
            payload = message.to_bytes()
            try:
                self.transport.sendto(payload, (self.broadcast_host, self.port))
                # Also send to 255.255.255.255 explicitly for compatibility across OS broadcast targets
                if self.broadcast_host != "255.255.255.255":
                    self.transport.sendto(payload, ("255.255.255.255", self.port))
            except Exception as exc:
                logger.warning(f"Failed to broadcast discovery datagram: {exc}")

    def close(self) -> None:
        """Close the UDP transport and release sockets."""
        if self.transport is not None:
            self.transport.close()
            self.transport = None
            self.protocol = None
            logger.info("UDP discovery transport closed.")
