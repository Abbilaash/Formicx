from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from formicx.enums.node_status import NodeStatus
from formicx.utils.ids import generate_node_id


class NodeResources(BaseModel):
    """Hardware resource specifications of a Formicx Node."""

    cpu_cores: int
    memory_mb: int

    @field_validator("cpu_cores")
    @classmethod
    def validate_cpu_cores(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("cpu_cores must be greater than zero.")
        return v

    @field_validator("memory_mb")
    @classmethod
    def validate_memory_mb(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("memory_mb must be greater than zero.")
        return v


class Node(BaseModel):
    """Represents a physical or virtual machine running Formicx."""

    node_id: str = Field(default_factory=generate_node_id)
    name: str
    architecture: str
    resources: NodeResources
    status: NodeStatus = NodeStatus.ONLINE

    @field_validator("name", "architecture")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or whitespace.")
        return stripped
