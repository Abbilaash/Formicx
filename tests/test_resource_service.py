import pytest

from formicx.communication.exceptions import AgentNotFoundError
from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent, AgentRuntime
from formicx.resources.service import ResourceService
from formicx.runtime.manager import AgentManager


def test_resource_service_sample_and_lookup():
    manager = AgentManager()
    agent = Agent(
        agent_id="agt_res_1",
        name="research-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.STOPPED,
    )
    manager.register_agent(agent)

    service = ResourceService(agent_manager=manager, enabled=True)
    all_res = service.get_all_resources()

    assert len(all_res) == 1
    assert all_res[0].agent_id == "agt_res_1"
    assert all_res[0].status == "STOPPED"

    # Query by ID
    res_by_id = service.get_agent_resources("agt_res_1")
    assert res_by_id.agent_name == "research-agent"

    # Query by Name
    res_by_name = service.get_agent_resources("research-agent")
    assert res_by_name.agent_id == "agt_res_1"

    # Unknown agent
    with pytest.raises(AgentNotFoundError):
        service.get_agent_resources("unknown-agent")
