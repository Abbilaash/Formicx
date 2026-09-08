from unittest.mock import patch
from typer.testing import CliRunner

from formicx.cli.main import app
from formicx.client.daemon_client import DaemonAPIError

runner = CliRunner()


@patch("formicx.cli.commands.node.get_client")
def test_cli_node_info(mock_get_client):
    mock_client = mock_get_client.return_value
    mock_client.get_node_info.return_value = {
        "name": "laptop",
        "host": "0.0.0.0",
        "port": 8765,
        "status": "ONLINE",
    }

    result = runner.invoke(app, ["node", "info"])
    assert result.exit_code == 0
    assert "laptop" in result.stdout
    assert "8765" in result.stdout


@patch("formicx.cli.commands.node.get_client")
def test_cli_node_peers_empty(mock_get_client):
    mock_client = mock_get_client.return_value
    mock_client.list_peers.return_value = []

    result = runner.invoke(app, ["node", "peers"])
    assert result.exit_code == 0
    assert "No registered peer nodes" in result.stdout


@patch("formicx.cli.commands.node.get_client")
def test_cli_node_peers_list(mock_get_client):
    mock_client = mock_get_client.return_value
    mock_client.list_peers.return_value = [
        {"name": "raspberry-pi", "host": "192.168.1.50", "port": 8000, "status": "ONLINE"}
    ]

    result = runner.invoke(app, ["node", "peers"])
    assert result.exit_code == 0
    assert "raspberry-pi" in result.stdout
    assert "192.168.1.50" in result.stdout


@patch("formicx.cli.commands.node.get_client")
def test_cli_node_ping_success(mock_get_client):
    mock_client = mock_get_client.return_value
    mock_client.ping_peer.return_value = {
        "status": "ONLINE",
        "peer": "raspberry-pi",
        "host": "192.168.1.50",
        "port": 8000,
        "latency_ms": 3.45,
    }

    result = runner.invoke(app, ["node", "ping", "raspberry-pi"])
    assert result.exit_code == 0
    assert "ONLINE" in result.stdout
    assert "raspberry-pi" in result.stdout
    assert "3.45 ms" in result.stdout


@patch("formicx.cli.commands.node.get_client")
def test_cli_node_ping_error(mock_get_client):
    mock_client = mock_get_client.return_value
    mock_client.ping_peer.side_effect = DaemonAPIError("Remote node 'raspberry-pi' is not registered")

    result = runner.invoke(app, ["node", "ping", "raspberry-pi"])
    assert result.exit_code == 1
    assert "Ping failed" in result.stdout
