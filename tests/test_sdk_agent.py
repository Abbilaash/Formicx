import os
import time
from typing import List
import pytest

from formicx import Agent, BaseAgent
from formicx.models.message import Message
from formicx.communication.local_transport import LocalHTTPTransport


class DummyTransport:
    """Mock transport for unit testing Agent base class behavior."""

    def __init__(self, incoming_messages: List[Message] = None):
        self.incoming_messages = incoming_messages or []
        self.sent_messages: List[Message] = []
        self.replies: List[dict] = []
        self.broadcasts: List[dict] = []
        self.agents_discovered = []

    def send(self, message: Message) -> dict:
        self.sent_messages.append(message)
        return {"status": "DELIVERED", "message_id": message.message_id, "recipient_agent_id": message.recipient}

    def receive_next(self, agent_identifier: str, timeout: float = None) -> Message:
        if self.incoming_messages:
            return self.incoming_messages.pop(0)
        return None

    def broadcast(self, sender_identifier: str, message_type: str, payload: dict, running_only: bool = False) -> List[str]:
        self.broadcasts.append({
            "sender": sender_identifier,
            "type": message_type,
            "payload": payload,
        })
        return ["agt_dest1", "agt_dest2"]

    def discover_agents(self, status: str = None) -> List:
        return self.agents_discovered

    def get_agent(self, identifier: str):
        return None


class SampleAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.events: List[str] = []
        self.received_payloads: List[dict] = []
        self.errors_caught: List[Exception] = []

    def on_start(self):
        self.events.append("started")

    def on_message(self, message: Message):
        self.events.append(f"message:{message.message_id}")
        self.received_payloads.append(message.payload)
        if message.payload.get("trigger_error"):
            raise ValueError("Simulated message handling failure")
        if message.payload.get("should_reply"):
            self.reply(message, {"status": "ok"})

    def on_error(self, error: Exception):
        self.events.append("error")
        self.errors_caught.append(error)

    def on_stop(self):
        self.events.append("stopped")


def test_agent_export_alias():
    assert Agent is BaseAgent


def test_agent_identity_and_properties(monkeypatch):
    monkeypatch.setenv("FORMICX_AGENT_ID", "agt_test_123")
    monkeypatch.setenv("FORMICX_AGENT_NAME", "my-test-agent")

    agent = SampleAgent(transport=DummyTransport())
    assert agent.id == "agt_test_123"
    assert agent.agent_id == "agt_test_123"
    assert agent.name == "my-test-agent"
    assert agent.agent_name == "my-test-agent"
    assert agent.running is False


from formicx.enums.message_type import MessageType


def test_agent_lifecycle_hooks_order():
    msg1 = Message(sender="agt_sender", recipient="agt_test", message_type=MessageType.REQUEST, payload={"data": 1})
    msg2 = Message(sender="agt_sender", recipient="agt_test", message_type=MessageType.REQUEST, payload={"data": 2})
    mock_transport = DummyTransport([msg1, msg2])

    agent = SampleAgent(agent_id="agt_test", transport=mock_transport)

    # Run for 2 iterations then stop in a thread or by limiting queue
    # We can invoke run() and stop after messages are consumed
    def stop_later():
        while len(agent.received_payloads) < 2:
            time.sleep(0.01)
        agent.stop()

    import threading
    t = threading.Thread(target=stop_later)
    t.start()

    agent.run(poll_timeout=0.05)
    t.join()

    assert agent.events[0] == "started"
    assert f"message:{msg1.message_id}" in agent.events
    assert f"message:{msg2.message_id}" in agent.events
    assert agent.events[-1] == "stopped"
    assert agent.events.count("stopped") == 1


def test_agent_recoverable_error_handling():
    bad_msg = Message(sender="agt_sender", recipient="agt_test", message_type=MessageType.REQUEST, payload={"trigger_error": True})
    good_msg = Message(sender="agt_sender", recipient="agt_test", message_type=MessageType.REQUEST, payload={"data": "success"})
    mock_transport = DummyTransport([bad_msg, good_msg])

    agent = SampleAgent(agent_id="agt_test", transport=mock_transport)

    def stop_later():
        while len(agent.received_payloads) < 2:
            time.sleep(0.01)
        agent.stop()

    import threading
    t = threading.Thread(target=stop_later)
    t.start()

    agent.run(poll_timeout=0.05)
    t.join()

    assert "error" in agent.events
    assert len(agent.errors_caught) == 1
    assert str(agent.errors_caught[0]) == "Simulated message handling failure"
    assert agent.received_payloads == [{"trigger_error": True}, {"data": "success"}]
    assert agent.events[-1] == "stopped"


def test_agent_messaging_helper_methods():
    mock_transport = DummyTransport()
    agent = SampleAgent(agent_id="agt_helper", transport=mock_transport)

    # Test send
    res = agent.send("agt_target", {"task": "do_work"})
    assert res["status"] == "DELIVERED"
    assert len(mock_transport.sent_messages) == 1
    assert mock_transport.sent_messages[0].recipient == "agt_target"

    # Test broadcast
    recipients = agent.broadcast({"event": "ping"})
    assert recipients == ["agt_dest1", "agt_dest2"]
    assert len(mock_transport.broadcasts) == 1

    # Test reply
    msg = Message(message_id="msg_orig_99", sender="agt_sender", recipient="agt_helper", message_type=MessageType.REQUEST, payload={"query": "test"})
    res_reply = agent.reply(msg, {"answer": 42})
    assert res_reply["status"] == "DELIVERED"
    assert mock_transport.sent_messages[1].recipient == "agt_sender"
    assert mock_transport.sent_messages[1].correlation_id == "msg_orig_99"


def test_on_stop_called_only_once():
    agent = SampleAgent(agent_id="agt_once", transport=DummyTransport())
    agent.on_start()
    agent.stop()
    agent._do_stop()
    agent._do_stop()

    assert agent.events.count("stopped") == 1
