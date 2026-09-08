# Developing Agents with the Formicx SDK

This guide explains how to build, validate, register, and run autonomous AI agents in Formicx using the high-level `Agent` SDK.

---

## 1. Creating a New Agent Project

Use the `formicx agent create` command to scaffold a new agent project:

```bash
formicx agent create my-research-agent
```

This creates a clean, standardized project directory:

```text
my-research-agent/
│
├── agent.yaml          # Agent manifest specification
├── agent.py            # Agent Python implementation deriving from Agent
├── README.md           # Quickstart guide
└── tests/
    └── test_agent.py   # Starter test
```

---

## 2. Implementing Agent Logic

Formicx agents inherit from `formicx.Agent` and override lifecycle hooks:

```python
from formicx import Agent


class MyResearchAgent(Agent):
    """High-level Formicx Agent implementation."""

    def on_start(self):
        print(f"[{self.name}] Agent initialized with ID {self.id}")

    def on_message(self, message):
        print(f"[{self.name}] Incoming message from {message.sender}: {message.payload}")

        # Convenient reply helper
        self.reply(
            message,
            {
                "status": "success",
                "answer": "Formicx simplifies agent development.",
            },
        )

    def on_stop(self):
        print(f"[{self.name}] Agent stopping cleanly.")


if __name__ == "__main__":
    MyResearchAgent().run()
```

---

## 3. Agent Lifecycle Hooks

| Hook | Invocation | Description |
| :--- | :--- | :--- |
| `on_start()` | Called once | Executed before the message loop starts. Use for setup & initialization. |
| `on_message(message)` | Called per message | Main message handler. Invoked whenever an unread message arrives. |
| `on_error(error)` | Called on exception | Invoked when an unhandled exception occurs in `on_message()`. Keeps loop running unless fatal. |
| `on_stop()` | Called once | Executed during graceful shutdown (signal, Ctrl+C, or `self.stop()`). |

---

## 4. Messaging Helper APIs

Inside any `Agent` subclass method, you can use built-in helpers wrapping the communication SDK:

```python
# Send a direct message to another agent
self.send(to="research-agent", payload={"query": "ping"}, message_type="REQUEST")

# Reply to an incoming message (auto-sets recipient, RESPONSE type, and correlation_id)
self.reply(message, payload={"result": 42})

# Broadcast an event payload to all registered running agents
self.broadcast(payload={"event": "status_update"}, message_type="EVENT")

# Discover all running agents in Formicx
agents = self.discover(status="RUNNING")

# Fetch details for a specific registered agent
target_agent = self.get_agent("research-agent")
```

---

## 5. Validating and Deploying Agents

### Step 1: Validate Project Structure
```bash
formicx agent validate ./my-research-agent
```
Performs static validation of `agent.yaml` schema, entrypoint resolution, and Python syntax compilation without executing user code.

### Step 2: Register Agent with Daemon
```bash
formicx agent register ./my-research-agent
```

### Step 3: Start Agent
```bash
formicx agent start my-research-agent
```

### Step 4: Inspect Status
```bash
formicx agent status my-research-agent
```
