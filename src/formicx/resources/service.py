"""ResourceService orchestrating agent OS process resource telemetry."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Dict, List, Optional

from formicx.communication.exceptions import AgentNotFoundError, AmbiguousAgentError
from formicx.models.agent import Agent
from formicx.resources.models import AgentResourceUsage
from formicx.resources.monitor import AgentResourceMonitor
from formicx.runtime.manager import AgentManager

logger = logging.getLogger("formicx.resources.service")


class ResourceService:
    """Service managing periodic background sampling of agent OS process metrics."""

    def __init__(

        self,
        agent_manager: AgentManager,
        monitor: Optional[AgentResourceMonitor] = None,
        interval_seconds: float = 5.0,
        enabled: bool = True,
    ) -> None:
        self.agent_manager = agent_manager
        self.monitor = monitor if monitor is not None else AgentResourceMonitor()
        self.interval_seconds = interval_seconds
        self.enabled = enabled

        self._metrics: Dict[str, AgentResourceUsage] = {}
        self._lock = threading.Lock()
        self._sampling_task: Optional[asyncio.Task] = None
        self._running = False

    def sample_all_resources(self) -> List[AgentResourceUsage]:
        """Perform a sampling sweep across all registered agents and update metric cache."""
        self.agent_manager.refresh_all_statuses()
        agents = self.agent_manager.list_agents()
        results: List[AgentResourceUsage] = []

        for agent in agents:
            handle = self.agent_manager.process_manager.get_process_handle(agent.agent_id)
            pid = handle.pid if handle else None
            is_running = handle.is_running() if handle else False
            status_str = agent.status.value

            usage = self.monitor.sample_agent(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                pid=pid,
                is_running=is_running,
                status_override=status_str,
            )

            with self._lock:
                self._metrics[agent.agent_id] = usage
            results.append(usage)

        return results

    def _resolve_agent(self, identifier: str) -> Agent:
        """Resolve an agent model by ID or display name."""
        agents = self.agent_manager.list_agents()
        # 1. Exact ID match
        for agt in agents:
            if agt.agent_id == identifier:
                return agt

        # 2. Name match
        named_matches = [agt for agt in agents if agt.name == identifier]
        if len(named_matches) == 1:
            return named_matches[0]
        elif len(named_matches) > 1:
            matching_ids = ", ".join([a.agent_id for a in named_matches])
            raise AmbiguousAgentError(f"Ambiguous agent name '{identifier}'. Multiple agents match: {matching_ids}")

        raise AgentNotFoundError(f"Agent not found: '{identifier}'")

    def get_agent_resources(self, identifier: str) -> AgentResourceUsage:
        """Get the latest resource metrics for an agent by ID or name."""
        agent = self._resolve_agent(identifier)
        self.agent_manager.refresh_agent_status(agent.agent_id)

        handle = self.agent_manager.process_manager.get_process_handle(agent.agent_id)
        pid = handle.pid if handle else None
        is_running = handle.is_running() if handle else False
        status_str = agent.status.value

        usage = self.monitor.sample_agent(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            pid=pid,
            is_running=is_running,
            status_override=status_str,
        )

        with self._lock:
            self._metrics[agent.agent_id] = usage

        return usage

    def get_all_resources(self) -> List[AgentResourceUsage]:
        """Return resource metrics for all registered agents."""
        return self.sample_all_resources()

    async def _sampling_loop(self) -> None:
        """Periodic background sampling loop."""
        while self._running:
            try:
                self.sample_all_resources()
            except Exception as exc:
                logger.error(f"Error during background resource sampling: {exc}")

            await asyncio.sleep(self.interval_seconds)

    async def start(self) -> None:
        """Start the background resource sampling service."""
        if not self.enabled:
            logger.info("Formicx resource monitoring service is disabled.")
            return

        if self._running:
            return

        self._running = True
        # Perform initial sampling sweep
        self.sample_all_resources()

        loop = asyncio.get_running_loop()
        self._sampling_task = loop.create_task(self._sampling_loop())
        logger.info(f"Formicx resource monitoring service started (interval: {self.interval_seconds}s).")

    async def stop(self) -> None:
        """Stop background sampling cleanly."""
        if not self._running:
            return

        self._running = False
        if self._sampling_task is not None:
            self._sampling_task.cancel()
            try:
                await self._sampling_task
            except asyncio.CancelledError:
                pass
            self._sampling_task = None

        self.monitor.clear_cache()
        logger.info("Formicx resource monitoring service stopped cleanly.")
