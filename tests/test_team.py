from __future__ import annotations

import pytest
from pydantic import ValidationError

from formicx import Team


def test_team_creation_valid():
    team = Team(
        name="startup-team",
        goal="Build product MVP",
        members=["agt_1", "agt_2", "agt_3"],
        coordinator="agt_1",
    )

    assert team.team_id.startswith("team_")
    assert team.name == "startup-team"
    assert team.goal == "Build product MVP"
    assert team.members == ["agt_1", "agt_2", "agt_3"]
    assert team.coordinator == "agt_1"


def test_team_without_coordinator():
    team = Team(
        name="peer-team",
        goal="Collab",
        members=["agt_1", "agt_2"],
    )

    assert team.coordinator is None


def test_team_invalid_empty_name_or_goal():
    with pytest.raises(ValidationError):
        Team(name="", goal="Goal", members=["agt_1"])

    with pytest.raises(ValidationError):
        Team(name="Team", goal="  ", members=["agt_1"])


def test_team_invalid_duplicate_members():
    with pytest.raises(ValidationError):
        Team(
            name="Team",
            goal="Goal",
            members=["agt_1", "agt_2", "agt_1"],
        )


def test_team_invalid_coordinator_not_in_members():
    with pytest.raises(ValidationError):
        Team(
            name="Team",
            goal="Goal",
            members=["agt_1", "agt_2"],
            coordinator="agt_unknown",
        )


def test_team_serialization():
    team = Team(
        name="dev-ops",
        goal="Maintain infrastructure",
        members=["agt_sys", "agt_monitor"],
        coordinator="agt_sys",
    )

    json_str = team.model_dump_json()
    assert "dev-ops" in json_str

    deserialized = Team.model_validate_json(json_str)
    assert deserialized.team_id == team.team_id
    assert deserialized.coordinator == "agt_sys"
