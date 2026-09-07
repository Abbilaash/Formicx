from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import httpx

from formicx.client.daemon_client import (
    DaemonAPIError,
    DaemonClient,
    DaemonUnavailableError,
)
from formicx.daemon.api import create_daemon_app
from formicx.runtime.manager import AgentManager


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_daemon_client_with_testclient(repo_root: Path):
    manager = AgentManager()
    app = create_daemon_app(manager)

    # Use FastAPI TestClient transport to test DaemonClient logic
    with TestClient(app) as test_client:
        client = DaemonClient(base_url="http://testserver", http_client=test_client)

        # Health
        health_data = client.health()
        assert health_data["status"] == "ok"

        # Register
        hello_dir = repo_root / "agents" / "hello-agent"
        reg_data = client.register_agent(hello_dir)
        assert reg_data["name"] == "hello-agent"
        agent_id = reg_data["agent_id"]

        # List
        agents = client.list_agents()
        assert len(agents) == 1

        # Get
        details = client.get_agent(agent_id)
        assert details["name"] == "hello-agent"


def test_daemon_client_unavailable():
    # Connect to invalid port where no server is running
    client = DaemonClient(base_url="http://127.0.0.1:59999", timeout=1.0)
    with pytest.raises(DaemonUnavailableError) as exc_info:
        client.health()

    assert "Unable to connect to formicxd" in str(exc_info.value)


def test_daemon_client_api_error(repo_root: Path):
    manager = AgentManager()
    app = create_daemon_app(manager)

    with TestClient(app) as test_client:
        client = DaemonClient(base_url="http://testserver", http_client=test_client)

        with pytest.raises(DaemonAPIError) as exc_info:
            client.get_agent("non_existent_agent")

        assert "not found" in str(exc_info.value).lower()
