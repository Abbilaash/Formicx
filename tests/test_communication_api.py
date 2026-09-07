from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from formicx.daemon.api import create_daemon_app
from formicx.enums.agent_status import AgentStatus
from formicx.enums.message_type import MessageType
from formicx.models.agent import Agent, AgentRuntime
from formicx.runtime.manager import AgentManager


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def comm_api_client(repo_root: Path):
    manager = AgentManager()
    agent_a = Agent(
        agent_id="agt_001",
        name="sender-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    agent_b = Agent(
        agent_id="agt_002",
        name="recipient-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    manager.register_agent(agent_a)
    manager.register_agent(agent_b)

    app = create_daemon_app(manager)
    client = TestClient(app)
    try:
        yield client, manager
    finally:
        manager.shutdown_all()


def test_api_send_and_receive_next(comm_api_client):
    client, _ = comm_api_client

    # Send message
    msg_data = {
        "sender": "sender-agent",
        "recipient": "recipient-agent",
        "message_type": "REQUEST",
        "payload": {"query": "hello daemon"},
    }
    res = client.post("/v1/messages", json=msg_data)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "DELIVERED"
    assert res_data["recipient_agent_id"] == "agt_002"

    # Peek inbox
    res_peek = client.get("/v1/agents/recipient-agent/messages")
    assert res_peek.status_code == 200
    pending = res_peek.json()
    assert len(pending) == 1
    assert pending[0]["sender"] == "agt_001"

    # Receive next
    res_next = client.get("/v1/agents/recipient-agent/messages/next")
    assert res_next.status_code == 200
    msg = res_next.json()
    assert msg["sender"] == "agt_001"
    assert msg["recipient"] == "agt_002"

    # Receive next again returns 204
    res_empty = client.get("/v1/agents/recipient-agent/messages/next?timeout=0.01")
    assert res_empty.status_code == 204


def test_api_broadcast(comm_api_client):
    client, _ = comm_api_client

    bcast_data = {
        "from_agent_id": "sender-agent",
        "message_type": "EVENT",
        "payload": {"event": "shutdown_notice"},
    }
    res = client.post("/v1/messages/broadcast", json=bcast_data)
    assert res.status_code == 200
    recipients = res.json()["recipients"]
    assert recipients == ["agt_002"]


def test_api_send_unknown_recipient(comm_api_client):
    client, _ = comm_api_client

    msg_data = {
        "sender": "sender-agent",
        "recipient": "non-existent-agent",
        "message_type": "REQUEST",
        "payload": {},
    }
    res = client.post("/v1/messages", json=msg_data)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
