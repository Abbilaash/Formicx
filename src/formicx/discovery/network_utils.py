"""Network utility functions for Formicx discovery."""

import socket
import logging

logger = logging.getLogger("formicx.discovery.network_utils")


def get_lan_ip() -> str:
    """Determine the primary non-loopback LAN IPv4 address for the current node.

    Uses a dummy UDP socket connection to an external address (8.8.8.8) to inspect
    the socket's local interface address. If network interfaces are offline or unreachable,
    falls back to '127.0.0.1'.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect does not actually send packets over UDP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception as exc:
        logger.debug(f"Could not determine LAN IP via UDP connection trick: {exc}. Falling back to 127.0.0.1")
        ip = "127.0.0.1"
    finally:
        s.close()

    return ip
