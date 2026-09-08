"""Agent Address abstraction for Formicx distributed messaging."""

from __future__ import annotations

from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator

from formicx.communication.exceptions import InvalidAgentAddressError


class AgentAddress(BaseModel):
    """Represents a Formicx agent address (local or distributed)."""

    agent_name: str = Field(..., description="Agent ID or name")
    node_name: Optional[str] = Field(default=None, description="Optional remote node identifier")

    @field_validator("agent_name")
    @classmethod
    def validate_agent_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise InvalidAgentAddressError("Agent name in address cannot be empty or whitespace.")
        if "@" in stripped:
            raise InvalidAgentAddressError(f"Agent name '{v}' cannot contain '@' symbol.")
        return stripped

    @field_validator("node_name")
    @classmethod
    def validate_node_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise InvalidAgentAddressError("Node name in address cannot be empty or whitespace.")
        if "@" in stripped:
            raise InvalidAgentAddressError(f"Node name '{v}' cannot contain '@' symbol.")
        return stripped

    @property
    def is_remote(self) -> bool:
        """Check whether this address targets a remote node."""
        return self.node_name is not None and len(self.node_name) > 0

    def is_local_to(self, local_node_name: Optional[str]) -> bool:
        """Check whether address is local given the current local node name."""
        if not self.is_remote:
            return True
        if local_node_name is None:
            return False
        return self.node_name.lower() == local_node_name.lower()

    def to_string(self) -> str:
        """Return canonical string format ('agent@node' or 'agent')."""
        if self.node_name:
            return f"{self.agent_name}@{self.node_name}"
        return self.agent_name

    def __str__(self) -> str:
        return self.to_string()

    @classmethod
    def parse(cls, raw_address: Union[str, AgentAddress]) -> AgentAddress:
        """Parse a string or return existing AgentAddress instance.

        Args:
            raw_address: Address string (e.g. 'vision-agent@raspberry-pi' or 'research-agent')
                         or an existing AgentAddress instance.

        Returns:
            AgentAddress instance.

        Raises:
            InvalidAgentAddressError: If format is invalid.
        """
        if isinstance(raw_address, AgentAddress):
            return raw_address

        if not isinstance(raw_address, str):
            raise InvalidAgentAddressError(f"Agent address must be a string or AgentAddress, got {type(raw_address).__name__}")

        stripped = raw_address.strip()
        if not stripped:
            raise InvalidAgentAddressError("Agent address cannot be empty or whitespace.")

        parts = stripped.split("@")
        if len(parts) == 1:
            return cls(agent_name=parts[0])
        elif len(parts) == 2:
            agent_part, node_part = parts[0].strip(), parts[1].strip()
            if not agent_part:
                raise InvalidAgentAddressError(f"Invalid agent address '{raw_address}': missing agent name before '@'.")
            if not node_part:
                raise InvalidAgentAddressError(f"Invalid agent address '{raw_address}': missing node name after '@'.")
            return cls(agent_name=agent_part, node_name=node_part)
        else:
            raise InvalidAgentAddressError(f"Invalid agent address '{raw_address}': contains multiple '@' symbols.")
