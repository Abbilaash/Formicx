from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from typing import Dict, Optional


@dataclass
class ProcessHandle:
    """Encapsulates process metadata for a managed Agent OS process."""

    agent_id: str
    process: subprocess.Popen
    pid: int
    start_time: datetime
    exit_code: Optional[int] = None
    intentional_stop: bool = False

    def poll(self) -> Optional[int]:
        """Poll the underlying process to check if it has exited.

        Returns:
            The exit code integer if terminated, or None if still running.
        """
        if self.exit_code is not None:
            return self.exit_code

        code = self.process.poll()
        if code is not None:
            self.exit_code = code
        return self.exit_code

    def is_running(self) -> bool:
        """Check if the process is currently running.

        Returns:
            True if running, False if terminated.
        """
        return self.poll() is None


class ProcessManager:
    """Manages creation, execution, and lifecycle termination of Agent OS processes."""

    def __init__(self) -> None:
        self._handles: Dict[str, ProcessHandle] = {}

    def start_process(self, agent_id: str, entrypoint: str | Path) -> ProcessHandle:
        """Start an Agent as an independent OS subprocess.

        Args:
            agent_id: The unique identifier of the Agent.
            entrypoint: Path to the Python entrypoint script.

        Returns:
            The created ProcessHandle.

        Raises:
            RuntimeError: If the Agent is already running.
            FileNotFoundError: If the entrypoint script does not exist.
        """
        if self.is_running(agent_id):
            handle = self._handles[agent_id]
            raise RuntimeError(f"Agent '{agent_id}' is already running with PID {handle.pid}.")

        entrypoint_path = Path(entrypoint).resolve()
        if not entrypoint_path.is_file():
            raise FileNotFoundError(f"Entrypoint script not found: {entrypoint_path}")

        proc = subprocess.Popen(
            [sys.executable, str(entrypoint_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(entrypoint_path.parent),
        )

        handle = ProcessHandle(
            agent_id=agent_id,
            process=proc,
            pid=proc.pid,
            start_time=datetime.now(timezone.utc),
        )

        self._handles[agent_id] = handle
        return handle

    def get_process_handle(self, agent_id: str) -> Optional[ProcessHandle]:
        """Get the ProcessHandle for an Agent ID.

        Args:
            agent_id: The unique identifier of the Agent.

        Returns:
            The ProcessHandle or None if not managed.
        """
        return self._handles.get(agent_id)

    def is_running(self, agent_id: str) -> bool:
        """Check whether an Agent process is currently running.

        Args:
            agent_id: The unique identifier of the Agent.

        Returns:
            True if running, False otherwise.
        """
        handle = self._handles.get(agent_id)
        if handle is None:
            return False
        return handle.is_running()

    def poll_process(self, agent_id: str) -> Optional[int]:
        """Poll process status for an Agent.

        Args:
            agent_id: The unique identifier of the Agent.

        Returns:
            Exit code if terminated, None if running or not found.
        """
        handle = self._handles.get(agent_id)
        if handle is None:
            return None
        return handle.poll()

    def terminate_process(self, agent_id: str, timeout: float = 5.0) -> Optional[int]:
        """Stop an Agent process gracefully, with force-kill fallback.

        Args:
            agent_id: The unique identifier of the Agent.
            timeout: Seconds to wait for graceful termination before sending kill signal.

        Returns:
            The process exit code.
        """
        handle = self._handles.get(agent_id)
        if handle is None:
            return None

        handle.intentional_stop = True

        if handle.is_running():
            try:
                handle.process.terminate()
                handle.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                handle.process.kill()
                handle.process.wait(timeout=2.0)

        handle.poll()
        return handle.exit_code

    def terminate_all(self, timeout: float = 5.0) -> Dict[str, Optional[int]]:
        """Terminate all currently running child processes.

        Args:
            timeout: Graceful wait timeout per process.

        Returns:
            Dictionary mapping agent_id to exit code.
        """
        results: Dict[str, Optional[int]] = {}
        for agent_id in list(self._handles.keys()):
            if self.is_running(agent_id):
                results[agent_id] = self.terminate_process(agent_id, timeout=timeout)
            else:
                results[agent_id] = self._handles[agent_id].exit_code
        return results
