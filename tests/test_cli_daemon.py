from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from formicx.cli.main import app as cli_app
from formicx.client.daemon_client import DaemonClient
from formicx.daemon.api import create_daemon_app
from formicx.runtime.manager import AgentManager

runner = CliRunner()


@pytest.fixture
def mock_daemon(monkeypatch):
    manager = AgentManager()
    fastapi_app = create_daemon_app(manager)
    test_client = TestClient(fastapi_app)

    monkeypatch.setattr(DaemonClient, "_get_client", lambda self: test_client)

    try:
        yield manager
    finally:
        manager.shutdown_all()


def test_cli_daemon_health(mock_daemon):
    res = runner.invoke(cli_app, ["daemon", "health"])
    assert res.exit_code == 0
    assert "formicxd is running and reachable." in res.stdout


def test_cli_daemon_status(mock_daemon):
    res = runner.invoke(cli_app, ["daemon", "status"])
    assert res.exit_code == 0
    assert "Formicx Daemon" in res.stdout
    assert "Status: RUNNING" in res.stdout
    assert "Managed Agents: 0" in res.stdout
