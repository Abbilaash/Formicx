from __future__ import annotations

import asyncio
import os
import signal
import sys
import uvicorn

from formicx.communication.peer import PeerRegistry
from formicx.communication.service import CommunicationService
from formicx.config import (
    FORMICX_ANNOUNCE_INTERVAL,
    FORMICX_DAEMON_HOST,
    FORMICX_DAEMON_PORT,
    FORMICX_DISCOVERY_ENABLED,
    FORMICX_DISCOVERY_PORT,
    FORMICX_PEER_TIMEOUT,
)
from formicx.daemon.api import create_daemon_app
from formicx.discovery.service import DiscoveryService
from formicx.runtime.manager import AgentManager


class FormicxDaemon:
    """The Formicx runtime daemon (formicxd)."""

    def __init__(
        self,
        host: str = FORMICX_DAEMON_HOST,
        port: int = FORMICX_DAEMON_PORT,
        node_name: str | None = None,
        manager: AgentManager | None = None,
        comm_service: CommunicationService | None = None,
        peer_registry: PeerRegistry | None = None,
        discovery_service: DiscoveryService | None = None,
        discovery_enabled: bool = FORMICX_DISCOVERY_ENABLED,
        discovery_port: int = FORMICX_DISCOVERY_PORT,
        announce_interval: float = FORMICX_ANNOUNCE_INTERVAL,
        peer_timeout: float = FORMICX_PEER_TIMEOUT,
    ) -> None:
        self.host = host
        self.port = port
        self.node_name = node_name or os.getenv("FORMICX_NODE_NAME", "local")
        self.manager = manager if manager is not None else AgentManager()
        self.peer_registry = peer_registry if peer_registry is not None else PeerRegistry()

        self.comm_service = (
            comm_service
            if comm_service is not None
            else CommunicationService(
                registry=self.manager.registry,
                local_node_name=self.node_name,
                peer_registry=self.peer_registry,
            )
        )

        self.discovery_service = (
            discovery_service
            if discovery_service is not None
            else DiscoveryService(
                local_node_name=self.node_name,
                local_node_host=self.host,
                local_node_port=self.port,
                peer_registry=self.peer_registry,
                discovery_port=discovery_port,
                announce_interval=announce_interval,
                peer_timeout=peer_timeout,
                enabled=discovery_enabled,
            )
        )

        self.app = create_daemon_app(
            self.manager,
            comm_service=self.comm_service,
            discovery_service=self.discovery_service,
            node_name=self.node_name,
            node_host=self.host,
            node_port=self.port,
        )
        self.server: uvicorn.Server | None = None

    def run(self) -> None:
        """Run the Uvicorn server hosting the local control API."""
        print(f"Formicx daemon started (Node: '{self.node_name}').")
        print(f"Control & networking interface available on http://{self.host}:{self.port}")

        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        self.server = uvicorn.Server(config)

        try:
            self.server.run()
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop all managed agent child processes and shutdown daemon."""
        print("\n[formicxd] Shutting down all managed agent processes...")
        self.manager.shutdown_all()
        print("[formicxd] Formicx Daemon stopped cleanly.")


def main() -> None:
    """CLI entrypoint for formicxd binary."""
    daemon = FormicxDaemon()
    daemon.run()


if __name__ == "__main__":
    main()
