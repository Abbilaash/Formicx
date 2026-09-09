from fastapi.testclient import TestClient
import pytest

from formicx.daemon.api import create_daemon_app
from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent, AgentRuntime
from formicx.resources.service import ResourceService
from formicx.runtime.manager import AgentManager


def test_daemon_resource_api_endpoints():
    manager = AgentManager()
    agt = Agent(
        agent_id="agt_res_api_1",
        name="mail-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.STOPPED,
    )
    manager.register_agent(agt)

    resource_service = ResourceService(agent_manager=manager)
    app = create_daemon_app(manager, resource_service=resource_service)
    client = TestClient(app)

    # Test GET /v1/resources
    resp = client.get("/v1/resources")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["agent_id"] == "agt_res_api_1"
    assert data[0]["agent_name"] == "mail-agent"

    # Test GET /v1/agents/{identifier}/resources
    resp_single = client.get("/v1/agents/mail-agent/resources")
    assert resp_single.status_code == 200
    single_data = resp_single.json()
    assert single_data["agent_id"] == "agt_res_api_1"
    assert single_data["status"] == "STOPPED"

    # Test GET /v1/agents/unknown/resources
    resp_404 = client.get("/v1/agents/unknown-agent/resources")
    assert resp_404.status_code == 404
