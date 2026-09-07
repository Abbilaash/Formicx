from __future__ import annotations

from typing import Dict, List, Optional

from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent
from formicx.runtime.process import ProcessManager
from formicx.runtime.registry import AgentRegistry


class AgentManager:
    """Central Formicx runtime manager coordinating Agent definitions and OS processes."""

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        process_manager: Optional[ProcessManager] = None,
    ) -> None:
        self.registry = registry if registry is not None else AgentRegistry()
        self.process_manager = process_manager if process_manager is not None else ProcessManager()

    def register_agent(self, agent: Agent) -> None:
        """Register an Agent definition in the runtime.

        Args:
            agent: The Agent instance to register.
        """
        self.registry.register(agent)

    def unregister_agent(self, agent_id: str) -> Agent:
        """Unregister an Agent definition from the runtime.

        Args:
            agent_id: The unique identifier of the Agent.

        Returns:
            The unregistered Agent model.

        Raises:
            RuntimeError: If the Agent is currently running.
        """
        if self.process_manager.is_running(agent_id):
            raise RuntimeError(f"Cannot unregister Agent '{agent_id}' while it is running. Stop it first.")
        return self.registry.unregister(agent_id)

    def get_agent(self, agent_id: str) -> Agent:
        """Get a registered Agent by ID.

        Args:
            agent_id: The unique agent identifier.

        Returns:
            The Agent model.
        """
        return self.registry.get(agent_id)

    def list_agents(self) -> List[Agent]:
        """List all registered Agents.

        Returns:
            List of all registered Agent models.
        """
        return self.registry.list_agents()

    def start_agent(self, agent_id: str) -> Agent:
        """Start an Agent as an independent OS process.

        Args:
            agent_id: The unique agent identifier.

        Returns:
            The updated Agent model with RUNNING status.

        Raises:
            RuntimeError: If the Agent is already running.
        """
        agent = self.registry.get(agent_id)
        self.refresh_agent_status(agent_id)

        if self.process_manager.is_running(agent_id) or agent.status in (
            AgentStatus.RUNNING,
            AgentStatus.STARTING,
        ):
            raise RuntimeError(f"Agent '{agent_id}' is already running.")

        agent.status = AgentStatus.STARTING

        try:
            self.process_manager.start_process(agent_id, agent.entrypoint)
            agent.status = AgentStatus.RUNNING
        except Exception:
            agent.status = AgentStatus.FAILED
            raise

        return agent

    def stop_agent(self, agent_id: str, timeout: float = 5.0) -> Agent:
        """Gracefully stop a running Agent process.

        Args:
            agent_id: The unique agent identifier.
            timeout: Grace period in seconds before force killing process.

        Returns:
            The updated Agent model with STOPPED status.
        """
        agent = self.registry.get(agent_id)
        self.refresh_agent_status(agent_id)

        if agent.status == AgentStatus.STOPPED:
            return agent

        if not self.process_manager.is_running(agent_id):
            agent.status = AgentStatus.STOPPED
            return agent

        agent.status = AgentStatus.STOPPING
        self.process_manager.terminate_process(agent_id, timeout=timeout)
        agent.status = AgentStatus.STOPPED
        return agent

    def restart_agent(self, agent_id: str, timeout: float = 5.0) -> Agent:
        """Restart an Agent process.

        Args:
            agent_id: The unique agent identifier.
            timeout: Grace period in seconds for stopping existing process.

        Returns:
            The restarted Agent model with RUNNING status.
        """
        if self.process_manager.is_running(agent_id):
            self.stop_agent(agent_id, timeout=timeout)
        return self.start_agent(agent_id)

    def refresh_agent_status(self, agent_id: str) -> AgentStatus:
        """Inspect underlying OS process status and update Agent lifecycle state.

        Args:
            agent_id: The unique agent identifier.

        Returns:
            The updated AgentStatus.
        """
        agent = self.registry.get(agent_id)
        handle = self.process_manager.get_process_handle(agent_id)

        if handle is None:
            return agent.status

        is_running = handle.is_running()

        if is_running:
            agent.status = AgentStatus.RUNNING
        else:
            if handle.intentional_stop:
                agent.status = AgentStatus.STOPPED
            elif agent.status in (AgentStatus.RUNNING, AgentStatus.STARTING):
                agent.status = AgentStatus.FAILED

        return agent.status

    def refresh_all_statuses(self) -> Dict[str, AgentStatus]:
        """Refresh status for all registered Agents.

        Returns:
            Dictionary mapping agent_id to updated AgentStatus.
        """
        statuses: Dict[str, AgentStatus] = {}
        for agent in self.registry.list_agents():
            statuses[agent.agent_id] = self.refresh_agent_status(agent.agent_id)
        return statuses

    def get_agent_status(self, agent_id: str) -> AgentStatus:
        """Get the current refreshed AgentStatus of an Agent.

        Args:
            agent_id: The unique agent identifier.

        Returns:
            The AgentStatus.
        """
        return self.refresh_agent_status(agent_id)

    def shutdown_all(self, timeout: float = 5.0) -> None:
        """Cleanly terminate all managed running child processes.

        Args:
            timeout: Grace period in seconds per process.
        """
        for agent in self.registry.list_agents():
            if self.process_manager.is_running(agent.agent_id):
                self.stop_agent(agent.agent_id, timeout=timeout)
