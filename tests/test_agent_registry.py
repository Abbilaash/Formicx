from __future__ import annotations

import pytest

from formicx.models.agent import Agent, AgentRuntime
from formicx.runtime.registry import AgentRegistry


def create_sample_agent(agent_id: str = "agt_1", name: str = "agent-1") -> Agent:
    return Agent(
        agent_id=agent_id,
        name=name,
        version="0.1.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
    )


def test_registry_register_and_get():
    registry = AgentRegistry()
    agent = create_sample_agent("agt_100", "researcher")

    registry.register(agent)
    assert registry.contains("agt_100")
    retrieved = registry.get("agt_100")
    assert retrieved.name == "researcher"


def test_registry_duplicate_registration_raises():
    registry = AgentRegistry()
    agent = create_sample_agent("agt_100", "researcher")

    registry.register(agent)
    with pytest.raises(ValueError):
        registry.register(agent)


def test_registry_get_unknown_raises():
    registry = AgentRegistry()
    with pytest.raises(KeyError):
        registry.get("agt_unknown")


def test_registry_list_agents():
    registry = AgentRegistry()
    a1 = create_sample_agent("agt_1", "one")
    a2 = create_sample_agent("agt_2", "two")

    registry.register(a1)
    registry.register(a2)

    agents = registry.list_agents()
    assert len(agents) == 2
    assert {a.agent_id for a in agents} == {"agt_1", "agt_2"}


def test_registry_unregister():
    registry = AgentRegistry()
    agent = create_sample_agent("agt_100", "worker")

    registry.register(agent)
    unregistered = registry.unregister("agt_100")

    assert unregistered.agent_id == "agt_100"
    assert not registry.contains("agt_100")

    with pytest.raises(KeyError):
        registry.unregister("agt_100")
