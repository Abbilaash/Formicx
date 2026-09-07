# Formicx Specification: Message Primitive

## Purpose
The **Message** primitive represents the standardized asynchronous communication contract between Formicx agents and services.

## Primitive Fields

| Field | Type | Description | Required | Validation |
|---|---|---|---|---|
| `message_id` | `str` | Unique message identifier (e.g. `msg_82bc17f9`). Automatically generated if omitted. | Yes | Non-empty |
| `sender` | `str` | Agent ID or Service ID sending the message (e.g. `agt_a81f3e92`). | Yes | Non-empty |
| `recipient` | `str` | Agent ID or Service ID receiving the message (e.g. `agt_b92c4d11`). | Yes | Non-empty |
| `message_type` | `MessageType` | Category of message payload. | Yes | Enum match |
| `payload` | `dict[str, Any]` | Generic JSON-serializable dictionary containing task details, data, or event metadata. | Yes | Default `{}` |
| `timestamp` | `datetime` | Timezone-aware UTC timestamp when message was generated. Automatically generated if omitted. | Yes | UTC ISO-8601 |

---

## Message Types (`MessageType`)

* `TASK`: Request for another agent or service to perform work.
* `RESPONSE`: Result or outcome returned for a previous `TASK`.
* `EVENT`: Broadcast notification of a state change or lifecycle trigger.
* `NOTIFICATION`: Informational status or system alert.

---

## Python Representation

```python
from formicx.models import Message
from formicx.enums import MessageType

message = Message(
    sender="agt_a81f3e92",
    recipient="agt_b92c4d11",
    message_type=MessageType.TASK,
    payload={
        "task": "Analyze repository architecture",
        "priority": "high"
    }
)
```

---

## JSON Serialization Example

```json
{
  "message_id": "msg_82bc17f9",
  "sender": "agt_a81f3e92",
  "recipient": "agt_b92c4d11",
  "message_type": "task",
  "payload": {
    "task": "Analyze repository architecture",
    "priority": "high"
  },
  "timestamp": "2026-09-07T16:24:20.000000Z"
}
```
