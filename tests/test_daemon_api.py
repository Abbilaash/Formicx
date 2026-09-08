from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from formicx.daemon.api import create_daemon_app
from formicx.runtime.manager import AgentManager


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def api_client(repo_root: Path):
    manager = AgentManager()
    app = create_daemon_app(manager)
    client = TestClient(app)
    try:
        yield client, manager, repo_root
    finally:
        manager.shutdown_all()


def test_api_health(api_client):
    client, _, _ = api_client
    response = client.get("/v1/health")
    assert response.status_code == 200
    res = response.json()
    assert res["status"] in ("ok", "healthy")
    assert res["daemon"] == "formicxd"
    assert res["node"] == "local"


def test_api_daemon_status(api_client):
    client, _, _ = api_client
    response = client.get("/v1/daemon/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["managed_agents"] == 0
    assert data["running_agents"] == 0


def test_api_register_list_start_stop_flow(api_client):
    client, manager, root = api_client
    hello_path = str(root / "agents" / "hello-agent")

    # Register
    res = client.post("/v1/agents/register", json={"path": hello_path})
    assert res.status_code == 201
    agent_data = res.json()
    assert agent_data["name"] == "hello-agent"
    agent_id = agent_data["agent_id"]

    # List
    res = client.get("/v1/agents")
    assert res.status_code == 200
    agents_list = res.json()
    assert len(agents_list) == 1
    assert agents_list[0]["agent_id"] == agent_id

    # Get Details by Name
    res = client.get("/v1/agents/hello-agent")
    assert res.status_code == 200
    assert res.json()["agent_id"] == agent_id

    # Start
    res = client.post(f"/v1/agents/{agent_id}/start")
    assert res.status_code == 200
    assert res.json()["status"] == "running"
    assert res.json()["pid"] is not None

    # Stop
    res = client.post(f"/v1/agents/{agent_id}/stop")
    assert res.status_code == 200
    assert res.json()["status"] == "stopped"


def test_api_register_invalid_path(api_client):
    client, _, _ = api_client
    res = client.post("/v1/agents/register", json={"path": "./invalid_dir"})
    assert res.status_code == 400
    assert "not found" in res.json()["detail"].lower()


def test_api_get_unknown_agent(api_client):
    client, _, _ = api_client
    res = client.get("/v1/agents/agt_unknown")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
