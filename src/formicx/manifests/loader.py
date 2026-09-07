from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml

from formicx.models.agent import Agent, AgentRuntime


def load_agent_manifest(manifest_path: str | Path) -> Agent:
    """Load an Agent definition from a YAML manifest file.

    Args:
        manifest_path: Path to the agent.yaml manifest file.

    Returns:
        Formicx Agent model populated with manifest configuration.

    Raises:
        FileNotFoundError: If the manifest file or entrypoint file does not exist.
        ValueError: If manifest content is invalid YAML, missing required fields, or malformed.
    """
    path = Path(manifest_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML content in manifest '{path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Manifest at '{path}' must contain a valid YAML dictionary.")

    # Validate required top-level fields
    required_fields = ["name", "version", "entrypoint", "runtime"]
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        raise ValueError(f"Manifest '{path}' is missing required fields: {', '.join(missing)}")

    raw_runtime = data["runtime"]
    if not isinstance(raw_runtime, dict) or "language" not in raw_runtime:
        raise ValueError(f"Manifest '{path}' runtime field must be a dict containing 'language'.")

    runtime = AgentRuntime(
        language=str(raw_runtime.get("language", "")),
        framework=str(raw_runtime.get("framework", "custom")),
    )

    # Resolve entrypoint relative to agent.yaml directory
    manifest_dir = path.parent
    entrypoint_rel = str(data["entrypoint"]).strip()
    if not entrypoint_rel:
        raise ValueError(f"Manifest '{path}' entrypoint field cannot be empty.")

    entrypoint_path = (manifest_dir / entrypoint_rel).resolve()
    if not entrypoint_path.exists():
        raise FileNotFoundError(
            f"Entrypoint script '{entrypoint_rel}' resolved to '{entrypoint_path}' does not exist."
        )

    agent_kwargs: Dict[str, Any] = {
        "name": str(data["name"]),
        "version": str(data["version"]),
        "runtime": runtime,
        "entrypoint": str(entrypoint_path),
        "capabilities": data.get("capabilities", []),
        "permissions": data.get("permissions", []),
    }

    if "agent_id" in data and data["agent_id"]:
        agent_kwargs["agent_id"] = str(data["agent_id"])

    if "node_id" in data and data["node_id"]:
        agent_kwargs["node_id"] = str(data["node_id"])

    return Agent(**agent_kwargs)
