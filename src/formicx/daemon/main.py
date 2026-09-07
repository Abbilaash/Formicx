from __future__ import annotations

import signal
import sys
import time
from pathlib import Path

from formicx.manifests.loader import load_agent_manifest
from formicx.runtime.manager import AgentManager


class FormicxDaemon:
    """The Formicx runtime daemon (formicxd)."""

    def __init__(self) -> None:
        self.manager = AgentManager()
        self._running = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        def handle_signal(signum, frame):
            print(f"\n[formicxd] Signal {signum} received. Initiating graceful shutdown...")
            self.stop()

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

    def load_and_start_manifest(self, manifest_path: str | Path) -> str:
        """Load an agent manifest, register it, and start the agent process.

        Args:
            manifest_path: Path to the agent.yaml file.

        Returns:
            The agent_id of the started Agent.
        """
        agent = load_agent_manifest(manifest_path)
        self.manager.register_agent(agent)
        self.manager.start_agent(agent.agent_id)
        print(f"[formicxd] Started Agent '{agent.name}' [{agent.agent_id}] entrypoint='{agent.entrypoint}'")
        return agent.agent_id

    def run(self) -> None:
        """Run the main daemon event loop."""
        self._running = True
        print("[formicxd] Formicx Daemon initialized and running.")
        try:
            while self._running:
                self.manager.refresh_all_statuses()
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\n[formicxd] KeyboardInterrupt caught.")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the daemon and terminate all managed child processes."""
        if not self._running:
            return
        self._running = False
        print("[formicxd] Shutting down all managed agent processes...")
        self.manager.shutdown_all()
        print("[formicxd] Formicx Daemon stopped cleanly.")


def main() -> None:
    """CLI entrypoint for running the Formicx daemon."""
    daemon = FormicxDaemon()
    daemon.run()


if __name__ == "__main__":
    main()
