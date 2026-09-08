# Formicx

Formicx is an open-source Linux-based operating environment designed specifically for developing, deploying, running, and coordinating persistent autonomous AI agents.

> **Core Philosophy:** Linux manages processes. Formicx manages agents.

While Linux handles processes, memory, CPU scheduling, filesystems, networking, and hardware, Formicx provides an agent operating layer managing operational identities, lifecycles, framework-independent process management, developer CLI control planes, multi-agent teams, reusable service integrations, and agent nodes.

---

## Current Status — Phase 6 Complete

Formicx is currently at **Phase 6 (Distributed Agent Networking)**.

Phase 6 introduces inter-node distributed agent messaging across separate machines (Laptops, Raspberry Pis, Cloud Servers). Agents communicate using qualified addresses (`agent-name@node-name`) while maintaining unified SDK primitives (`self.send()`), peer node registries, network HTTP transport routing, authoritative remote communication policy enforcement, and `formicx node` CLI management tools.

---

## High-Level Agent SDK Usage

Creating an autonomous Formicx agent with local or distributed communication requires minimal boilerplate:

```python
from formicx import Agent, CommunicationDeniedError, NodeUnavailableError


class CoordinatorAgent(Agent):

    def on_start(self):
        print(f"[{self.name}] Agent started with ID {self.id}")

        # Send local message
        self.send(to="research-agent", payload={"task": "local_search"})

        try:
            # Send distributed message to an agent on a remote node
            self.send(
                to="vision-agent@raspberry-pi",
                payload={"task": "analyze_camera_feed"},
            )
        except NodeUnavailableError:
            print(f"[{self.name}] Remote node 'raspberry-pi' is offline or unknown.")
        except CommunicationDeniedError as e:
            print(f"[{self.name}] Inter-node communication blocked by policy: {e}")

    def on_message(self, message):
        print(f"[{self.name}] Received message from {message.sender}: {message.payload}")

        self.reply(message, {"status": "success", "echo": message.payload})


if __name__ == "__main__":
    CoordinatorAgent().run()
```

---

## Distributed Node & Peer Configuration (`formicx.yaml`)

Configure node identity and peer network definitions:

```yaml
node:
  name: laptop
  host: 0.0.0.0
  port: 8765

peers:
  raspberry-pi:
    host: 192.168.1.50
    port: 8000

  home-server:
    host: 192.168.1.60
    port: 9000
```

---

## Agent Communication Policies

Configure policies in `formicx.yaml` or daemon configuration to restrict local and remote communication:

```yaml
agent_policies:
  whatsapp-agent:
    allow:
      - mail-agent
      - calendar-agent

  research-agent:
    allow:
      - vision-agent@raspberry-pi
      - web-agent

  isolated-agent:
    allow: []
```

### Key Policy & Networking Rules:
1. **Unified Addressing:** Local addresses (`"agent-a"`) and qualified distributed addresses (`"agent-a@node-b"`) use identical SDK method calls (`self.send()`).
2. **Authoritative Enforcement:** Remote messages received over HTTP are validated against local policies before inbox delivery.
3. **Peer Node Management:** In-memory registry maps remote node names to target IP hosts and ports.

---

## CLI Node & Peer Commands

Inspect local node details and manage remote peers from the terminal:

```bash
# Display local node details
formicx node info

# List known remote peer nodes
formicx node peers

# Ping remote peer node health endpoint
formicx node ping raspberry-pi
# ONLINE Ping to peer 'raspberry-pi' (192.168.1.50:8000) succeeded in 4.25 ms.
```

---

## CLI Policy & Message Commands

Inspect policy rules and send debug messages directly from the terminal:

```bash
# List configured agent policies
formicx policy list

# Check communication permissions
formicx policy check whatsapp-agent vision-agent@raspberry-pi

# Send a message to a remote agent
formicx message send coordinator-agent vision-agent@raspberry-pi '{"task":"analyze"}'
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

### 2. Manage Agents & Nodes with the CLI

In Terminal 2:

```bash
# Check daemon status
formicx daemon health
formicx daemon status

# Check local node and peers
formicx node info
formicx node peers

# Register an agent
formicx agent register ./agents/hello-agent

# Start an agent process
formicx agent start hello-agent

# Stop an agent process
formicx agent stop hello-agent
```

---

## Help System

Access CLI documentation globally or per command group:

```bash
formicx --help
formicx agent --help
formicx node --help
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
│   │   ├── phase5-communication-policies.md
│   │   └── phase6-distributed-networking.md
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
│       │   ├── address.py
│       │   ├── exceptions.py
│       │   ├── network_transport.py
│       │   ├── peer.py
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
│               ├── node.py
│               └── policy.py
├── examples/
│   ├── phase0_demo.py
│   ├── runtime_demo.py
│   ├── phase2_cli_demo.md
│   ├── sdk_demo.py
│   └── distributed_demo.py
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
    ├── test_phase5_integration.py
    ├── test_agent_address.py
    ├── test_peer_registry.py
    ├── test_network_routing.py
    ├── test_cli_node.py
    └── test_phase6_integration.py
```

---

## License

Formicx is released under the [MIT License](LICENSE).


