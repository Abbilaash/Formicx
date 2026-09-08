"""Protocol definition and validation for Formicx UDP node discovery."""

from enum import Enum
import json
import logging
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("formicx.discovery.protocol")

PROTOCOL_IDENTIFIER = "formicx-discovery"
PROTOCOL_VERSION = "1"


class DiscoveryMessageType(str, Enum):
    """Types of node discovery messages."""

    ANNOUNCE = "ANNOUNCE"
    DISCOVER = "DISCOVER"
    RESPONSE = "RESPONSE"


class DiscoveryMessage(BaseModel):
    """Pydantic model representing a Formicx UDP discovery packet."""

    protocol: str = Field(default=PROTOCOL_IDENTIFIER, description="Protocol identifier")
    version: str = Field(default=PROTOCOL_VERSION, description="Protocol version string")
    message_type: DiscoveryMessageType = Field(..., description="Message intent: ANNOUNCE, DISCOVER, or RESPONSE")
    node_name: str = Field(..., description="Name identifier of the originating Formicx node")
    host: str = Field(..., description="Reachable LAN IP address or host of the originating node")
    port: int = Field(..., description="HTTP listener port of the originating node's formicxd daemon")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of announcement")

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: str) -> str:
        if v != PROTOCOL_IDENTIFIER:
            raise ValueError(f"Invalid protocol identifier '{v}', expected '{PROTOCOL_IDENTIFIER}'.")
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if v != PROTOCOL_VERSION:
            raise ValueError(f"Unsupported protocol version '{v}', expected '{PROTOCOL_VERSION}'.")
        return v

    @field_validator("node_name", "host")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or whitespace.")
        return stripped

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if v <= 0 or v > 65535:
            raise ValueError("Port must be an integer between 1 and 65535.")
        return v

    def to_json(self) -> str:
        """Serialize message to a compact JSON string."""
        return self.model_dump_json()

    def to_bytes(self) -> bytes:
        """Serialize message to UTF-8 encoded bytes for UDP transmission."""
        return self.to_json().encode("utf-8")


def parse_discovery_message(raw_data: bytes | str) -> Optional[DiscoveryMessage]:
    """Parse and validate raw UDP datagram bytes or JSON string into a DiscoveryMessage.

    Returns None if payload is malformed, invalid JSON, or fails protocol validation.
    Does not raise uncaught exceptions.
    """
    try:
        if isinstance(raw_data, bytes):
            text = raw_data.decode("utf-8", errors="replace")
        else:
            text = str(raw_data)

        data = json.loads(text)
        if not isinstance(data, dict):
            logger.debug("Discarding discovery packet: Root JSON payload is not an object.")
            return None

        msg = DiscoveryMessage.model_validate(data)
        return msg

    except Exception as exc:
        logger.debug(f"Discarding invalid discovery datagram: {exc}")
        return None
