"""Communication Service for Formicx."""

from typing import Any, Dict, List, Optional, Union

from formicx.enums.agent_status import AgentStatus
from formicx.enums.message_type import MessageType
from formicx.models.agent import Agent
from formicx.models.message import Message
from formicx.runtime.registry import AgentRegistry
from formicx.communication.discovery import AgentDiscoveryService
from formicx.communication.inbox import AgentInbox
from formicx.communication.router import MessageRouter


class CommunicationService:
    """High-level Communication Service managing routing, inboxes, and discovery."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        self._discovery = AgentDiscoveryService(registry=self._registry)
        self._router = MessageRouter(discovery=self._discovery)

    @property
    def discovery(self) -> AgentDiscoveryService:
        return self._discovery

    @property
    def router(self) -> MessageRouter:
        return self._router

    def send_message(self, message: Message) -> Dict[str, Any]:
        """Send a message from one agent to another.

        Args:
            message: Message object to route.

        Returns:
            Dict containing delivery confirmation details.
        """
        canonical_recipient_id = self._router.route(message)
        return {
            "message_id": message.message_id,
            "status": "DELIVERED",
            "recipient_agent_id": canonical_recipient_id,
        }

    def receive_next(
        self, agent_identifier: str, timeout: Optional[float] = None
    ) -> Optional[Message]:
        """Receive the next pending message for an agent, consuming it.

        Args:
            agent_identifier: Agent ID or name.
            timeout: Max seconds to wait for a message.

        Returns:
            Message model or None if no message available.
        """
        agent = self._discovery.resolve_agent(agent_identifier)
        inbox = self._router.get_or_create_inbox(agent.agent_id)
        return inbox.receive_next(timeout=timeout)

    def peek_inbox(self, agent_identifier: str) -> List[Message]:
        """Inspect pending messages for an agent without consuming them.

        Args:
            agent_identifier: Agent ID or name.

        Returns:
            List of pending Message models.
        """
        agent = self._discovery.resolve_agent(agent_identifier)
        inbox = self._router.get_or_create_inbox(agent.agent_id)
        return inbox.peek()

    def list_history(self, agent_identifier: str) -> List[Message]:
        """List historical messages for an agent.

        Args:
            agent_identifier: Agent ID or name.

        Returns:
            List of historical Message models.
        """
        agent = self._discovery.resolve_agent(agent_identifier)
        inbox = self._router.get_or_create_inbox(agent.agent_id)
        return inbox.list_history()

    def discover_agents(
        self, status: Optional[Union[str, AgentStatus]] = None
    ) -> List[Agent]:
        """Discover registered agents with optional status filter."""
        return self._discovery.discover_agents(status=status)

    def get_agent(self, identifier: str) -> Agent:
        """Resolve and return registered agent details."""
        return self._discovery.resolve_agent(identifier)

    def broadcast(
        self,
        sender_identifier: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        running_only: bool = False,
    ) -> List[str]:
        """Broadcast payload to all registered agents except sender."""
        return self._router.broadcast(
            sender_identifier=sender_identifier,
            message_type=message_type,
            payload=payload,
            running_only=running_only,
        )
