"""Message Router for Formicx supporting local and distributed network routing."""

import logging
import threading
from typing import Any, Dict, List, Optional

from formicx.enums.agent_status import AgentStatus
from formicx.enums.message_type import MessageType
from formicx.models.message import Message
from formicx.communication.address import AgentAddress
from formicx.communication.discovery import AgentDiscoveryService
from formicx.communication.exceptions import (
    AgentNotFoundError,
    CommunicationDeniedError,
    InvalidMessageError,
    MessageDeliveryError,
    NodeUnavailableError,
)
from formicx.communication.inbox import AgentInbox
from formicx.communication.network_transport import NetworkHTTPTransport
from formicx.communication.peer import PeerRegistry
from formicx.communication.policy import CommunicationPolicyEngine

logger = logging.getLogger("formicx.communication.router")


class MessageRouter:
    """Routes messages between registered Formicx agents (local and distributed across nodes)."""

    def __init__(
        self,
        discovery: AgentDiscoveryService,
        policy_engine: Optional[CommunicationPolicyEngine] = None,
        local_node_name: Optional[str] = None,
        peer_registry: Optional[PeerRegistry] = None,
        network_transport: Optional[NetworkHTTPTransport] = None,
    ) -> None:
        self._discovery = discovery
        self._policy_engine = (
            policy_engine if policy_engine is not None else CommunicationPolicyEngine(discovery=discovery)
        )
        self.local_node_name = local_node_name
        self.peer_registry = peer_registry if peer_registry is not None else PeerRegistry()
        self.network_transport = network_transport if network_transport is not None else NetworkHTTPTransport()

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
        """Route a message to its local or remote destination if permitted by policy.

        Args:
            message: The Message instance to route.

        Returns:
            The canonical recipient agent_id or qualified destination address string.

        Raises:
            AgentNotFoundError: If sender or recipient cannot be found.
            CommunicationDeniedError: If policy prohibits communication.
            NodeUnavailableError: If remote destination node is unknown or offline.
            InvalidMessageError: If message formatting is invalid.
        """
        # Parse recipient address (e.g. 'vision-agent@raspberry-pi' or 'research-agent')
        recipient_addr = AgentAddress.parse(message.recipient)

        # Determine if message is destined for a remote node
        is_remote_dest = recipient_addr.is_remote and not recipient_addr.is_local_to(self.local_node_name)

        if is_remote_dest:
            return self._route_remote(message, recipient_addr)
        else:
            return self._route_local(message, recipient_addr)

    def _route_remote(self, message: Message, recipient_addr: AgentAddress) -> str:
        """Route message to a remote peer node."""
        # Validate sender exists locally (if sender is local)
        sender_addr = AgentAddress.parse(message.sender)
        if not sender_addr.is_remote or sender_addr.is_local_to(self.local_node_name):
            try:
                sender_agent = self._discovery.resolve_agent(sender_addr.agent_name)
                sender_key = sender_agent.name
                sender_id = sender_agent.agent_id
            except AgentNotFoundError:
                raise AgentNotFoundError(f"Sender agent not found in registry: '{message.sender}'")
        else:
            sender_key = sender_addr.to_string()
            sender_id = sender_addr.to_string()

        dest_qualified = recipient_addr.to_string()

        # Authoritative policy evaluation for remote destination
        if not self._policy_engine.can_communicate(sender_id, dest_qualified) and not self._policy_engine.can_communicate(sender_key, dest_qualified) and not self._policy_engine.can_communicate(sender_key, recipient_addr.agent_name):
            raise CommunicationDeniedError(
                f"CommunicationDeniedError: Agent '{sender_key}' "
                f"is not permitted to communicate with remote target '{dest_qualified}'."
            )

        # Normalize sender to qualified form if local node name exists
        if self.local_node_name and not sender_addr.is_remote:
            message.sender = f"{sender_key}@{self.local_node_name}"

        # Resolve peer node details
        node_name = recipient_addr.node_name
        peer = self.peer_registry.get_peer(node_name)

        # Transmit to remote node via NetworkHTTPTransport
        self.network_transport.send_remote_message(peer, message)
        return dest_qualified

    def _route_local(self, message: Message, recipient_addr: AgentAddress) -> str:
        """Route message to a local agent inbox."""
        # Resolve sender (local or incoming remote)
        sender_addr = AgentAddress.parse(message.sender)
        if not sender_addr.is_remote or sender_addr.is_local_to(self.local_node_name):
            try:
                sender_agent = self._discovery.resolve_agent(sender_addr.agent_name)
                sender_id = sender_agent.agent_id
                sender_name = sender_agent.name
            except AgentNotFoundError:
                raise AgentNotFoundError(f"Sender agent not found in registry: '{message.sender}'")
        else:
            sender_id = message.sender
            sender_name = message.sender

        # Resolve local recipient
        recipient_agent = self._discovery.resolve_agent(recipient_addr.agent_name)

        # Normalize message fields
        if not sender_addr.is_remote:
            message.sender = sender_agent.agent_id
        message.recipient = recipient_agent.agent_id

        # Authoritative policy evaluation for local destination
        if not self._policy_engine.can_communicate(sender_id, recipient_agent.agent_id) and not self._policy_engine.can_communicate(sender_name, recipient_agent.name) and not self._policy_engine.can_communicate(sender_id, recipient_agent.name):
            raise CommunicationDeniedError(
                f"CommunicationDeniedError: Agent '{sender_name}' ({sender_id}) "
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
        """Broadcast a message to all local registered agents allowed by policy."""
        sender_agent = self._discovery.resolve_agent(sender_identifier)
        all_agents = self._discovery.discover_agents()

        delivered_recipients: List[str] = []
        for target in all_agents:
            if target.agent_id == sender_agent.agent_id:
                continue
            if running_only and target.status != AgentStatus.RUNNING:
                continue

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
