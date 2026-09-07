from __future__ import annotations
import secrets


def generate_agent_id() -> str:
    """Generate a unique random identifier for an Agent (e.g. agt_a81f3e92)."""
    return f"agt_{secrets.token_hex(4)}"


def generate_message_id() -> str:
    """Generate a unique random identifier for a Message (e.g. msg_82bc17f9)."""
    return f"msg_{secrets.token_hex(4)}"


def generate_node_id() -> str:
    """Generate a unique random identifier for a Node (e.g. node_12345678)."""
    return f"node_{secrets.token_hex(4)}"


def generate_service_id() -> str:
    """Generate a unique random identifier for a Service (e.g. svc_abc12345)."""
    return f"svc_{secrets.token_hex(4)}"


def generate_team_id() -> str:
    """Generate a unique random identifier for a Team (e.g. team_789xyz12)."""
    return f"team_{secrets.token_hex(4)}"
