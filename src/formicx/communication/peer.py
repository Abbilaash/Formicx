"""Peer Node model and Peer Registry for Formicx distributed networking."""

from __future__ import annotations

import logging
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, field_validator
import yaml

from formicx.communication.exceptions import NodeUnavailableError

logger = logging.getLogger("formicx.communication.peer")


class PeerNode(BaseModel):
    """Domain model representing a remote Formicx peer node."""

    name: str = Field(..., description="Unique name identifier of the peer node")
    host: str = Field(..., description="IP address or hostname of the peer node")
    port: int = Field(default=8765, description="Network listener port of the peer node")
    status: str = Field(default="ONLINE", description="Status of the peer node (e.g. ONLINE, OFFLINE, UNKNOWN)")

    @field_validator("name", "host")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or whitespace.")
        return stripped

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if v <= 0 or v > 65535:
            raise ValueError("port must be an integer between 1 and 65535.")
        return v

    @property
    def url(self) -> str:
        """Return base HTTP URL for peer node."""
        return f"http://{self.host}:{self.port}"


class PeerRegistry:
    """In-memory registry managing known Formicx peer nodes."""

    def __init__(self, initial_peers: Optional[List[PeerNode]] = None) -> None:
        self._peers: Dict[str, PeerNode] = {}
        self._lock = threading.Lock()
        if initial_peers:
            for peer in initial_peers:
                self.register_peer(peer)

    def register_peer(self, peer: PeerNode) -> PeerNode:
        """Register or update a peer node in the registry."""
        key = peer.name.strip().lower()
        with self._lock:
            self._peers[key] = peer
        logger.info(f"Registered peer node '{peer.name}' -> {peer.host}:{peer.port}")
        return peer

    def get_peer(self, name: str) -> PeerNode:
        """Retrieve a peer node by name.

        Args:
            name: Peer node name identifier.

        Returns:
            PeerNode instance.

        Raises:
            NodeUnavailableError: If peer node is not found in registry.
        """
        key = name.strip().lower()
        with self._lock:
            if key in self._peers:
                return self._peers[key]

        raise NodeUnavailableError(f"Remote node '{name}' is not registered in peer registry.")

    def contains(self, name: str) -> bool:
        """Check whether a peer node name exists in the registry."""
        key = name.strip().lower()
        with self._lock:
            return key in self._peers

    def list_peers(self) -> List[PeerNode]:
        """Return a list of all registered peer nodes."""
        with self._lock:
            return list(self._peers.values())

    def unregister_peer(self, name: str) -> Optional[PeerNode]:
        """Unregister a peer node by name."""
        key = name.strip().lower()
        with self._lock:
            return self._peers.pop(key, None)

    def clear(self) -> None:
        """Clear all registered peer nodes."""
        with self._lock:
            self._peers.clear()

    def load_from_dict(self, config_data: Dict[str, Any]) -> None:
        """Load peer configurations from a dictionary structure."""
        if not isinstance(config_data, dict):
            raise ValueError("Configuration data must be a dictionary.")

        peers_config = config_data.get("peers", {})
        if not isinstance(peers_config, dict):
            raise ValueError("'peers' section must be a dictionary.")

        for peer_name, peer_info in peers_config.items():
            if isinstance(peer_info, str):
                # Format: "192.168.1.50:8000"
                if ":" in peer_info:
                    host, port_str = peer_info.rsplit(":", 1)
                    port = int(port_str)
                else:
                    host, port = peer_info, 8765
            elif isinstance(peer_info, dict):
                host = str(peer_info.get("host", "127.0.0.1"))
                port = int(peer_info.get("port", 8765))
            else:
                raise ValueError(f"Invalid peer configuration format for '{peer_name}'.")

            peer = PeerNode(name=str(peer_name), host=host, port=port)
            self.register_peer(peer)

    def load_from_yaml(self, yaml_filepath: Union[str, Path]) -> None:
        """Load peer configurations from a YAML file."""
        path = Path(yaml_filepath).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Peer configuration file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in peer config file '{path}': {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Peer YAML file '{path}' must contain a root dictionary.")

        self.load_from_dict(data)
