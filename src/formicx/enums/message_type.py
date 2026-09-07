from __future__ import annotations
from enum import Enum


class MessageType(str, Enum):
    """Standard message types for agent-to-agent communication."""
    TASK = "task"
    RESPONSE = "response"
    EVENT = "event"
    NOTIFICATION = "notification"
