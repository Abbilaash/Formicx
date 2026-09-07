from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from formicx.cli.main import app as cli_app
from formicx.client.daemon_client import DaemonClient
from formicx.daemon.api import create_daemon_app
from formicx.runtime.manager import AgentManager

runner = CliRunner()


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def mock_daemon(monkeypatch, repo_root: Path):
    manager = AgentManager()
    fastapi_app = create_daemon_app(manager)
    test_client = TestClient(fastapi_app)

    # Patch DaemonClient._get_client in commands to route to test_client
    monkeypatch.setattr(DaemonClient, "_get_client", lambda self: test_client)

    try:
        yield manager, repo_root
    finally:
        manager.shutdown_all()


def test_cli_agent_register_and_list(mock_daemon):
    _, root = mock_daemon
    hello_path = str(root / "agents" / "hello-agent")

    # Register
    res = runner.invoke(cli_app, ["agent", "register", hello_path])
    assert res.exit_code == 0
    assert "Agent registered successfully" in res.stdout
    assert "hello-agent" in res.stdout

    # List
    res = runner.invoke(cli_app, ["agent", "list"])
    assert res.exit_code == 0
    assert "hello-agent" in res.stdout
    assert "CREATED" in res.stdout


def test_cli_agent_start_status_stop_flow(mock_daemon):
    _, root = mock_daemon
    hello_path = str(root / "agents" / "hello-agent")

    runner.invoke(cli_app, ["agent", "register", hello_path])

    # Start
    res = runner.invoke(cli_app, ["agent", "start", "hello-agent"])
    assert res.exit_code == 0
    assert "Agent started successfully" in res.stdout
    assert "RUNNING" in res.stdout

    # Status
    res = runner.invoke(cli_app, ["agent", "status", "hello-agent"])
    assert res.exit_code == 0
    assert "hello-agent" in res.stdout
    assert "RUNNING" in res.stdout

    # Restart
    res = runner.invoke(cli_app, ["agent", "restart", "hello-agent"])
    assert res.exit_code == 0
    assert "Agent restarted successfully" in res.stdout

    # Stop
    res = runner.invoke(cli_app, ["agent", "stop", "hello-agent"])
    assert res.exit_code == 0
    assert "Agent stopped successfully" in res.stdout
    assert "STOPPED" in res.stdout


def test_cli_agent_unknown_agent_error():
    # Calling client to unreachable daemon or unmapped agent
    res = runner.invoke(cli_app, ["agent", "start", "agt_unknown"])
    assert res.exit_code == 1
    assert "Error:" in res.stdout or "Error:" in res.stderr
    assert "Traceback" not in res.stdout
