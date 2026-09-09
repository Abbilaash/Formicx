from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from formicx.config import FORMICX_DAEMON_URL


class DaemonClientError(Exception):
    """Base exception for Formicx daemon client errors."""
    pass


class DaemonUnavailableError(DaemonClientError):
    """Raised when the Formicx daemon is unreachable."""

    def __init__(self, message: Optional[str] = None) -> None:
        if message is None:
            message = (
                "Unable to connect to formicxd.\n\n"
                "The Formicx daemon does not appear to be running.\n\n"
                "Start it with:\n\n"
                "    formicxd"
            )
        super().__init__(message)


class DaemonAPIError(DaemonClientError):
    """Raised when the Formicx daemon API returns an error response."""
    pass


class DaemonClient:
    """HTTP client abstraction for communicating with the local formicxd daemon."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        import os
        if base_url is None:
            base_url = os.getenv("FORMICX_DAEMON_URL", FORMICX_DAEMON_URL)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._custom_client = http_client

    def _get_client(self) -> httpx.Client:
        if self._custom_client is not None:
            return self._custom_client
        return httpx.Client(timeout=self.timeout)

    def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        client = self._get_client()
        url = f"{self.base_url}{path}"
        try:
            response = client.request(method, url, json=json_data)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            raise DaemonUnavailableError() from exc
        except httpx.HTTPError as exc:
            raise DaemonClientError(f"HTTP communication error: {exc}") from exc

        if response.is_error:
            try:
                data = response.json()
                detail = data.get("detail", response.text)
            except Exception:
                detail = response.text
            raise DaemonAPIError(detail)

        return response.json()

    def health(self) -> Dict[str, Any]:
        """Check health status of formicxd daemon."""
        return self._request("GET", "/v1/health")

    def daemon_status(self) -> Dict[str, Any]:
        """Retrieve operational metrics of formicxd daemon."""
        return self._request("GET", "/v1/daemon/status")

    def register_agent(self, path: str | Path) -> Dict[str, Any]:
        """Register an agent manifest with formicxd."""
        return self._request("POST", "/v1/agents/register", json_data={"path": str(path)})

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents from formicxd."""
        return self._request("GET", "/v1/agents")

    def get_agent(self, identifier: str) -> Dict[str, Any]:
        """Get details for a registered agent by ID or name."""
        return self._request("GET", f"/v1/agents/{identifier}")

    def start_agent(self, identifier: str) -> Dict[str, Any]:
        """Start a registered agent."""
        return self._request("POST", f"/v1/agents/{identifier}/start")

    def stop_agent(self, identifier: str) -> Dict[str, Any]:
        """Stop a running agent."""
        return self._request("POST", f"/v1/agents/{identifier}/stop")

    def restart_agent(self, identifier: str) -> Dict[str, Any]:
        """Restart a registered agent."""
        return self._request("POST", f"/v1/agents/{identifier}/restart")

    def send_message(
        self,
        sender: str,
        recipient: str,
        message_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message via the formicxd daemon."""
        data = {
            "sender": sender,
            "recipient": recipient,
            "message_type": message_type,
            "payload": payload,
            "correlation_id": correlation_id,
        }
        return self._request("POST", "/v1/messages", json_data=data)

    def get_inbox(
        self, identifier: str, history: bool = False
    ) -> List[Dict[str, Any]]:
        """Inspect pending messages or history for an agent's inbox."""
        path = f"/v1/agents/{identifier}/messages"
        if history:
            path += "?history=true"
        return self._request("GET", path)

    def receive_next_message(
        self, identifier: str, timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Consume the next pending message for an agent."""
        path = f"/v1/agents/{identifier}/messages/next"
        if timeout is not None:
            path += f"?timeout={timeout}"
        client = self._get_client()
        url = f"{self.base_url}{path}"
        try:
            response = client.get(url)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            raise DaemonUnavailableError() from exc
        except httpx.HTTPError as exc:
            raise DaemonClientError(f"HTTP communication error: {exc}") from exc

        if response.status_code == 204:
            return None

        if response.is_error:
            try:
                data = response.json()
                detail = data.get("detail", response.text)
            except Exception:
                detail = response.text
        return response.json()

    # --- Phase 5 Agent Communication Policies Client Methods ---

    def list_policies(self) -> Dict[str, Any]:
        """Fetch all loaded agent communication policies from formicxd."""
        return self._request("GET", "/v1/policies")

    def check_policy(self, source: str, destination: str) -> Dict[str, Any]:
        """Check whether source is permitted by policy to communicate with destination."""
        params = f"?source={source}&destination={destination}"
        return self._request("GET", f"/v1/policies/check{params}")

    # --- Phase 6 Distributed Agent Networking Client Methods ---

    def get_node_info(self) -> Dict[str, Any]:
        """Get local Formicx node details."""
        return self._request("GET", "/v1/node/info")

    def list_peers(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all registered remote peer nodes."""
        path = "/v1/node/peers"
        if active_only:
            path += "?active_only=true"
        return self._request("GET", path)

    def trigger_discovery(self) -> Dict[str, Any]:
        """Trigger an immediate LAN node discovery request."""
        return self._request("POST", "/v1/node/discover")

    def ping_peer(self, peer_name: str) -> Dict[str, Any]:
        """Ping a remote peer node to check status and latency."""
        return self._request("GET", f"/v1/node/ping/{peer_name}")

    # --- Phase 8 Agent-Aware Resource Monitoring Client Methods ---

    def get_all_resources(self) -> List[Dict[str, Any]]:
        """Fetch OS resource usage metrics for all registered agents."""
        return self._request("GET", "/v1/resources")

    def get_agent_resources(self, identifier: str) -> Dict[str, Any]:
        """Fetch OS resource usage metrics for a specific agent by ID or name."""
        return self._request("GET", f"/v1/agents/{identifier}/resources")
