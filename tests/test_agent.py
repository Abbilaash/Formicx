from __future__ import annotations

import pytest
from pydantic import ValidationError

from formicx.models import Agent, AgentRuntime
from formicx.enums import AgentStatus


def test_agent_creation_defaults():
    agent = Agent(
        name="researcher",
        version="0.1.0",
        runtime=AgentRuntime(language="python", framework="langgraph"),
        entrypoint="main.py",
    )

    assert agent.agent_id.startswith("agt_")
    assert agent.name == "researcher"
    assert agent.version == "0.1.0"
    assert agent.status == AgentStatus.CREATED
    assert agent.capabilities == []
    assert agent.permissions == []
    assert agent.node_id is None
    assert agent.started_at is None


def test_agent_explicit_id_and_fields():
    agent = Agent(
        agent_id="agt_custom123",
        name="developer",
        version="1.0.0",
        runtime=AgentRuntime(language="python", framework="custom"),
        entrypoint="app.py",
        status=AgentStatus.RUNNING,
        capabilities=["coding"],
        permissions=["network.internet"],
        node_id="node_local",
    )

    assert agent.agent_id == "agt_custom123"
    assert agent.status == AgentStatus.RUNNING
    assert agent.capabilities == ["coding"]
    assert agent.permissions == ["network.internet"]
    assert agent.node_id == "node_local"


def test_agent_invalid_empty_name():
    with pytest.raises(ValidationError):
        Agent(
            name="",
            version="0.1.0",
            runtime=AgentRuntime(language="python"),
            entrypoint="main.py",
        )


def test_agent_invalid_empty_entrypoint():
    with pytest.raises(ValidationError):
        Agent(
            name="test",
            version="0.1.0",
            runtime=AgentRuntime(language="python"),
            entrypoint="   ",
        )


def test_agent_runtime_invalid_empty_language():
    with pytest.raises(ValidationError):
        AgentRuntime(language="")


def test_agent_serialization():
    agent = Agent(
        name="researcher",
        version="0.1.0",
        runtime=AgentRuntime(language="python", framework="openai"),
        entrypoint="main.py",
        capabilities=["research"],
    )

    data = agent.model_dump()
    assert data["name"] == "researcher"
    assert data["runtime"]["framework"] == "openai"
    assert data["status"] == "created"

    json_str = agent.model_dump_json()
    assert "researcher" in json_str

    deserialized = Agent.model_validate_json(json_str)
    assert deserialized.agent_id == agent.agent_id
    assert deserialized.runtime.framework == "openai"
    assert deserialized.status == AgentStatus.CREATED
