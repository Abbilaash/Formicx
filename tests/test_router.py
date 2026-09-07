import pytest
from formicx.enums.agent_status import AgentStatus
from formicx.enums.message_type import MessageType
from formicx.models.agent import Agent, AgentRuntime
from formicx.models.message import Message
from formicx.runtime.registry import AgentRegistry
from formicx.communication.discovery import AgentDiscoveryService
from formicx.communication.exceptions import AgentNotFoundError, AmbiguousAgentError
from formicx.communication.router import MessageRouter


@pytest.fixture
def sample_registry():
    registry = AgentRegistry()
    agent_a = Agent(
        agent_id="agt_001",
        name="worker-a",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    agent_b = Agent(
        agent_id="agt_002",
        name="worker-b",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    agent_c1 = Agent(
        agent_id="agt_003",
        name="duplicate-name",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.STOPPED,
    )
    agent_c2 = Agent(
        agent_id="agt_004",
        name="duplicate-name",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.STOPPED,
    )

    registry.register(agent_a)
    registry.register(agent_b)
    registry.register(agent_c1)
    registry.register(agent_c2)
    return registry


def test_route_successful_by_id_and_name(sample_registry):
    discovery = AgentDiscoveryService(sample_registry)
    router = MessageRouter(discovery)

    msg = Message(
        sender="agt_001",
        recipient="worker-b",
        message_type=MessageType.REQUEST,
        payload={"query": "ping"},
    )
    recipient_id = router.route(msg)
    assert recipient_id == "agt_002"

    inbox = router.get_or_create_inbox("agt_002")
    assert inbox.pending_count == 1
    received = inbox.receive_next()
    assert received.sender == "agt_001"
    assert received.recipient == "agt_002"


def test_route_unknown_sender(sample_registry):
    discovery = AgentDiscoveryService(sample_registry)
    router = MessageRouter(discovery)

    msg = Message(
        sender="unknown_sender",
        recipient="worker-b",
        message_type=MessageType.REQUEST,
    )
    with pytest.raises(AgentNotFoundError, match="Sender agent not found"):
        router.route(msg)


def test_route_unknown_recipient(sample_registry):
    discovery = AgentDiscoveryService(sample_registry)
    router = MessageRouter(discovery)

    msg = Message(
        sender="agt_001",
        recipient="non_existent_recipient",
        message_type=MessageType.REQUEST,
    )
    with pytest.raises(AgentNotFoundError, match="Agent not found"):
        router.route(msg)


def test_route_ambiguous_name(sample_registry):
    discovery = AgentDiscoveryService(sample_registry)
    router = MessageRouter(discovery)

    msg = Message(
        sender="agt_001",
        recipient="duplicate-name",
        message_type=MessageType.REQUEST,
    )
    with pytest.raises(AmbiguousAgentError, match="Multiple agents named"):
        router.route(msg)


def test_broadcast(sample_registry):
    discovery = AgentDiscoveryService(sample_registry)
    router = MessageRouter(discovery)

    recipients = router.broadcast(
        sender_identifier="worker-a",
        message_type=MessageType.EVENT,
        payload={"event": "announcement"},
    )
    assert set(recipients) == {"agt_002", "agt_003", "agt_004"}
    assert "agt_001" not in recipients

    # Check worker-b inbox
    inbox_b = router.get_or_create_inbox("agt_002")
    assert inbox_b.pending_count == 1
    msg_b = inbox_b.receive_next()
    assert msg_b.sender == "agt_001"
    assert msg_b.payload == {"event": "announcement"}


def test_broadcast_running_only(sample_registry):
    discovery = AgentDiscoveryService(sample_registry)
    router = MessageRouter(discovery)

    recipients = router.broadcast(
        sender_identifier="worker-a",
        message_type=MessageType.EVENT,
        payload={"event": "running_only_event"},
        running_only=True,
    )
    # Only agt_002 is RUNNING (agt_003 and agt_004 are STOPPED)
    assert recipients == ["agt_002"]
