"""Communication domain exceptions for Formicx."""

class CommunicationError(Exception):
    """Base exception for all communication-related errors."""
    pass


class AgentNotFoundError(CommunicationError):
    """Raised when a target agent cannot be found by ID or name."""
    pass


class AmbiguousAgentError(CommunicationError):
    """Raised when an agent name matches multiple registered agents."""
    pass


class MessageDeliveryError(CommunicationError):
    """Raised when a message cannot be delivered or routed."""
    pass


class InvalidMessageError(CommunicationError):
    """Raised when a message format or payload is invalid."""
    pass


class TransportUnavailableError(CommunicationError):
    """Raised when the communication transport cannot reach the daemon."""
    pass


class CommunicationDeniedError(CommunicationError):
    """Raised when an agent attempts to communicate with a destination prohibited by policy."""
    pass


class NodeUnavailableError(CommunicationError):
    """Raised when a remote Formicx node is offline, unreachable, or unknown."""
    pass


class InvalidAgentAddressError(CommunicationError):
    """Raised when an agent address format is invalid."""
    pass


