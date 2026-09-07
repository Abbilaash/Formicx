import time
from formicx.enums.message_type import MessageType
from formicx.models.message import Message
from formicx.communication.inbox import AgentInbox


def test_inbox_enqueue_and_receive():
    inbox = AgentInbox(agent_id="agt_001")
    assert inbox.pending_count == 0

    msg1 = Message(
        sender="agt_sender",
        recipient="agt_001",
        message_type=MessageType.REQUEST,
        payload={"task": "1"},
    )
    inbox.enqueue(msg1)
    assert inbox.pending_count == 1

    received = inbox.receive_next(timeout=0.1)
    assert received is not None
    assert received.message_id == msg1.message_id
    assert inbox.pending_count == 0


def test_inbox_empty_and_timeout():
    inbox = AgentInbox(agent_id="agt_001")
    assert inbox.receive_next(timeout=0.01) is None


def test_inbox_peek_does_not_consume():
    inbox = AgentInbox(agent_id="agt_001")
    msg1 = Message(
        sender="agt_sender",
        recipient="agt_001",
        message_type=MessageType.EVENT,
        payload={"task": "peek_test"},
    )
    inbox.enqueue(msg1)

    pending = inbox.peek()
    assert len(pending) == 1
    assert pending[0].message_id == msg1.message_id
    assert inbox.pending_count == 1  # Not consumed

    # Now consume
    received = inbox.receive_next()
    assert received.message_id == msg1.message_id
    assert inbox.pending_count == 0


def test_inbox_history():
    inbox = AgentInbox(agent_id="agt_001", max_history=2)
    m1 = Message(sender="s", recipient="agt_001", message_type=MessageType.EVENT)
    m2 = Message(sender="s", recipient="agt_001", message_type=MessageType.EVENT)
    m3 = Message(sender="s", recipient="agt_001", message_type=MessageType.EVENT)

    inbox.enqueue(m1)
    inbox.enqueue(m2)
    inbox.enqueue(m3)

    history = inbox.list_history()
    assert len(history) == 2
    assert history[0].message_id == m2.message_id
    assert history[1].message_id == m3.message_id
