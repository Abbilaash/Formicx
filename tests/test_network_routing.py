from unittest.mock import MagicMock
import pytest

from formicx.models.agent import Agent, AgentRuntime
from formicx.models.message import Message
from formicx.enums.agent_status import AgentStatus
from formicx.enums.message_type import MessageType
from formicx.runtime.registry import AgentRegistry
from formicx.communication.discovery import AgentDiscoveryService
from formicx.communication.exceptions import (
    AgentNotFoundError,
    CommunicationDeniedError,
    NodeUnavailableError,
)
from formicx.communication.network_transport import NetworkHTTPTransport
from formicx.communication.peer import PeerNode, PeerRegistry
from formicx.communication.policy import CommunicationPolicyEngine
from formicx.communication.router import MessageRouter


@pytest.fixture
def routing_setup():
    registry = AgentRegistry()
    sender_agent = Agent(
        agent_id="agt_local_01",
        name="local-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    recipient_agent = Agent(
        agent_id="agt_local_02",
        name="target-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    registry.register(sender_agent)
    registry.register(recipient_agent)

    discovery = AgentDiscoveryService(registry=registry)
    policy_engine = CommunicationPolicyEngine(discovery=discovery)
    peer_registry = PeerRegistry()
    mock_network = MagicMock(spec=NetworkHTTPTransport)

    router = MessageRouter(
        discovery=discovery,
        policy_engine=policy_engine,
        local_node_name="laptop",
        peer_registry=peer_registry,
        network_transport=mock_network,
    )

    return {
        "router": router,
        "registry": registry,
        "policy_engine": policy_engine,
        "peer_registry": peer_registry,
        "mock_network": mock_network,
    }


def test_route_local_message(routing_setup):
    router = routing_setup["router"]
    msg = Message(
        sender="local-agent",
        recipient="target-agent",
        message_type="REQUEST",
        payload={"query": "hello local"},
    )
    res_id = router.route(msg)
    assert res_id == "agt_local_02"
    inbox = router.get_inbox("agt_local_02")
    assert inbox is not None
    assert inbox.pending_count == 1


def test_route_remote_message_success(routing_setup):
    router = routing_setup["router"]
    peer_registry = routing_setup["peer_registry"]
    mock_network = routing_setup["mock_network"]

    peer = PeerNode(name="raspberry-pi", host="192.168.1.50", port=8000)
    peer_registry.register_peer(peer)

    msg = Message(
        sender="local-agent",
        recipient="vision-agent@raspberry-pi",
        message_type="REQUEST",
        payload={"task": "analyze_image"},
    )

    dest = router.route(msg)
    assert dest == "vision-agent@raspberry-pi"
    assert msg.sender == "local-agent@laptop"
    mock_network.send_remote_message.assert_called_once_with(peer, msg)


def test_route_remote_unknown_node(routing_setup):
    router = routing_setup["router"]
    msg = Message(
        sender="local-agent",
        recipient="vision-agent@unknown-node",
        message_type="REQUEST",
        payload={"task": "ping"},
    )

    with pytest.raises(NodeUnavailableError) as exc_info:
        router.route(msg)

    assert "is not registered in peer registry" in str(exc_info.value)


def test_route_remote_policy_denied(routing_setup):
    router = routing_setup["router"]
    policy_engine = routing_setup["policy_engine"]
    peer_registry = routing_setup["peer_registry"]

    peer = PeerNode(name="raspberry-pi", host="192.168.1.50", port=8000)
    peer_registry.register_peer(peer)

    # Restrict local-agent to only communicate with target-agent
    policy_engine.set_policy("local-agent", ["target-agent"])

    msg = Message(
        sender="local-agent",
        recipient="vision-agent@raspberry-pi",
        message_type="REQUEST",
        payload={"task": "ping"},
    )

    with pytest.raises(CommunicationDeniedError):
        router.route(msg)
