from pathlib import Path
import pytest

from formicx.enums.agent_status import AgentStatus
from formicx.enums.message_type import MessageType
from formicx.models.agent import Agent, AgentRuntime
from formicx.models.message import Message
from formicx.runtime.manager import AgentManager
from formicx.communication.discovery import AgentDiscoveryService
from formicx.communication.exceptions import CommunicationDeniedError
from formicx.communication.policy import AgentCommunicationPolicy, CommunicationPolicyEngine
from formicx.communication.router import MessageRouter


@pytest.fixture
def mock_registry():
    manager = AgentManager()
    agent_a = Agent(
        agent_id="agt_001",
        name="whatsapp-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    agent_b = Agent(
        agent_id="agt_002",
        name="mail-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    agent_c = Agent(
        agent_id="agt_003",
        name="research-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    agent_d = Agent(
        agent_id="agt_004",
        name="isolated-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    manager.register_agent(agent_a)
    manager.register_agent(agent_b)
    manager.register_agent(agent_c)
    manager.register_agent(agent_d)
    return manager.registry


def test_default_open_policy(mock_registry):
    discovery = AgentDiscoveryService(registry=mock_registry)
    engine = CommunicationPolicyEngine(discovery=discovery)

    # No policies configured -> default open
    assert engine.can_communicate("whatsapp-agent", "research-agent") is True
    assert engine.can_communicate("agt_001", "agt_003") is True


def test_explicit_allow_list(mock_registry):
    discovery = AgentDiscoveryService(registry=mock_registry)
    engine = CommunicationPolicyEngine(discovery=discovery)

    engine.set_policy("whatsapp-agent", ["mail-agent"])

    assert engine.can_communicate("whatsapp-agent", "mail-agent") is True
    assert engine.can_communicate("whatsapp-agent", "research-agent") is False
    assert engine.can_communicate("agt_001", "agt_002") is True
    assert engine.can_communicate("agt_001", "agt_003") is False


def test_empty_allow_list(mock_registry):
    discovery = AgentDiscoveryService(registry=mock_registry)
    engine = CommunicationPolicyEngine(discovery=discovery)

    engine.set_policy("isolated-agent", [])

    assert engine.can_communicate("isolated-agent", "mail-agent") is False
    assert engine.can_communicate("isolated-agent", "whatsapp-agent") is False


def test_directional_permissions(mock_registry):
    discovery = AgentDiscoveryService(registry=mock_registry)
    engine = CommunicationPolicyEngine(discovery=discovery)

    # A allows B
    engine.set_policy("whatsapp-agent", ["mail-agent"])
    # B restricts to empty list
    engine.set_policy("mail-agent", [])

    # whatsapp-agent -> mail-agent: ALLOWED
    assert engine.can_communicate("whatsapp-agent", "mail-agent") is True
    # mail-agent -> whatsapp-agent: DENIED (because B has explicit policy allow: [])
    assert engine.can_communicate("mail-agent", "whatsapp-agent") is False


def test_router_denied_communication_raises_error(mock_registry):
    discovery = AgentDiscoveryService(registry=mock_registry)
    engine = CommunicationPolicyEngine(discovery=discovery)
    engine.set_policy("whatsapp-agent", ["mail-agent"])

    router = MessageRouter(discovery=discovery, policy_engine=engine)

    msg_allowed = Message(
        sender="whatsapp-agent",
        recipient="mail-agent",
        message_type=MessageType.REQUEST,
        payload={"query": "test"},
    )
    recip_id = router.route(msg_allowed)
    assert recip_id == "agt_002"

    msg_denied = Message(
        sender="whatsapp-agent",
        recipient="research-agent",
        message_type=MessageType.REQUEST,
        payload={"query": "test"},
    )
    with pytest.raises(CommunicationDeniedError) as exc_info:
        router.route(msg_denied)

    assert "is not permitted to communicate with" in str(exc_info.value)


def test_router_broadcast_policy_filtering(mock_registry):
    discovery = AgentDiscoveryService(registry=mock_registry)
    engine = CommunicationPolicyEngine(discovery=discovery)
    # whatsapp-agent allows only mail-agent
    engine.set_policy("whatsapp-agent", ["mail-agent"])

    router = MessageRouter(discovery=discovery, policy_engine=engine)

    delivered = router.broadcast(
        sender_identifier="whatsapp-agent",
        message_type=MessageType.EVENT,
        payload={"event": "ping"},
    )

    assert delivered == ["agt_002"]
    assert "agt_003" not in delivered
    assert "agt_004" not in delivered


def test_config_dict_and_yaml_loading(tmp_path: Path, mock_registry):
    discovery = AgentDiscoveryService(registry=mock_registry)
    engine = CommunicationPolicyEngine(discovery=discovery)

    config_dict = {
        "communication": {
            "default_policy": "allow",
        },
        "agent_policies": {
            "whatsapp-agent": {
                "allow": ["mail-agent"],
            },
            "isolated-agent": {
                "allow": [],
            },
        },
    }

    engine.load_from_dict(config_dict)
    assert engine.can_communicate("whatsapp-agent", "mail-agent") is True
    assert engine.can_communicate("whatsapp-agent", "research-agent") is False
    assert engine.can_communicate("isolated-agent", "mail-agent") is False

    # Test YAML file loading
    yaml_file = tmp_path / "policy.yaml"
    import yaml
    yaml_file.write_text(yaml.dump(config_dict), encoding="utf-8")

    engine2 = CommunicationPolicyEngine(discovery=discovery)
    engine2.load_from_yaml(yaml_file)
    assert engine2.can_communicate("whatsapp-agent", "mail-agent") is True
    assert engine2.can_communicate("whatsapp-agent", "research-agent") is False
