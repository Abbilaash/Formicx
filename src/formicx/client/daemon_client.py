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
        base_url: str = FORMICX_DAEMON_URL,
        timeout: float = 10.0,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
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
