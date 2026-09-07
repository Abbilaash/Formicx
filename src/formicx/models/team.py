from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from formicx.utils.ids import generate_team_id


class Team(BaseModel):
    """Represents a logical group of Formicx agents collaborating toward a goal."""

    team_id: str = Field(default_factory=generate_team_id)
    name: str
    goal: str
    members: List[str] = Field(default_factory=list)
    coordinator: Optional[str] = None

    @field_validator("name", "goal")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or whitespace.")
        return stripped

    @field_validator("members")
    @classmethod
    def validate_unique_members(cls, v: List[str]) -> List[str]:
        if len(v) != len(set(v)):
            raise ValueError("Team member agent IDs must be unique.")
        return v

    @model_validator(mode="after")
    def validate_coordinator_in_members(self) -> Team:
        if self.coordinator is not None:
            if self.coordinator not in self.members:
                raise ValueError(
                    f"Coordinator agent ID '{self.coordinator}' must exist within team members."
                )
        return self
