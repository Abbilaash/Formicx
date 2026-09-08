from unittest.mock import MagicMock
from typer.testing import CliRunner

from formicx.cli.commands.node import node_app, get_client

runner = CliRunner()


def test_cli_node_info_with_discovery(monkeypatch):
    mock_client = MagicMock()
    mock_client.get_node_info.return_value = {
        "name": "laptop",
        "host": "127.0.0.1",
        "port": 8765,
        "status": "ONLINE",
        "discovery_enabled": True,
        "discovery_port": 9999,
        "peer_count": 2,
    }
    monkeypatch.setattr("formicx.cli.commands.node.get_client", lambda: mock_client)

    result = runner.invoke(node_app, ["info"])
    assert result.exit_code == 0
    assert "laptop" in result.output
    assert "enabled" in result.output
    assert "9999" in result.output


def test_cli_node_discover(monkeypatch):
    mock_client = MagicMock()
    mock_client.trigger_discovery.return_value = {
        "status": "DISCOVERY_TRIGGERED",
        "node": "laptop",
    }
    mock_client.list_peers.return_value = [
        {"name": "raspberry-pi", "host": "192.168.1.50", "port": 8000, "source": "discovered", "status": "ONLINE"}
    ]
    monkeypatch.setattr("formicx.cli.commands.node.get_client", lambda: mock_client)

    result = runner.invoke(node_app, ["discover"])
    assert result.exit_code == 0
    assert "Discovery request sent successfully" in result.output
    assert "raspberry-pi" in result.output
