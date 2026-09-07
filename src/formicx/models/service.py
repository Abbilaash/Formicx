from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field, field_validator

from formicx.utils.ids import generate_service_id


class Service(BaseModel):
    """Represents a reusable capability integration provided through Formicx."""

    service_id: str = Field(default_factory=generate_service_id)
    name: str
    capabilities: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    status: str = "active"

    @field_validator("name", "status")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or whitespace.")
        return stripped
