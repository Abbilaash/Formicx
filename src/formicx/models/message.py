from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator

from formicx.enums.message_type import MessageType
from formicx.utils.ids import generate_message_id


class Message(BaseModel):
    """Represents a standard communication contract between Formicx primitives."""

    message_id: str = Field(default_factory=generate_message_id)
    sender: str
    recipient: str
    message_type: MessageType
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None

    @field_validator("message_type", mode="before")
    @classmethod
    def validate_message_type(cls, v: Any) -> MessageType:
        if isinstance(v, str):
            try:
                return MessageType(v.lower())
            except ValueError:
                raise ValueError(f"Invalid message_type '{v}'. Valid types: {[t.value for t in MessageType]}")
        return v

    @field_validator("sender", "recipient")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or whitespace.")
        return stripped


