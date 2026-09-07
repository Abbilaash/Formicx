"""Formicx Agent SDK Context."""

import os
from typing import Any, Dict, List, Optional, Union

from formicx.enums.message_type import MessageType
from formicx.models.agent import Agent
from formicx.models.message import Message
from formicx.communication.exceptions import InvalidMessageError
from formicx.communication.local_transport import LocalHTTPTransport
from formicx.communication.transport import MessageTransport


class AgentContext:
    """Agent execution context providing native communication primitives."""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        transport: Optional[MessageTransport] = None,
    ) -> None:
        self.agent_id = agent_id or os.environ.get("FORMICX_AGENT_ID")
        self.agent_name = agent_name or os.environ.get("FORMICX_AGENT_NAME")
        self.transport = transport or LocalHTTPTransport()

    @classmethod
    def current(cls, transport: Optional[MessageTransport] = None) -> "AgentContext":
        """Initialize an AgentContext bound to the current process's environment identity."""
        return cls(transport=transport)

    @property
    def identity(self) -> str:
        """Return the primary identifier for this agent context."""
        if self.agent_id:
            return self.agent_id
        if self.agent_name:
            return self.agent_name
        raise InvalidMessageError("AgentContext has no agent_id or agent_name identity configured.")

    def send(
        self,
        to: str,
        payload: Dict[str, Any],
        message_type: Union[str, MessageType] = MessageType.REQUEST,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message to a recipient agent.

        Args:
            to: Recipient agent ID or name.
            payload: JSON-serializable dictionary payload.
            message_type: MessageType enum or string (REQUEST, RESPONSE, EVENT, NOTIFICATION).
            correlation_id: Optional correlation ID string.

        Returns:
            Dict containing delivery confirmation.
        """
        if isinstance(message_type, str):
            msg_type = MessageType(message_type.lower())
        else:
            msg_type = message_type

        message = Message(
            sender=self.identity,
            recipient=to,
            message_type=msg_type,
            payload=payload,
            correlation_id=correlation_id,
        )
        return self.transport.send(message)

    def receive(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Receive the next pending message for this agent, consuming it.

        Args:
            timeout: Maximum seconds to wait for a message.

        Returns:
            Message model or None if timeout expires without messages.
        """
        return self.transport.receive_next(self.identity, timeout=timeout)

    def reply(
        self,
        original_message: Message,
        payload: Dict[str, Any],
        message_type: Union[str, MessageType] = MessageType.RESPONSE,
    ) -> Dict[str, Any]:
        """Reply to an incoming message, setting recipient and correlation_id automatically.

        Args:
            original_message: The Message being replied to.
            payload: JSON-serializable dictionary response payload.
            message_type: MessageType enum or string (defaults to RESPONSE).

        Returns:
            Dict containing delivery confirmation.
        """
        return self.send(
            to=original_message.sender,
            payload=payload,
            message_type=message_type,
            correlation_id=original_message.message_id,
        )

    def discover(self, status: Optional[str] = None) -> List[Agent]:
        """Discover registered agents in Formicx."""
        return self.transport.discover_agents(status=status)

    def get_agent(self, identifier: str) -> Agent:
        """Resolve and retrieve registered agent details."""
        return self.transport.get_agent(identifier)

    def broadcast(
        self,
        payload: Dict[str, Any],
        message_type: Union[str, MessageType] = MessageType.EVENT,
        running_only: bool = False,
    ) -> List[str]:
        """Broadcast a message payload to all other registered agents."""
        if isinstance(message_type, str):
            msg_type = MessageType(message_type.lower())
        else:
            msg_type = message_type

        return self.transport.broadcast(
            sender_identifier=self.identity,
            message_type=msg_type,
            payload=payload,
            running_only=running_only,
        )
