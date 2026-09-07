"""Agent Discovery Service for Formicx."""

from typing import List, Optional, Union

from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent
from formicx.runtime.registry import AgentRegistry
from formicx.communication.exceptions import AgentNotFoundError, AmbiguousAgentError


class AgentDiscoveryService:
    """Provides agent resolution and discovery using the AgentRegistry as source of truth."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def resolve_agent(self, identifier: str) -> Agent:
        """Resolve an agent identifier (which can be an agent_id or agent name).

        Args:
            identifier: The agent_id or unique agent name.

        Returns:
            The resolved Agent model.

        Raises:
            AgentNotFoundError: If no matching agent exists.
            AmbiguousAgentError: If multiple agents match the given name.
        """
        # 1. Direct agent_id lookup
        if self._registry.contains(identifier):
            return self._registry.get(identifier)

        # 2. Match by name
        all_agents = self._registry.list_agents()
        matches = [a for a in all_agents if a.name == identifier]

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            raise AmbiguousAgentError(
                f"Multiple agents named '{identifier}' exist. Use an Agent ID instead."
            )
        else:
            raise AgentNotFoundError(f"Agent not found: '{identifier}'")

    def discover_agents(
        self, status: Optional[Union[str, AgentStatus]] = None
    ) -> List[Agent]:
        """Discover registered agents with optional status filtering.

        Args:
            status: Optional AgentStatus or string status to filter by (e.g. 'RUNNING').

        Returns:
            List of matching Agent models.
        """
        agents = self._registry.list_agents()
        if status is None:
            return agents

        target_status_str = status.value if isinstance(status, AgentStatus) else str(status).upper()
        return [a for a in agents if a.status.value.upper() == target_status_str]
