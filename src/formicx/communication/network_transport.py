"""Network HTTP Transport for inter-node Formicx distributed messaging."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
import httpx

from formicx.models.message import Message
from formicx.communication.exceptions import (
    AgentNotFoundError,
    CommunicationDeniedError,
    InvalidMessageError,
    MessageDeliveryError,
    NodeUnavailableError,
)
from formicx.communication.peer import PeerNode

logger = logging.getLogger("formicx.communication.network")


class NetworkHTTPTransport:
    """HTTP transport for sending Formicx messages to remote daemon nodes."""

    def __init__(
        self,
        timeout: float = 30.0,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.timeout = timeout
        self._custom_client = http_client

    def _get_client(self) -> httpx.Client:
        if self._custom_client is not None:
            return self._custom_client
        return httpx.Client(timeout=self.timeout)

    def send_remote_message(self, peer: PeerNode, message: Message) -> Dict[str, Any]:
        """Send a Formicx message to a remote node's daemon over HTTP.

        Args:
            peer: PeerNode instance representing the destination node.
            message: Message instance to transmit.

        Returns:
            Dictionary containing remote delivery confirmation.

        Raises:
            NodeUnavailableError: If the target peer node is unreachable.
            AgentNotFoundError: If recipient agent does not exist on target node.
            CommunicationDeniedError: If policy rejects the message on target node.
            InvalidMessageError: If remote node rejects message formatting.
        """
        client = self._get_client()
        url = f"{peer.url}/v1/messages/remote"
        payload = message.model_dump(mode="json")

        logger.info(
            f"Transmitting remote message {message.message_id} to node '{peer.name}' ({url}) "
            f"from '{message.sender}' to '{message.recipient}'"
        )

        try:
            resp = client.post(url, json=payload)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            raise NodeUnavailableError(
                f"Unable to reach remote node '{peer.name}' at {peer.url}: {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise NodeUnavailableError(
                f"HTTP network error contacting remote node '{peer.name}': {exc}"
            ) from exc

        if resp.is_error:
            self._handle_remote_error(resp, peer_name=peer.name)

        return resp.json()

    def ping_peer(self, peer: PeerNode, timeout: float = 5.0) -> Dict[str, Any]:
        """Ping a remote peer node health endpoint to measure status and latency.

        Args:
            peer: PeerNode instance.
            timeout: Max timeout in seconds.

        Returns:
            Dictionary containing status, node name, and latency_ms.

        Raises:
            NodeUnavailableError: If peer is unreachable.
        """
        client = self._get_client()
        url = f"{peer.url}/v1/health"
        start_t = time.perf_counter()

        try:
            resp = client.get(url, timeout=timeout)
            latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "ONLINE",
                    "peer": peer.name,
                    "host": peer.host,
                    "port": peer.port,
                    "latency_ms": latency_ms,
                    "daemon_info": data,
                }
            else:
                raise NodeUnavailableError(
                    f"Peer node '{peer.name}' returned non-200 status code: {resp.status_code}"
                )
        except Exception as exc:
            raise NodeUnavailableError(
                f"Peer node '{peer.name}' at {peer.url} is offline or unreachable: {exc}"
            ) from exc

    def _handle_remote_error(self, resp: httpx.Response, peer_name: str) -> None:
        """Map HTTP error status codes from remote node to Formicx domain exceptions."""
        try:
            data = resp.json()
            detail = data.get("detail", resp.text)
        except Exception:
            detail = resp.text

        status_code = resp.status_code

        if status_code == 404:
            raise AgentNotFoundError(detail)
        elif status_code == 403:
            raise CommunicationDeniedError(detail)
        elif status_code == 400:
            raise InvalidMessageError(detail)
        elif status_code in (502, 503, 504):
            raise NodeUnavailableError(f"Remote node '{peer_name}' unavailable ({status_code}): {detail}")
        else:
            raise MessageDeliveryError(f"Remote node '{peer_name}' delivery error ({status_code}): {detail}")
