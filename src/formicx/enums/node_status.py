from __future__ import annotations

from enum import Enum


class NodeStatus(str, Enum):
    """Availability and operational states of a Formicx Node."""

    ONLINE = "online"
    OFFLINE = "offline"
    UNAVAILABLE = "unavailable"
