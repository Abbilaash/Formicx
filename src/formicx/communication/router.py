"""Message Router for Formicx."""

import threading
from typing import Any, Dict, List, Optional

from formicx.enums.agent_status import AgentStatus
from formicx.enums.message_type import MessageType
from formicx.models.message import Message
from formicx.communication.discovery import AgentDiscoveryService
from formicx.communication.exceptions import (
    AgentNotFoundError,
    CommunicationDeniedError,
    InvalidMessageError,
    MessageDeliveryError,
)
from formicx.communication.inbox import AgentInbox
from formicx.communication.policy import CommunicationPolicyEngine


class MessageRouter:
    """Routes messages between registered Formicx agents and manages inboxes with policy checks."""

    def __init__(
        self,
        discovery: AgentDiscoveryService,
        policy_engine: Optional[CommunicationPolicyEngine] = None,
    ) -> None:
        self._discovery = discovery
        self._policy_engine = (
            policy_engine if policy_engine is not None else CommunicationPolicyEngine(discovery=discovery)
        )
        self._inboxes: Dict[str, AgentInbox] = {}
        self._lock = threading.Lock()

    @property
    def policy_engine(self) -> CommunicationPolicyEngine:
        """Return the policy engine instance."""
        return self._policy_engine

    def get_or_create_inbox(self, agent_id: str) -> AgentInbox:
        """Get or lazily create an AgentInbox for the given agent_id."""
        with self._lock:
            if agent_id not in self._inboxes:
                self._inboxes[agent_id] = AgentInbox(agent_id=agent_id)
            return self._inboxes[agent_id]

    def get_inbox(self, agent_id: str) -> Optional[AgentInbox]:
        """Get an AgentInbox if it exists."""
        with self._lock:
            return self._inboxes.get(agent_id)

    def route(self, message: Message) -> str:
        """Route a message to its recipient inbox if permitted by communication policy.

        Args:
            message: The Message instance to route.

        Returns:
            The canonical recipient agent_id.

        Raises:
            AgentNotFoundError: If sender or recipient cannot be found.
            CommunicationDeniedError: If policy prohibits communication from sender to recipient.
            InvalidMessageError: If message structure is invalid.
        """
        # Validate sender exists in registry
        try:
            sender_agent = self._discovery.resolve_agent(message.sender)
        except AgentNotFoundError:
            raise AgentNotFoundError(f"Sender agent not found in registry: '{message.sender}'")

        # Resolve recipient
        recipient_agent = self._discovery.resolve_agent(message.recipient)

        # Normalize sender and recipient IDs on the message
        message.sender = sender_agent.agent_id
        message.recipient = recipient_agent.agent_id

        # Authoritative policy evaluation
        if not self._policy_engine.can_communicate(sender_agent.agent_id, recipient_agent.agent_id):
            raise CommunicationDeniedError(
                f"CommunicationDeniedError: Agent '{sender_agent.name}' ({sender_agent.agent_id}) "
                f"is not permitted to communicate with '{recipient_agent.name}' ({recipient_agent.agent_id})."
            )

        # Enqueue into recipient inbox
        inbox = self.get_or_create_inbox(recipient_agent.agent_id)
        inbox.enqueue(message)

        return recipient_agent.agent_id

    def broadcast(
        self,
        sender_identifier: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        running_only: bool = False,
    ) -> List[str]:
        """Broadcast a message to all registered agents allowed by communication policy.

        Args:
            sender_identifier: Agent ID or name of sender.
            message_type: Type of message.
            payload: Message payload dictionary.
            running_only: If True, deliver only to currently RUNNING agents.

        Returns:
            List of recipient agent IDs delivered to.
        """
        sender_agent = self._discovery.resolve_agent(sender_identifier)
        all_agents = self._discovery.discover_agents()

        delivered_recipients: List[str] = []
        for target in all_agents:
            if target.agent_id == sender_agent.agent_id:
                continue
            if running_only and target.status != AgentStatus.RUNNING:
                continue

            # Check communication policy for broadcast destination
            if not self._policy_engine.can_communicate(sender_agent.agent_id, target.agent_id):
                continue

            broadcast_msg = Message(
                sender=sender_agent.agent_id,
                recipient=target.agent_id,
                message_type=message_type,
                payload=payload,
            )
            inbox = self.get_or_create_inbox(target.agent_id)
            inbox.enqueue(broadcast_msg)
            delivered_recipients.append(target.agent_id)

        return delivered_recipients

