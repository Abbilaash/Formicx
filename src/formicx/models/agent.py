from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from formicx.enums.agent_status import AgentStatus
from formicx.utils.ids import generate_agent_id


class AgentRuntime(BaseModel):
    """Runtime environment details for an Agent."""

    language: str
    framework: str = "custom"

    @field_validator("language", "framework")
    @classmethod
    def validate_non_empty_strings(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or whitespace.")
        return stripped


class Agent(BaseModel):
    """Represents an independently executable, identifiable, and manageable autonomous AI Agent."""

    agent_id: str = Field(default_factory=generate_agent_id)
    name: str
    version: str
    runtime: AgentRuntime
    entrypoint: str
    status: AgentStatus = AgentStatus.CREATED
    capabilities: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    node_id: Optional[str] = None

    @field_validator("name", "version", "entrypoint")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or whitespace.")
        return stripped
