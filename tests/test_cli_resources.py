from unittest.mock import MagicMock
from typer.testing import CliRunner

from formicx.cli.commands.agent import agent_app

runner = CliRunner()


def test_cli_agent_resources_all(monkeypatch):
    mock_client = MagicMock()
    mock_client.get_all_resources.return_value = [
        {
            "agent_id": "agt_1",
            "agent_name": "research-agent",
            "pid": 1234,
            "status": "RUNNING",
            "cpu_percent": 14.2,
            "memory_bytes": 440401920,
            "memory_percent": 5.2,
            "thread_count": 8,
        },
        {
            "agent_id": "agt_2",
            "agent_name": "vision-agent",
            "pid": 1235,
            "status": "RUNNING",
            "cpu_percent": 62.8,
            "memory_bytes": 1288490188,
            "memory_percent": 15.0,
            "thread_count": 12,
        },
    ]
    monkeypatch.setattr("formicx.cli.commands.agent._get_client", lambda: mock_client)

    result = runner.invoke(agent_app, ["resources"])
    assert result.exit_code == 0
    assert "FORMICX AGENT RESOURCES" in result.output
    assert "research-agent" in result.output
    assert "1234" in result.output
    assert "420.0 MB" in result.output
    assert "1.20 GB" in result.output


def test_cli_agent_resources_single(monkeypatch):
    mock_client = MagicMock()
    mock_client.get_agent_resources.return_value = {
        "agent_id": "agt_1",
        "agent_name": "research-agent",
        "pid": 1234,
        "status": "RUNNING",
        "cpu_percent": 14.2,
        "memory_bytes": 440401920,
        "memory_percent": 5.2,
        "thread_count": 8,
    }
    monkeypatch.setattr("formicx.cli.commands.agent._get_client", lambda: mock_client)

    result = runner.invoke(agent_app, ["resources", "research-agent"])
    assert result.exit_code == 0
    assert "Agent: research-agent" in result.output
    assert "PID:\n1234" in result.output
    assert "CPU:\n14.2%" in result.output
    assert "420.0 MB" in result.output
    assert "Threads:\n8" in result.output
