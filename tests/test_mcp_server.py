"""Unit tests for Formicx Model Context Protocol (MCP) Server."""

import json
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from formicx.cli.main import app
from formicx.mcp.server import FormicxMCPServer, TOOL_DEFINITIONS

runner = CliRunner()


@pytest.fixture
def mock_daemon_client():
    client = MagicMock()
    client.list_agents.return_value = [
        {"agent_id": "agt_001", "name": "calc-agent", "status": "RUNNING", "pid": 1234}
    ]
    client.register_agent.return_value = {
        "agent_id": "agt_002",
        "name": "worker-agent",
        "status": "CREATED",
    }
    client.start_agent.return_value = {"agent_id": "agt_001", "status": "RUNNING"}
    client.stop_agent.return_value = {"agent_id": "agt_001", "status": "STOPPED"}
    client.send_message.return_value = {"message_id": "msg_123", "status": "DELIVERED"}
    client.get_inbox.return_value = [{"message_id": "msg_123", "payload": {"result": 42}}]
    client.daemon_status.return_value = {"status": "RUNNING", "managed_agents": 1}
    return client


def test_mcp_initialize(mock_daemon_client):
    server = FormicxMCPServer(daemon_client=mock_daemon_client)
    res = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert res is not None
    assert res["id"] == 1
    assert res["result"]["serverInfo"]["name"] == "formicx-mcp"
    assert "tools" in res["result"]["capabilities"]


def test_mcp_tools_list(mock_daemon_client):
    server = FormicxMCPServer(daemon_client=mock_daemon_client)
    res = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert res is not None
    tools = res["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "formicx_list_agents" in tool_names
    assert "formicx_send_message" in tool_names
    assert "formicx_register_agent" in tool_names


def test_mcp_tools_call_list_agents(mock_daemon_client):
    server = FormicxMCPServer(daemon_client=mock_daemon_client)
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "formicx_list_agents", "arguments": {}},
    }
    res = server.handle_request(req)
    assert res is not None
    content = json.loads(res["result"]["content"][0]["text"])
    assert len(content) == 1
    assert content[0]["name"] == "calc-agent"
    mock_daemon_client.list_agents.assert_called_once()


def test_mcp_tools_call_send_message(mock_daemon_client):
    server = FormicxMCPServer(daemon_client=mock_daemon_client)
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "formicx_send_message",
            "arguments": {
                "sender": "calc-agent",
                "recipient": "calc-agent",
                "payload": {"action": "add", "a": 5, "b": 10},
            },
        },
    }
    res = server.handle_request(req)
    assert res is not None
    content = json.loads(res["result"]["content"][0]["text"])
    assert content["status"] == "DELIVERED"
    mock_daemon_client.send_message.assert_called_once_with(
        sender="calc-agent",
        recipient="calc-agent",
        message_type="REQUEST",
        payload={"action": "add", "a": 5, "b": 10},
        correlation_id=None,
    )


def test_cli_mcp_tools():
    result = runner.invoke(app, ["mcp", "tools"])
    assert result.exit_code == 0
    assert "Available Formicx MCP Tools" in result.stdout
    assert "formicx_list_agents" in result.stdout
    assert "formicx_get_documentation" in result.stdout


def test_mcp_get_documentation_tool(mock_daemon_client):
    server = FormicxMCPServer(daemon_client=mock_daemon_client)
    req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "formicx_get_documentation",
            "arguments": {"topic": "sdk"},
        },
    }
    res = server.handle_request(req)
    assert res is not None
    text = res["result"]["content"][0]["text"]
    assert "Formicx Agent SDK Reference" in text


def test_mcp_resources_list(mock_daemon_client):
    server = FormicxMCPServer(daemon_client=mock_daemon_client)
    res = server.handle_request({"jsonrpc": "2.0", "id": 6, "method": "resources/list"})
    assert res is not None
    resources = res["result"]["resources"]
    uris = [r["uri"] for r in resources]
    assert "formicx://docs/overview" in uris
    assert "formicx://docs/sdk" in uris


def test_mcp_resources_read(mock_daemon_client):
    server = FormicxMCPServer(daemon_client=mock_daemon_client)
    req = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "resources/read",
        "params": {"uri": "formicx://docs/overview"},
    }
    res = server.handle_request(req)
    assert res is not None
    content = res["result"]["contents"][0]["text"]
    assert "Formicx Overview" in content


def test_mcp_prompts_get(mock_daemon_client):
    server = FormicxMCPServer(daemon_client=mock_daemon_client)
    res = server.handle_request({"jsonrpc": "2.0", "id": 8, "method": "prompts/get"})
    assert res is not None
    msg_text = res["result"]["messages"][0]["content"]["text"]
    assert "Formicx" in msg_text

