from __future__ import annotations

import os

FORMICX_DAEMON_HOST: str = os.getenv("FORMICX_DAEMON_HOST", "127.0.0.1")
FORMICX_DAEMON_PORT: int = int(os.getenv("FORMICX_DAEMON_PORT", "8765"))
FORMICX_DAEMON_URL: str = os.getenv(
    "FORMICX_DAEMON_URL", f"http://{FORMICX_DAEMON_HOST}:{FORMICX_DAEMON_PORT}"
)

# Discovery Configurations
_disc_enabled_str = os.getenv("FORMICX_DISCOVERY_ENABLED", "true").strip().lower()
FORMICX_DISCOVERY_ENABLED: bool = _disc_enabled_str not in ("false", "0", "no", "off")
FORMICX_DISCOVERY_PORT: int = int(os.getenv("FORMICX_DISCOVERY_PORT", "9999"))
FORMICX_ANNOUNCE_INTERVAL: float = float(os.getenv("FORMICX_ANNOUNCE_INTERVAL", "15.0"))
FORMICX_PEER_TIMEOUT: float = float(os.getenv("FORMICX_PEER_TIMEOUT", "60.0"))
# Resource Monitoring Configurations
_res_enabled_str = os.getenv("FORMICX_RESOURCES_ENABLED", "true").strip().lower()
FORMICX_RESOURCES_ENABLED: bool = _res_enabled_str not in ("false", "0", "no", "off")
FORMICX_RESOURCE_INTERVAL: float = float(os.getenv("FORMICX_RESOURCE_INTERVAL", "5.0"))
