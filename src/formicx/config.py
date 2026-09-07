from __future__ import annotations

import os

FORMICX_DAEMON_HOST: str = os.getenv("FORMICX_DAEMON_HOST", "127.0.0.1")
FORMICX_DAEMON_PORT: int = int(os.getenv("FORMICX_DAEMON_PORT", "8765"))
FORMICX_DAEMON_URL: str = os.getenv(
    "FORMICX_DAEMON_URL", f"http://{FORMICX_DAEMON_HOST}:{FORMICX_DAEMON_PORT}"
)
