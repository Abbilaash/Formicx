"""Agent Communication Policy engine and domain models for Formicx."""

from __future__ import annotations

import logging
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, field_validator
import yaml

from formicx.communication.discovery import AgentDiscoveryService
from formicx.communication.exceptions import AgentNotFoundError

logger = logging.getLogger("formicx.communication.policy")


class AgentCommunicationPolicy(BaseModel):
    """Domain model representing a directional communication policy for a source agent."""

    source_agent_id: str
    allowed_destinations: Set[str] = Field(default_factory=set)

    @field_validator("source_agent_id")
    @classmethod
    def validate_source(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("source_agent_id cannot be empty.")
        return stripped

    @field_validator("allowed_destinations", mode="before")
    @classmethod
    def normalize_destinations(cls, v: Any) -> Set[str]:
        if isinstance(v, list):
            return {str(item).strip() for item in v if str(item).strip()}
        if isinstance(v, set):
            return {str(item).strip() for item in v if str(item).strip()}
        if v is None:
            return set()
        raise ValueError("allowed_destinations must be a list or set of string agent identifiers.")


class CommunicationPolicyEngine:
    """Authoritative policy engine evaluating directional agent-to-agent communication permissions."""

    def __init__(
        self,
        discovery: Optional[AgentDiscoveryService] = None,
        default_policy: str = "allow",
    ) -> None:
        self._discovery = discovery
        self._default_policy = default_policy.lower()
        self._policies: Dict[str, AgentCommunicationPolicy] = {}
        self._lock = threading.Lock()

    def set_policy(
        self,
        source_identifier: str,
        allowed_destinations: Union[List[str], Set[str]],
    ) -> AgentCommunicationPolicy:
        """Configure an explicit communication policy for a source agent."""
        source_key = source_identifier.strip()
        if self._discovery is not None:
            try:
                resolved = self._discovery.resolve_agent(source_identifier)
                source_key = resolved.agent_id
            except AgentNotFoundError:
                pass

        dest_set = set(allowed_destinations)
        policy = AgentCommunicationPolicy(
            source_agent_id=source_key,
            allowed_destinations=dest_set,
        )

        with self._lock:
            self._policies[source_key] = policy
            # Also key by raw source_identifier if different
            if source_identifier != source_key:
                self._policies[source_identifier] = policy

        logger.info(f"Communication policy set for '{source_key}': allowed_destinations={dest_set}")
        return policy

    def get_policy(self, source_identifier: str) -> Optional[AgentCommunicationPolicy]:
        """Retrieve the configured policy for a source agent, if any."""
        with self._lock:
            if source_identifier in self._policies:
                return self._policies[source_identifier]

        if self._discovery is not None:
            try:
                resolved = self._discovery.resolve_agent(source_identifier)
                with self._lock:
                    return self._policies.get(resolved.agent_id) or self._policies.get(resolved.name)
            except AgentNotFoundError:
                pass

        return None

    def can_communicate(self, source_identifier: str, destination_identifier: str) -> bool:
        """Authoritatively evaluate whether source is permitted to communicate with destination.

        Args:
            source_identifier: Agent ID or name initiating communication.
            destination_identifier: Target Agent ID or name.

        Returns:
            True if communication is permitted, False if prohibited.
        """
        # Resolve canonical IDs and names if discovery service is available
        source_id = source_identifier
        source_name = source_identifier
        dest_id = destination_identifier
        dest_name = destination_identifier

        if self._discovery is not None:
            try:
                resolved_src = self._discovery.resolve_agent(source_identifier)
                source_id = resolved_src.agent_id
                source_name = resolved_src.name
            except AgentNotFoundError:
                pass

            try:
                resolved_dst = self._discovery.resolve_agent(destination_identifier)
                dest_id = resolved_dst.agent_id
                dest_name = resolved_dst.name
            except AgentNotFoundError:
                pass

        # Retrieve policy for source agent
        policy = self.get_policy(source_id) or self.get_policy(source_name)

        # Case 1: No explicit policy configured for source agent -> Default Open
        if policy is None:
            return self._default_policy == "allow"

        # Case 2/3: Policy configured -> Check if destination ID or name is explicitly allowed
        allowed = (dest_id in policy.allowed_destinations) or (dest_name in policy.allowed_destinations)
        return allowed

    def list_policies(self) -> Dict[str, AgentCommunicationPolicy]:
        """Return a copy of all loaded agent communication policies."""
        with self._lock:
            return dict(self._policies)

    def clear(self) -> None:
        """Clear all configured policies."""
        with self._lock:
            self._policies.clear()

    def load_from_dict(self, config_data: Dict[str, Any]) -> None:
        """Load communication policies from a dictionary configuration structure."""
        if not isinstance(config_data, dict):
            raise ValueError("Configuration data must be a dictionary.")

        comm_cfg = config_data.get("communication", {})
        if isinstance(comm_cfg, dict) and "default_policy" in comm_cfg:
            self._default_policy = str(comm_cfg["default_policy"]).lower()

        agent_policies = config_data.get("agent_policies", {})
        if not isinstance(agent_policies, dict):
            raise ValueError("'agent_policies' section must be a dictionary.")

        for source_name, policy_data in agent_policies.items():
            if not isinstance(policy_data, dict) or "allow" not in policy_data:
                raise ValueError(f"Policy for '{source_name}' must be a dict containing an 'allow' list.")

            allow_list = policy_data["allow"]
            if not isinstance(allow_list, list):
                raise ValueError(f"'allow' field for '{source_name}' must be a list of agent identifiers.")

            self.set_policy(source_name, allow_list)

    def load_from_yaml(self, yaml_filepath: Union[str, Path]) -> None:
        """Load communication policies from a YAML file."""
        path = Path(yaml_filepath).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Policy configuration file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in policy file '{path}': {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Policy YAML file '{path}' must contain a root dictionary.")

        self.load_from_dict(data)
