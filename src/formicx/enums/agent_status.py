from __future__ import annotations

from enum import Enum


class AgentStatus(str, Enum):
    """Lifecycle states of a Formicx Agent."""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    WAITING = "waiting"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
