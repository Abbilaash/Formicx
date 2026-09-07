from __future__ import annotations

import asyncio
import signal
import sys
import uvicorn

from formicx.config import FORMICX_DAEMON_HOST, FORMICX_DAEMON_PORT
from formicx.daemon.api import create_daemon_app
from formicx.runtime.manager import AgentManager


class FormicxDaemon:
    """The Formicx runtime daemon (formicxd)."""

    def __init__(
        self,
        host: str = FORMICX_DAEMON_HOST,
        port: int = FORMICX_DAEMON_PORT,
        manager: AgentManager | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.manager = manager if manager is not None else AgentManager()
        self.app = create_daemon_app(self.manager)
        self.server: uvicorn.Server | None = None

    def run(self) -> None:
        """Run the Uvicorn server hosting the local control API."""
        print(f"Formicx daemon started.")
        print(f"Local control interface available on http://{self.host}:{self.port}")
        print(f"Listening on localhost only.")

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
