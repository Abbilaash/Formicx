import pytest
from formicx.resources.models import AgentResourceUsage


def test_agent_resource_usage_model_defaults():
    usage = AgentResourceUsage(
        agent_id="agt_123",
        agent_name="research-agent",
    )

    assert usage.agent_id == "agt_123"
    assert usage.agent_name == "research-agent"
    assert usage.pid is None
    assert usage.status == "STOPPED"
    assert usage.cpu_percent == 0.0
    assert usage.memory_bytes == 0
    assert usage.memory_percent == 0.0
    assert usage.thread_count == 0
    assert usage.is_active is False
    assert usage.last_sampled_at is not None


def test_agent_resource_usage_active_property():
    active_usage = AgentResourceUsage(
        agent_id="agt_456",
        agent_name="vision-agent",
        pid=1234,
        status="RUNNING",
        cpu_percent=15.5,
        memory_bytes=420000000,
        memory_percent=5.2,
        thread_count=4,
    )

    assert active_usage.is_active is True
    assert active_usage.pid == 1234
    assert active_usage.cpu_percent == 15.5
