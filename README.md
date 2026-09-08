# Formicx

Formicx is an open-source Linux-based operating environment designed specifically for developing, deploying, running, and coordinating persistent autonomous AI agents.

> **Core Philosophy:** Linux manages processes. Formicx manages agents.

While Linux handles processes, memory, CPU scheduling, filesystems, networking, and hardware, Formicx provides an agent operating layer managing operational identities, lifecycles, framework-independent process management, developer CLI control planes, multi-agent teams, reusable service integrations, and agent nodes.

---

## Current Status — Phase 5 Complete

Formicx is currently at **Phase 5 (Agent Communication Policies)**.

Phase 5 introduces directional agent-to-agent communication policy enforcement. By default, communication remains open (`allow_all`). Developers can configure directional policies restricting sender agents to explicitly allowed target agents, enforce isolated agents (`allow: []`), perform policy-filtered broadcasts, enforce reply authorization, and inspect policy configurations via `formicx policy` CLI commands.

---

## High-Level Agent SDK Usage

Creating an autonomous Formicx agent requires minimal boilerplate:

```python
from formicx import Agent, CommunicationDeniedError


class EchoAgent(Agent):

    def on_start(self):
        print(f"[{self.name}] Agent started with ID {self.id}")

    def on_message(self, message):
        print(f"[{self.name}] Received message from {message.sender}: {message.payload}")

        try:
            # Reply helper (auto-sets recipient, RESPONSE type, and correlation_id)
            self.reply(
                message,
                {
                    "echo": message.payload,
                    "status": "success",
                },
            )
        except CommunicationDeniedError as e:
            print(f"[{self.name}] Reply blocked by policy: {e}")

    def on_stop(self):
        print(f"[{self.name}] Agent shutting down.")


if __name__ == "__main__":
    EchoAgent().run()
```

---

## Agent Communication Policies

Configure policies in `formicx.yaml` or daemon configuration to restrict communication topically:

```yaml
agent_policies:
  whatsapp-agent:
    allow:
      - mail-agent
      - calendar-agent

  research-agent:
    allow:
      - web-agent
      - summarizer-agent

  isolated-agent:
    allow: []
```

### Key Policy Rules:
1. **Default Open:** If no policy exists for an agent, it can communicate with any destination.
2. **Sender-based Directional Enforcement:** Restricts the sender agent. Allowing `A -> B` does not imply `B -> A`.
3. **Authoritative Enforcement:** Evaluated in the daemon/message router before inbox delivery.
4. **Broadcast Filtering:** Skips unpermitted recipients without failing the entire broadcast.

---

## Agent Project Creation & Validation CLI

Developers can quickly scaffold and validate new agent projects:

```bash
# 1. Create a new agent project from template
formicx agent create my-agent

# 2. Validate agent manifest and python syntax statically
formicx agent validate ./my-agent

# 3. Register and start agent with formicxd daemon
formicx agent register ./my-agent
formicx agent start my-agent
```

---

## CLI Policy Commands

Inspect policy rules and check agent communication permissions from the terminal:

```bash
# List all configured agent policies
formicx policy list

# Check if communication between source and destination is allowed
formicx policy check whatsapp-agent mail-agent
# ALLOWED

formicx policy check whatsapp-agent research-agent
# DENIED: whatsapp-agent is not permitted to communicate with research-agent
```

---

## CLI Message Commands

Inspect and send messages directly from the terminal:

```bash
# Send a message manually
formicx message send coordinator-agent research-agent '{"question":"What is 2+2?"}'

# Inspect unconsumed pending inbox
formicx message inbox research-agent

# Inspect message history
formicx message history research-agent
```

---

## Installation

Formicx requires Python 3.11+.

Clone the repository and install in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

This registers the CLI binaries `formicx` and `formicxd`.

---

## Quickstart Guide

### 1. Start the Formicx Daemon

In Terminal 1:

```bash
formicxd
```

### 2. Manage Agents with the CLI

In Terminal 2:

```bash
# Check daemon status
formicx daemon health
formicx daemon status

# Register an agent
formicx agent register ./agents/hello-agent

# Start an agent process
formicx agent start hello-agent

# List registered agents
formicx agent list

# Inspect detailed status
formicx agent status hello-agent

# Inspect communication policies
formicx policy list
formicx policy check hello-agent worker-agent

# Stop an agent process
formicx agent stop hello-agent
```

---

## Help System

Access CLI documentation globally or per command group:

```bash
formicx --help
formicx agent --help
formicx policy --help
formicx message --help
formicx daemon --help
formicx help
```

---

## Running Tests

Execute the complete unit and integration test suite using `pytest`:

```bash
pytest
```

---

## Repository Architecture

```text
formicx/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── docs/
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── phase1-runtime.md
│   │   ├── phase2-control-plane.md
│   │   ├── phase3-communication.md
│   │   ├── phase4-agent-sdk.md
│   │   └── phase5-communication-policies.md
│   └── specifications/
│       ├── agent.md
│       ├── agent-manifest.md
│       ├── message.md
│       ├── node.md
│       ├── service.md
│       └── team.md
├── agents/
│   ├── hello-agent/
│   ├── worker-agent/
│   └── failing-agent/
├── src/
│   └── formicx/
│       ├── __init__.py
│       ├── config.py
│       ├── models/
│       ├── enums/
│       ├── utils/
│       ├── manifests/
│       ├── runtime/
│       ├── communication/
│       │   ├── __init__.py
│       │   ├── exceptions.py
│       │   ├── policy.py
│       │   ├── router.py
│       │   ├── service.py
│       │   └── local_transport.py
│       ├── daemon/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   └── api.py
│       ├── client/
│       │   ├── __init__.py
│       │   └── daemon_client.py
│       ├── sdk/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   └── context.py
│       └── cli/
│           ├── __init__.py
│           ├── main.py
│           └── commands/
│               ├── __init__.py
│               ├── agent.py
│               ├── daemon.py
│               ├── message.py
│               └── policy.py
├── examples/
│   ├── phase0_demo.py
│   ├── runtime_demo.py
│   ├── phase2_cli_demo.md
│   └── sdk_demo.py
└── tests/
    ├── test_agent.py
    ├── test_message.py
    ├── test_node.py
    ├── test_service.py
    ├── test_team.py
    ├── test_manifest_loader.py
    ├── test_agent_registry.py
    ├── test_process_manager.py
    ├── test_agent_manager.py
    ├── test_concurrent_agents.py
    ├── test_daemon_api.py
    ├── test_daemon_client.py
    ├── test_cli_agent.py
    ├── test_cli_daemon.py
    ├── test_cli_help.py
    ├── test_communication_router.py
    ├── test_communication_service.py
    ├── test_cli_message.py
    ├── test_agent_sdk.py
    ├── test_communication_policy.py
    ├── test_cli_policy.py
    └── test_phase5_integration.py
```

---

## License

Formicx is released under the [MIT License](LICENSE).

