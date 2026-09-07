from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from formicx.cli.main import app as cli_app
from formicx.client.daemon_client import DaemonClient
from formicx.daemon.api import create_daemon_app
from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent, AgentRuntime
from formicx.runtime.manager import AgentManager

runner = CliRunner()


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def mock_daemon(monkeypatch, repo_root: Path):
    manager = AgentManager()
    agent_a = Agent(
        agent_id="agt_001",
        name="coordinator-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    agent_b = Agent(
        agent_id="agt_002",
        name="research-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    manager.register_agent(agent_a)
    manager.register_agent(agent_b)

    fastapi_app = create_daemon_app(manager)
    test_client = TestClient(fastapi_app)

    monkeypatch.setattr(DaemonClient, "_get_client", lambda self: test_client)

    try:
        yield manager
    finally:
        manager.shutdown_all()


def test_cli_message_help():
    res = runner.invoke(cli_app, ["message", "--help"])
    assert res.exit_code == 0
    assert "Debug and inspect Formicx agent messages." in res.stdout


def test_cli_message_send_success(mock_daemon):
    res = runner.invoke(
        cli_app,
        [
            "message",
            "send",
            "coordinator-agent",
            "research-agent",
            '{"question": "What is 2+2?"}',
        ],
    )
    assert res.exit_code == 0
    assert "Message delivered successfully" in res.stdout
    assert "From: coordinator-agent" in res.stdout
    assert "To: research-agent" in res.stdout


def test_cli_message_send_single_quoted_json(mock_daemon):
    # Simulates Windows CMD passing literal single quotes surrounding JSON argument
    res = runner.invoke(
        cli_app,
        [
            "message",
            "send",
            "coordinator-agent",
            "research-agent",
            '\'{"question": "What is 2+2?"}\'',
        ],
    )
    assert res.exit_code == 0
    assert "Message delivered successfully" in res.stdout


def test_cli_message_send_cmd_unquoted_keys(mock_daemon):
    # Simulates Windows CMD stripping double quotes leaving unquoted or single quoted keys
    res = runner.invoke(
        cli_app,
        [
            "message",
            "send",
            "coordinator-agent",
            "research-agent",
            "'{question: What is 2+2?}'",
        ],
    )
    assert res.exit_code == 0
    assert "Message delivered successfully" in res.stdout


def test_cli_message_send_invalid_json(mock_daemon):
    res = runner.invoke(
        cli_app,
        [
            "message",
            "send",
            "coordinator-agent",
            "research-agent",
            "not_valid_json",
        ],
    )
    assert res.exit_code == 1
    assert "Invalid JSON payload" in res.output


def test_cli_message_inbox_and_history(mock_daemon):
    # Send a message first
    runner.invoke(
        cli_app,
        [
            "message",
            "send",
            "coordinator-agent",
            "research-agent",
            '{"question": "What is 2+2?"}',
        ],
    )

    # Check inbox
    res_inbox = runner.invoke(cli_app, ["message", "inbox", "research-agent"])
    assert res_inbox.exit_code == 0
    assert "agt_001" in res_inbox.stdout
    assert "REQUEST" in res_inbox.stdout

    # Check history
    res_history = runner.invoke(cli_app, ["message", "history", "research-agent"])
    assert res_history.exit_code == 0
    assert "agt_001" in res_history.stdout
