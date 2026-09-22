<p align="center">
  <img src="image-banner.png" alt="Formicx Logo" width="100%">
</p>

<p align="center">
  <a href="https://github.com/Abbilaash/Formicx/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Abbilaash/Formicx?color=e50914&style=flat-square" alt="License"></a>
  <a href="https://github.com/Abbilaash/Formicx"><img src="https://img.shields.io/badge/Open%20Source-%E2%9D%A4-e50914?style=flat-square" alt="Open Source"></a>
  <a href="https://hits.sh/github.com/Abbilaash/Formicx/"><img src="https://hits.sh/github.com/Abbilaash/Formicx/badge.svg?color=e50914&label=Views&style=flat-square" alt="Views"></a>
  <a href="https://github.com/Abbilaash/Formicx/network/members"><img src="https://img.shields.io/github/forks/Abbilaash/Formicx?color=e50914&style=flat-square" alt="Forks"></a>
  <a href="https://github.com/Abbilaash/Formicx/stargazers"><img src="https://img.shields.io/github/stars/Abbilaash/Formicx?color=e50914&style=flat-square" alt="Stars"></a>
</p>

# Formicx

Formicx is an open-source Linux-based operating environment designed specifically for developing, deploying, running, and coordinating persistent autonomous AI agents.

> **Core Philosophy:** Linux manages processes. Formicx manages agents.

While Linux handles processes, memory, CPU scheduling, filesystems, networking, and hardware, Formicx provides an agent operating layer managing operational identities, lifecycles, framework-independent process management, developer CLI control planes, multi-agent teams, reusable service integrations, and agent nodes.

---

## Why Formicx?

Traditional operating systems like Linux, macOS, and Windows were engineered for web servers, static binaries, and human-driven applications. They were **never designed for autonomous, non-deterministic AI agent fleets**.

Formicx fills the architectural gap between high-level LLM agent frameworks (LangChain, AutoGen, CrewAI) and low-level operating system kernels.

| Problem / Issue in Current OS | Impact on AI Agent Fleets | How Formicx Solves It |
| :--- | :--- | :--- |
| **Anonymous Process Model** | The kernel sees every agent as generic `python3` processes with zero logical context or agent identity. | **1:1 Kernel PID Mapping:** Assigns a first-class operational identity and kernel process mapping to every agent. |
| **Opaque Resource Telemetry** | OS monitors container black-boxes, making it impossible to detect agent-specific memory leaks or LLM retry spikes. | **Agent-Aware Telemetry:** Collects non-blocking CPU, RAM (`psutil`), thread count, and uptime per agent via CLI and API. |
| **No Inter-Agent Access Control** | Prompts attempt to enforce rules ("do not invoke tool X"), leading to rogue agent executions and security breaches. | **Authoritative Control Plane ACLs:** Enforces strict policy envelopes defining authorized agent-to-agent communication paths. |
| **Manual Network Configuration** | Inter-agent coordination across local devices requires hardcoded IP addresses or centralized cloud webhooks. | **Zero-Config mDNS Peer Discovery:** Automatically discovers agent nodes across local networks over peer-to-peer mDNS. |
| **Fragile Runtime Lifecycles** | An unhandled exception or OOM error crashes the parent Python process, killing the entire agent swarm without trace. | **Dedicated Supervisor Daemon (`formicxd`):** Provides daemonized background lifecycle governance (`start`, `stop`, `restart`, `recover`). |

---

## Installation

Formicx requires Python 3.11+.

Clone the repository and install in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

This registers the CLI binaries `formicx` and `formicxd`.

---

## Example

Create, register, and run a **Calculator Agent** with an `add` capability using Formicx.

### 1. Create the Calculator Agent Files

Create a directory named `calculator-agent` containing `agent.yaml` and `main.py`:

**`calculator-agent/agent.yaml`** (Agent Manifest):
```yaml
name: calculator-agent
version: 0.1.0

runtime:
  language: python
  framework: custom

entrypoint: main.py

capabilities:
  - add
```

**`calculator-agent/main.py`** (Agent Code):
```python
import sys
from formicx import Agent


class CalculatorAgent(Agent):

    def on_start(self):
        print(f"[{self.name}] Calculator Agent started with ID: {self.id}", flush=True)

    def on_message(self, message):
        payload = message.payload or {}
        action = payload.get("action")

        if action == "add":
            a = float(payload.get("a", 0))
            b = float(payload.get("b", 0))
            result = a + b
            print(f"[{self.name}] Calculating {a} + {b} = {result}", flush=True)

            self.reply(
                message,
                {
                    "action": "add",
                    "a": a,
                    "b": b,
                    "result": result,
                    "status": "success",
                },
            )

    def on_stop(self):
        print(f"[{self.name}] Stopping cleanly.", flush=True)


if __name__ == "__main__":
    CalculatorAgent().run()
```

### 2. Start the Formicx Daemon

In **Terminal 1**, start the supervisor daemon:

```bash
formicxd
```

### 3. Register, Start, and Test the Agent

In **Terminal 2**, run the following commands:

```bash
# Register the calculator agent
formicx agent register ./calculator-agent

# Start the agent process
formicx agent start calculator-agent

# Verify agent status
formicx agent list
```

### 4. Send a Request and View Output

Send an `add` calculation message to the agent (Formicx requires the sender to be a registered agent, e.g. `calculator-agent`):

```bash
formicx message send calculator-agent calculator-agent "{\"action\":\"add\",\"a\":15,\"b\":27}"
```

**Output:**
```text
[calculator-agent] Processing: 15.0 + 27.0 = 42.0
```

Alternatively, invoke it via a Python test script (`test_calculator.py`):

```python
import time
from formicx import DaemonClient

client = DaemonClient()

# Send calculation request to calculator-agent
client.send_message(
    sender="calculator-agent",
    recipient="calculator-agent",
    message_type="REQUEST",
    payload={"action": "add", "a": 25, "b": 17},
)

time.sleep(0.5)

# Fetch calculation response from history
history = client.get_inbox("calculator-agent", history=True)
for msg in reversed(history):
    payload = msg.get("payload", {})
    if "result" in payload:
        print("Result:", payload)
        break
```

Run:
```bash
python test_calculator.py
```

**Output:**
```text
Result: {'action': 'add', 'a': 25.0, 'b': 17.0, 'result': 42.0, 'status': 'success'}
```

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

# Inspect OS resource usage across agents
formicx agent resources
formicx agent resources research-agent

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
formicx mcp --help
formicx help
```

---

## MCP Integration for AI Assistants

Formicx includes a built-in **Model Context Protocol (MCP)** server (`formicx-mcp` or `formicx mcp start`) that enables AI coding agents (**Antigravity**, **Cursor**, **Claude Desktop**, **Copilot**) to inspect, manage, and communicate with Formicx agents directly from the IDE.

### Features
- **MCP Tool Execution**: `formicx_list_agents`, `formicx_register_agent`, `formicx_start_agent`, `formicx_stop_agent`, `formicx_send_message`, `formicx_get_inbox`, `formicx_daemon_status`.
- **Complete Context & Documentation**: AI agents can invoke `formicx_get_documentation` or read `formicx://docs/*` MCP resources to get full context on Formicx SDK usage, manifests, CLI commands, and architecture.

### IDE Configuration (`mcpServers`)
```json
{
  "mcpServers": {
    "formicx": {
      "command": "formicx-mcp",
      "args": []
    }
  }
}
```
For detailed setup guides, see the [MCP Integration Guide](docs/mcp_integration.md).

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

## Contributing & Good First Issues

Formicx welcomes open-source contributions! Whether you're fixing a bug, improving CLI commands, or building new agent templates, check out our guides:

- [Contributing Guide](CONTRIBUTING.md) — Setup local dev environment, run tests, submit PRs.
- [Good First Issues Guide](docs/GOOD_FIRST_ISSUES.md) — Curated beginner-friendly tasks with clear pointers and acceptance criteria.

---

## License

Formicx is released under the [MIT License](LICENSE).



