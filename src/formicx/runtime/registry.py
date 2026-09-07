from __future__ import annotations

from typing import Dict, List
from formicx.models.agent import Agent


class AgentRegistry:
    """In-memory registry for Formicx Agent definitions."""

    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        """Register an Agent definition in the registry.

        Args:
            agent: The Agent instance to register.

        Raises:
            ValueError: If an Agent with the same agent_id is already registered.
        """
        if agent.agent_id in self._agents:
            raise ValueError(f"Agent with ID '{agent.agent_id}' is already registered.")
        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> Agent:
        """Retrieve a registered Agent by ID.

        Args:
            agent_id: The unique agent identifier.

        Returns:
            The registered Agent model.

        Raises:
            KeyError: If no Agent with agent_id is found.
        """
        if agent_id not in self._agents:
            raise KeyError(f"Agent with ID '{agent_id}' is not registered.")
        return self._agents[agent_id]

    def list_agents(self) -> List[Agent]:
        """List all registered Agents.

        Returns:
            A list of all registered Agent models.
        """
        return list(self._agents.values())

    def unregister(self, agent_id: str) -> Agent:
        """Unregister an Agent definition from the registry.

        Args:
            agent_id: The unique agent identifier.

        Returns:
            The unregistered Agent model.

        Raises:
            KeyError: If no Agent with agent_id is found.
        """
        if agent_id not in self._agents:
            raise KeyError(f"Agent with ID '{agent_id}' is not registered.")
        return self._agents.pop(agent_id)

    def contains(self, agent_id: str) -> bool:
        """Check whether an Agent ID is registered.

        Args:
            agent_id: The unique agent identifier.

        Returns:
            True if registered, False otherwise.
        """
        return agent_id in self._agents
