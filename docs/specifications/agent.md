# Formicx Specification: Agent Primitive

## Definition
An **Agent** is an independently executable, identifiable, and manageable autonomous computational entity registered with Formicx.

## Purpose
Formicx manages the operational identity, runtime metadata, capabilities, permissions, and lifecycle state of agents regardless of their internal reasoning framework (e.g. LangGraph, CrewAI, OpenAI Agents SDK, custom scripts).

## Primitive Fields

| Field | Type | Description | Required | Validation |
|---|---|---|---|---|
| `agent_id` | `str` | Unique system identifier (e.g. `agt_a81f3e92`). Automatically generated if omitted. | Yes | Non-empty |
| `name` | `str` | Human-readable name provided by developer (e.g. `researcher`). | Yes | Non-empty |
| `version` | `str` | Semantic version string (e.g. `0.1.0`). | Yes | Non-empty |
| `runtime` | `AgentRuntime` | Nested model specifying `language` (e.g. `python`) and `framework` (e.g. `langgraph`, `custom`). | Yes | `language` non-empty |
| `entrypoint` | `str` | Entry point script or command (e.g. `main.py`). | Yes | Non-empty |
| `status` | `AgentStatus` | Lifecycle state enum. Default: `CREATED`. | Yes | Enum match |
| `capabilities` | `list[str]` | Declared functional capabilities (e.g. `["research", "summarization"]`). | No | Default `[]` |
| `permissions` | `list[str]` | Declared platform permissions (e.g. `["network.internet"]`). | No | Default `[]` |
| `node_id` | `str \| None` | Identifier of host `Node` where agent resides. | No | Default `None` |

---

## Agent Lifecycle States (`AgentStatus`)

The agent lifecycle states are defined by the `AgentStatus` enum:

* `CREATED`: Registered with Formicx, not yet initialized.
* `STARTING`: Resources being allocated and process booting.
* `RUNNING`: Actively executing tasks or listening for messages.
* `WAITING`: Waiting for external input, response, or timer.
* `STOPPING`: Graceful shutdown requested.
* `STOPPED`: Process terminated cleanly.
* `FAILED`: Terminated due to error or crash.

### Lifecycle Flow
```text
CREATED → STARTING → RUNNING → WAITING → STOPPING → STOPPED
                        │
                        ▼
                      FAILED
```

---

## Python Representation

```python
from formicx.models import Agent, AgentRuntime
from formicx.enums import AgentStatus

agent = Agent(
    name="researcher",
    version="0.1.0",
    runtime=AgentRuntime(
        language="python",
        framework="langgraph"
    ),
    entrypoint="main.py",
    capabilities=["research", "summarization"],
    permissions=["network.internet"],
    node_id="node_12345678"
)
```

---

## JSON Serialization Example

```json
{
  "agent_id": "agt_a81f3e92",
  "name": "researcher",
  "version": "0.1.0",
  "runtime": {
    "language": "python",
    "framework": "langgraph"
  },
  "entrypoint": "main.py",
  "status": "created",
  "capabilities": [
    "research",
    "summarization"
  ],
  "permissions": [
    "network.internet"
  ],
  "node_id": "node_12345678"
}
```
