"""OS process resource monitor using psutil for Formicx agents."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
from typing import Dict, Optional
import psutil

from formicx.resources.models import AgentResourceUsage

logger = logging.getLogger("formicx.resources.monitor")


class AgentResourceMonitor:
    """Monitors OS-level CPU, Memory, and Thread resources consumed by Formicx agents."""

    def __init__(self) -> None:
        # Cache psutil.Process objects by PID for accurate CPU delta calculations
        self._proc_cache: Dict[int, psutil.Process] = {}

    def _get_psutil_proc(self, pid: int) -> Optional[psutil.Process]:
        """Retrieve or instantiate a cached psutil.Process object."""
        if pid in self._proc_cache:
            proc = self._proc_cache[pid]
            if proc.is_running():
                return proc
            else:
                self._proc_cache.pop(pid, None)

        try:
            proc = psutil.Process(pid)
            # Initialize CPU percent calculation baseline
            proc.cpu_percent(interval=None)
            self._proc_cache[pid] = proc
            return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as exc:
            logger.debug(f"Unable to access process PID {pid}: {exc}")
            return None

    def sample_agent(
        self,
        agent_id: str,
        agent_name: str,
        pid: Optional[int],
        is_running: bool,
        status_override: Optional[str] = None,
    ) -> AgentResourceUsage:
        """Sample resource statistics for an Agent process.

        Args:
            agent_id: Unique agent identifier.
            agent_name: Display name of the agent.
            pid: Operating system Process ID.
            is_running: Logical running status from ProcessManager.
            status_override: Optional status string (e.g. 'STOPPED' or 'FAILED').

        Returns:
            Normalized AgentResourceUsage instance.
        """
        now = time.time()
        effective_override = status_override.upper() if status_override else None

        if pid is None or not is_running:
            # Clean up cache if process stopped
            if pid is not None:
                self._proc_cache.pop(pid, None)
            return AgentResourceUsage(
                agent_id=agent_id,
                agent_name=agent_name,
                pid=pid,
                status=effective_override or "STOPPED",
                cpu_percent=0.0,
                memory_bytes=0,
                memory_percent=0.0,
                thread_count=0,
                last_sampled_at=now,
            )

        proc = self._get_psutil_proc(pid)
        if proc is None:
            return AgentResourceUsage(
                agent_id=agent_id,
                agent_name=agent_name,
                pid=pid,
                status=effective_override or "UNKNOWN",
                cpu_percent=0.0,
                memory_bytes=0,
                memory_percent=0.0,
                thread_count=0,
                last_sampled_at=now,
            )

        try:
            # Gather process telemetry cleanly
            cpu_pct = proc.cpu_percent(interval=None)
            mem_info = proc.memory_info()
            rss_bytes = mem_info.rss
            mem_pct = proc.memory_percent()
            num_threads = proc.num_threads()
            proc_status = proc.status().upper()

            # Map psutil status or use RUNNING
            effective_status = effective_override or ("RUNNING" if proc_status in ("RUNNING", "SLEEPING", "DISK-SLEEP") else proc_status)

            return AgentResourceUsage(
                agent_id=agent_id,
                agent_name=agent_name,
                pid=pid,
                status=effective_status,
                cpu_percent=round(cpu_pct, 2),
                memory_bytes=rss_bytes,
                memory_percent=round(mem_pct, 2),
                thread_count=num_threads,
                last_sampled_at=now,
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as exc:
            logger.debug(f"Process PID {pid} became inaccessible during sampling: {exc}")
            self._proc_cache.pop(pid, None)
            return AgentResourceUsage(
                agent_id=agent_id,
                agent_name=agent_name,
                pid=pid,
                status=effective_override or "STOPPED",
                cpu_percent=0.0,
                memory_bytes=0,
                memory_percent=0.0,
                thread_count=0,
                last_sampled_at=now,
            )


    def clear_cache(self) -> None:
        """Clear cached psutil Process handles."""
        self._proc_cache.clear()
