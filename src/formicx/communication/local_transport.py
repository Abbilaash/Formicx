"""Local HTTP Transport implementation for Formicx Agent Communication."""

from typing import Any, Dict, List, Optional
import httpx

from formicx.config import FORMICX_DAEMON_URL
from formicx.enums.message_type import MessageType
from formicx.models.agent import Agent
from formicx.models.message import Message
from formicx.communication.exceptions import (
    AgentNotFoundError,
    AmbiguousAgentError,
    InvalidMessageError,
    MessageDeliveryError,
    TransportUnavailableError,
)
from formicx.communication.transport import MessageTransport


class LocalHTTPTransport(MessageTransport):
    """Local HTTP transport communicating with formicxd over 127.0.0.1."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
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

    def _handle_error_response(self, response: httpx.Response) -> None:
        try:
            data = response.json()
            detail = data.get("detail", response.text)
        except Exception:
            detail = response.text

        detail_lower = detail.lower()
        if "multiple agents" in detail_lower:
            raise AmbiguousAgentError(detail)
        elif "not found" in detail_lower:
            raise AgentNotFoundError(detail)
        elif "invalid" in detail_lower:
            raise InvalidMessageError(detail)
        else:
            raise MessageDeliveryError(detail)

    def send(self, message: Message) -> Dict[str, Any]:
        client = self._get_client()
        url = f"{self.base_url}/v1/messages"
        payload = message.model_dump(mode="json")
        try:
            resp = client.post(url, json=payload)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            raise TransportUnavailableError(
                "Unable to connect to formicxd communication service."
            ) from exc

        if resp.is_error:
            self._handle_error_response(resp)

        return resp.json()

    def receive_next(
        self, agent_identifier: str, timeout: Optional[float] = None
    ) -> Optional[Message]:
        client = self._get_client()
        url = f"{self.base_url}/v1/agents/{agent_identifier}/messages/next"
        params = {}
        if timeout is not None:
            params["timeout"] = timeout

        # Use read timeout longer than poll timeout
        read_timeout = max(self.timeout, (timeout or 0) + 5.0)

        try:
            resp = client.get(url, params=params, timeout=read_timeout)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            raise TransportUnavailableError(
                "Unable to connect to formicxd communication service."
            ) from exc

        if resp.status_code == 204:
            return None

        if resp.is_error:
            self._handle_error_response(resp)

        data = resp.json()
        if not data:
            return None
        return Message.model_validate(data)

    def discover_agents(self, status: Optional[str] = None) -> List[Agent]:
        client = self._get_client()
        url = f"{self.base_url}/v1/agents"
        params = {}
        if status:
            params["status"] = status

        try:
            resp = client.get(url, params=params)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            raise TransportUnavailableError(
                "Unable to connect to formicxd communication service."
            ) from exc

        if resp.is_error:
            self._handle_error_response(resp)

        return [Agent.model_validate(item) for item in resp.json()]

    def get_agent(self, identifier: str) -> Agent:
        client = self._get_client()
        url = f"{self.base_url}/v1/agents/{identifier}"
        try:
            resp = client.get(url)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            raise TransportUnavailableError(
                "Unable to connect to formicxd communication service."
            ) from exc

        if resp.is_error:
            self._handle_error_response(resp)

        return Agent.model_validate(resp.json())

    def broadcast(
        self,
        sender_identifier: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        running_only: bool = False,
    ) -> List[str]:
        client = self._get_client()
        url = f"{self.base_url}/v1/messages/broadcast"
        body = {
            "from_agent_id": sender_identifier,
            "message_type": message_type.value,
            "payload": payload,
            "running_only": running_only,
        }
        try:
            resp = client.post(url, json=body)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            raise TransportUnavailableError(
                "Unable to connect to formicxd communication service."
            ) from exc

        if resp.is_error:
            self._handle_error_response(resp)

        return resp.json().get("recipients", [])
