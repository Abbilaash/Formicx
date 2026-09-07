"""Abstract Transport interface for Formicx Agent Communication."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from formicx.enums.message_type import MessageType
from formicx.models.agent import Agent
from formicx.models.message import Message


class MessageTransport(ABC):
    """Abstract interface for agent transport implementations."""

    @abstractmethod
    def send(self, message: Message) -> Dict[str, Any]:
        """Send a message to the communication layer."""
        pass

    @abstractmethod
    def receive_next(
        self, agent_identifier: str, timeout: Optional[float] = None
    ) -> Optional[Message]:
        """Receive the next pending message for an agent."""
        pass

    @abstractmethod
    def discover_agents(self, status: Optional[str] = None) -> List[Agent]:
        """Discover registered agents."""
        pass

    @abstractmethod
    def get_agent(self, identifier: str) -> Agent:
        """Resolve and retrieve agent details."""
        pass

    @abstractmethod
    def broadcast(
        self,
        sender_identifier: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        running_only: bool = False,
    ) -> List[str]:
        """Broadcast a message payload to all agents except sender."""
        pass
