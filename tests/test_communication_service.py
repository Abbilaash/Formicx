import pytest
from formicx.enums.agent_status import AgentStatus
from formicx.enums.message_type import MessageType
from formicx.models.agent import Agent, AgentRuntime
from formicx.models.message import Message
from formicx.runtime.registry import AgentRegistry
from formicx.communication.service import CommunicationService


@pytest.fixture
def comm_service():
    registry = AgentRegistry()
    agt_a = Agent(
        agent_id="agt_001",
        name="agent-a",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    agt_b = Agent(
        agent_id="agt_002",
        name="agent-b",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    registry.register(agt_a)
    registry.register(agt_b)
    return CommunicationService(registry=registry)


def test_comm_service_send_and_receive(comm_service):
    msg = Message(
        sender="agent-a",
        recipient="agent-b",
        message_type=MessageType.REQUEST,
        payload={"query": "test"},
    )
    res = comm_service.send_message(msg)
    assert res["status"] == "DELIVERED"
    assert res["recipient_agent_id"] == "agt_002"

    # Peek inbox
    pending = comm_service.peek_inbox("agent-b")
    assert len(pending) == 1
    assert pending[0].payload == {"query": "test"}

    # Receive next
    received = comm_service.receive_next("agent-b")
    assert received is not None
    assert received.sender == "agt_001"
    assert received.recipient == "agt_002"

    # Subsequent receive returns None
    assert comm_service.receive_next("agent-b", timeout=0.01) is None


def test_comm_service_discover(comm_service):
    agents = comm_service.discover_agents()
    assert len(agents) == 2

    running_agents = comm_service.discover_agents(status="RUNNING")
    assert len(running_agents) == 2

    stopped_agents = comm_service.discover_agents(status="STOPPED")
    assert len(stopped_agents) == 0


def test_comm_service_broadcast(comm_service):
    recipients = comm_service.broadcast(
        sender_identifier="agent-a",
        message_type=MessageType.EVENT,
        payload={"notice": "all"},
    )
    assert recipients == ["agt_002"]

    msg = comm_service.receive_next("agent-b")
    assert msg.payload == {"notice": "all"}
