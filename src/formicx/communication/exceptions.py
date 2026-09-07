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
