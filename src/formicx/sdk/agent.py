"""Formicx Base Agent SDK Abstraction."""

from __future__ import annotations

import logging
import signal
import sys
from typing import Any, Dict, List, Optional, Union

from formicx.communication.transport import MessageTransport
from formicx.enums.message_type import MessageType
from formicx.models.agent import Agent as AgentModel
from formicx.models.message import Message
from formicx.sdk.context import AgentContext

logger = logging.getLogger("formicx.sdk.agent")


class Agent:
    """High-level Base Agent abstraction for Formicx developers.

    Provides automatic context management, lifecycle hooks (on_start, on_message,
    on_stop, on_error), messaging helpers, and an automatic execution loop.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        transport: Optional[MessageTransport] = None,
    ) -> None:
        self._context = AgentContext(
            agent_id=agent_id,
            agent_name=agent_name,
            transport=transport,
        )
        self._running: bool = False
        self._stop_called: bool = False

    @property
    def context(self) -> AgentContext:
        """Return the underlying AgentContext."""
        return self._context

    @property
    def id(self) -> str:
        """Return the agent's ID."""
        try:
            return self._context.identity
        except Exception:
            return ""

    @property
    def agent_id(self) -> str:
        """Alias for agent ID."""
        return self.id

    @property
    def name(self) -> str:
        """Return the agent's display name or identity."""
        return self._context.agent_name or self.id

    @property
    def agent_name(self) -> str:
        """Alias for agent name."""
        return self.name

    @property
    def running(self) -> bool:
        """Check if the agent message loop is running."""
        return self._running

    # --- Lifecycle Hooks ---

    def on_start(self) -> None:
        """Lifecycle hook invoked once before the message loop starts."""
        pass

    def on_message(self, message: Message) -> None:
        """Lifecycle hook invoked whenever a message is received."""
        pass

    def on_stop(self) -> None:
        """Lifecycle hook invoked once when the agent is shutting down."""
        pass

    def on_error(self, error: Exception) -> None:
        """Hook invoked when an unhandled error occurs in on_message()."""
        sys.stderr.write(f"[{self.name or 'Agent'}] Error in on_message: {error}\n")
        sys.stderr.flush()

    # --- Messaging Helper APIs ---

    def send(
        self,
        to: str,
        payload: Dict[str, Any],
        message_type: Union[str, MessageType] = MessageType.REQUEST,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message to another agent."""
        return self._context.send(
            to=to,
            payload=payload,
            message_type=message_type,
            correlation_id=correlation_id,
        )

    def receive(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Receive next pending message directly (mainly for custom behaviors)."""
        return self._context.receive(timeout=timeout)

    def reply(
        self,
        original_message: Message,
        payload: Dict[str, Any],
        message_type: Union[str, MessageType] = MessageType.RESPONSE,
    ) -> Dict[str, Any]:
        """Reply to an incoming message."""
        return self._context.reply(
            original_message=original_message,
            payload=payload,
            message_type=message_type,
        )

    def broadcast(
        self,
        payload: Dict[str, Any],
        message_type: Union[str, MessageType] = MessageType.EVENT,
        running_only: bool = False,
    ) -> List[str]:
        """Broadcast a message payload to all other registered agents."""
        return self._context.broadcast(
            payload=payload,
            message_type=message_type,
            running_only=running_only,
        )

    def discover(self, status: Optional[str] = None) -> List[AgentModel]:
        """Discover registered agents in Formicx."""
        return self._context.discover(status=status)

    def get_agent(self, identifier: str) -> AgentModel:
        """Get details for a registered agent."""
        return self._context.get_agent(identifier)

    # --- Execution Loop & Shutdown ---

    def stop(self) -> None:
        """Signal the agent message loop to stop."""
        self._running = False

    def _do_stop(self) -> None:
        """Execute on_stop exactly once."""
        if not self._stop_called:
            self._stop_called = True
            self._running = False
            try:
                self.on_stop()
            except Exception as exc:
                self.on_error(exc)

    def _setup_signal_handlers(self) -> None:
        """Register cross-platform signal handlers for graceful shutdown."""
        def handler(signum, frame):
            self.stop()

        try:
            signal.signal(signal.SIGINT, handler)
        except (ValueError, OSError):
            pass

        if hasattr(signal, "SIGTERM"):
            try:
                signal.signal(signal.SIGTERM, handler)
            except (ValueError, OSError):
                pass

    def run(self, poll_timeout: float = 0.2) -> None:
        """Start the agent execution lifecycle: on_start() -> message loop -> on_stop()."""
        self._running = True
        self._stop_called = False
        self._setup_signal_handlers()

        try:
            self.on_start()
        except Exception as exc:
            self.on_error(exc)
            self._do_stop()
            return

        try:
            while self._running:
                try:
                    message = self._context.receive(timeout=poll_timeout)
                    if message is not None:
                        try:
                            self.on_message(message)
                        except Exception as exc:
                            self.on_error(exc)
                except Exception as exc:
                    self.on_error(exc)
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            self._do_stop()


BaseAgent = Agent
