from __future__ import annotations

from datetime import timezone
import pytest
from pydantic import ValidationError

from formicx import Message, MessageType


def test_message_creation_defaults():
    msg = Message(
        sender="agt_1",
        recipient="agt_2",
        message_type=MessageType.TASK,
        payload={"action": "analyze"},
    )

    assert msg.message_id.startswith("msg_")
    assert msg.sender == "agt_1"
    assert msg.recipient == "agt_2"
    assert msg.message_type == MessageType.TASK
    assert msg.payload == {"action": "analyze"}
    assert msg.timestamp.tzinfo == timezone.utc


def test_message_empty_sender_or_recipient():
    with pytest.raises(ValidationError):
        Message(
            sender="",
            recipient="agt_2",
            message_type=MessageType.TASK,
        )

    with pytest.raises(ValidationError):
        Message(
            sender="agt_1",
            recipient="   ",
            message_type=MessageType.TASK,
        )


def test_message_serialization():
    msg = Message(
        sender="agt_1",
        recipient="agt_2",
        message_type=MessageType.RESPONSE,
        payload={"status": "success"},
    )

    json_str = msg.model_dump_json()
    assert "response" in json_str

    deserialized = Message.model_validate_json(json_str)
    assert deserialized.message_id == msg.message_id
    assert deserialized.message_type == MessageType.RESPONSE
    assert deserialized.payload == {"status": "success"}
