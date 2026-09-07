import os
import pytest
from formicx.enums.agent_status import AgentStatus
from formicx.enums.message_type import MessageType
from formicx.models.agent import Agent, AgentRuntime
from formicx.models.message import Message
from formicx.runtime.registry import AgentRegistry
from formicx.communication.service import CommunicationService
from formicx.communication.transport import MessageTransport
from formicx.sdk.context import AgentContext


class DirectServiceTransport(MessageTransport):
    """Local mock transport for testing SDK directly against CommunicationService."""

    def __init__(self, service: CommunicationService) -> None:
        self.service = service

    def send(self, message: Message):
        return self.service.send_message(message)

    def receive_next(self, agent_identifier: str, timeout=None):
        return self.service.receive_next(agent_identifier, timeout=timeout)

    def discover_agents(self, status=None):
        return self.service.discover_agents(status=status)

    def get_agent(self, identifier: str):
        return self.service.get_agent(identifier)

    def broadcast(self, sender_identifier, message_type, payload, running_only=False):
        return self.service.broadcast(
            sender_identifier, message_type, payload, running_only
        )


@pytest.fixture
def comm_service():
    registry = AgentRegistry()
    agt_a = Agent(
        agent_id="agt_001",
        name="coordinator-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    agt_b = Agent(
        agent_id="agt_002",
        name="research-agent",
        version="1.0.0",
        runtime=AgentRuntime(language="python"),
        entrypoint="main.py",
        status=AgentStatus.RUNNING,
    )
    registry.register(agt_a)
    registry.register(agt_b)
    return CommunicationService(registry=registry)


def test_agent_context_env_identity(monkeypatch):
    monkeypatch.setenv("FORMICX_AGENT_ID", "agt_test_01")
    monkeypatch.setenv("FORMICX_AGENT_NAME", "test-agent")

    ctx = AgentContext()
    assert ctx.agent_id == "agt_test_01"
    assert ctx.agent_name == "test-agent"
    assert ctx.identity == "agt_test_01"


def test_sdk_send_reply_flow(comm_service):
    transport = DirectServiceTransport(comm_service)

    coord_ctx = AgentContext(
        agent_id="agt_001", agent_name="coordinator-agent", transport=transport
    )
    research_ctx = AgentContext(
        agent_id="agt_002", agent_name="research-agent", transport=transport
    )

    # 1. Coordinator sends request to research-agent
    send_res = coord_ctx.send(
        to="research-agent",
        payload={"question": "What is 2 + 2?"},
        message_type="REQUEST",
    )
    orig_msg_id = send_res["message_id"]

    # 2. Research agent receives request
    req_msg = research_ctx.receive(timeout=0.1)
    assert req_msg is not None
    assert req_msg.message_id == orig_msg_id
    assert req_msg.sender == "agt_001"
    assert req_msg.payload == {"question": "What is 2 + 2?"}

    # 3. Research agent replies using context.reply()
    research_ctx.reply(req_msg, payload={"answer": "4"})

    # 4. Coordinator receives response
    resp_msg = coord_ctx.receive(timeout=0.1)
    assert resp_msg is not None
    assert resp_msg.sender == "agt_002"
    assert resp_msg.recipient == "agt_001"
    assert resp_msg.message_type == MessageType.RESPONSE
    assert resp_msg.correlation_id == orig_msg_id
    assert resp_msg.payload == {"answer": "4"}


def test_sdk_discover_and_broadcast(comm_service):
    transport = DirectServiceTransport(comm_service)
    ctx = AgentContext(
        agent_id="agt_001", agent_name="coordinator-agent", transport=transport
    )

    agents = ctx.discover()
    assert len(agents) == 2

    recipients = ctx.broadcast(payload={"event": "sync"}, message_type="EVENT")
    assert recipients == ["agt_002"]
