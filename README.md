<p align="center">
  <img src="image-banner.png" alt="Formicx Logo" width="100%">
</p>

<p align="center">
  <a href="https://pypi.org/project/formicx/"><img src="https://img.shields.io/pypi/v/formicx?color=e50914&style=flat-square" alt="PyPI Package"></a>
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

## Quickstart

### Prerequisites & Installation

Formicx requires **Python 3.11+**.

Install Formicx directly from the official [PyPI Package Page](https://pypi.org/project/formicx/):

```bash
pip install formicx
```

Or using `uv`:

```bash
uv pip install formicx
```

#### Installing from Source (Development)
Alternatively, clone the repository and install in editable mode with development dependencies:

```bash
git clone https://github.com/Abbilaash/Formicx.git
cd Formicx
pip install -e ".[dev]"
```

This registers the global CLI executables `formicx`, `formicxd`, and `formicx-mcp`.

### Starting the Daemon

Launch the `formicxd` supervisor daemon on your host machine:

```bash
formicxd
```

By default, `formicxd` starts the local HTTP control API at `http://127.0.0.1:8642`, initializes resource monitoring, and starts local mDNS peer discovery.

---

## Example

Create, register, and execute a **Calculator Agent** with an `add` capability using Formicx.

### 1. Create the Calculator Agent Project

Create a directory named `calculator-agent` containing `agent.yaml` and `main.py`:

**`calculator-agent/agent.yaml`** (Manifest):
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

**`calculator-agent/main.py`** (Implementation):
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

### 2. Start the Daemon

In **Terminal 1**, run:

```bash
formicxd
```

### 3. Register & Start the Agent

In **Terminal 2**, run:

```bash
# Register the agent project manifest
formicx agent register ./calculator-agent

# Start the agent process
formicx agent start calculator-agent

# Check agent status
formicx agent list
```

### 4. Send a Message & Receive Response

Send an `add` request message to the agent:

```bash
formicx message send calculator-agent calculator-agent "{\"action\":\"add\",\"a\":15,\"b\":27}"
```

**Terminal Output:**
```text
[calculator-agent] Calculating 15.0 + 27.0 = 42.0
```

Alternatively, query the agent via the Python `DaemonClient` SDK:

```python
import time
from formicx import DaemonClient

client = DaemonClient()

# Send calculation request
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

---

## Command Line Guide

The `formicx` CLI provides complete operational control over agents, daemon states, network nodes, communication policies, and MCP servers.

| Command Group | Command Syntax | Purpose |
| :--- | :--- | :--- |
| **`formicx agent`** | `formicx agent <subcommand>` | Create, validate, register, start, stop, restart, inspect, and monitor agent processes. |
| **`formicx daemon`** | `formicx daemon <subcommand>` | Check status, ping health, start, or stop the `formicxd` background supervisor server. |
| **`formicx node`** | `formicx node <subcommand>` | Inspect local node identity and list active mDNS discovered peer nodes across local networks. |
| **`formicx message`** | `formicx message <subcommand>` | Send messages, read/peek inboxes, view history, or broadcast events across agents. |
| **`formicx policy`** | `formicx policy <subcommand>` | Manage authoritative communication access control lists (ACLs) between agents. |
| **`formicx mcp`** | `formicx mcp <subcommand>` | Launch the Model Context Protocol (MCP) server for integration with AI coding agents. |

---

### `formicx agent`

Commands for managing agent definitions and OS process lifecycles.

#### `create`
Scaffold a new Formicx agent project directory from a template.
```bash
formicx agent create research-agent
formicx agent create hello-agent --template basic
```

#### `validate`
Validate an agent project's `agent.yaml` manifest schema and Python entrypoint syntax without running code.
```bash
formicx agent validate ./calculator-agent
```

#### `register`
Register an agent directory or `agent.yaml` manifest with `formicxd`.
```bash
formicx agent register ./calculator-agent
```

#### `list`
List all registered Formicx agents, their operational status, and active OS process IDs (PIDs).
```bash
formicx agent list
```

#### `status`
Display detailed runtime status, entrypoint path, language runtime, PID, and uptime for an agent.
```bash
formicx agent status calculator-agent
```

#### `start`
Start a registered agent as an independent OS child process supervised by `formicxd`.
```bash
formicx agent start calculator-agent
```

#### `stop`
Gracefully terminate a running agent process.
```bash
formicx agent stop calculator-agent
```

#### `restart`
Restart a running or stopped agent process cleanly.
```bash
formicx agent restart calculator-agent
```

#### `resources`
Inspect real-time CPU %, RAM (RSS memory), thread count, and OS process metrics per agent or across all agents.
```bash
formicx agent resources
formicx agent resources calculator-agent
```

---

### `formicx daemon`

Commands for managing the `formicxd` supervisor service.

#### `start`
Start the background `formicxd` supervisor daemon server.
```bash
formicx daemon start
```

#### `status`
Display daemon operational status, total managed agents count, and running agents count.
```bash
formicx daemon status
```

#### `health`
Perform a fast HTTP health check ping against `formicxd`.
```bash
formicx daemon health
```

#### `stop`
Stop the `formicxd` daemon and gracefully terminate all active agent child processes.
```bash
formicx daemon stop
```

---

### `formicx node`

Commands for inspecting local host node identity and peer discovery.

#### `info`
Display local node name, host IP address, control port, and unique node identifier.
```bash
formicx node info
```

#### `peers`
List active Formicx daemon peer nodes automatically discovered over mDNS on local networks.
```bash
formicx node peers
```

---

### `formicx message`

Commands for sending and reading inter-agent messages.

#### `send`
Send a payload message from a sender agent to a target recipient agent.
```bash
formicx message send agent-a agent-b "{\"action\":\"ping\"}"
```

#### `inbox`
Receive or peek the next unread message from an agent's inbox queue.
```bash
formicx message inbox calculator-agent
```

#### `list`
List inbox messages or historical delivered messages for an agent.
```bash
formicx message list calculator-agent --history
```

#### `broadcast`
Broadcast an event payload to all active running agents across the node.
```bash
formicx message broadcast admin-agent "{\"event\":\"system_alert\"}"
```

---

### `formicx policy`

Commands for managing inter-agent communication security policies (ACLs).

#### `allow`
Grant permission for a source agent to send messages/invoke actions on a target agent.
```bash
formicx policy allow worker-agent database-agent
```

#### `deny`
Revoke communication permission between a source agent and target agent.
```bash
formicx policy deny worker-agent database-agent
```

#### `list`
Display all active communication access control rules.
```bash
formicx policy list
```

#### `reset`
Reset all policy rules to default permissions.
```bash
formicx policy reset
```

---

### `formicx mcp`

Commands for managing Model Context Protocol integration.

#### `start`
Launch the `formicx-mcp` server to connect Formicx directly to AI coding agents.
```bash
formicx mcp start
```

---

## MCP Integration for AI Coding Agents

Formicx includes a built-in **Model Context Protocol (MCP)** server (`formicx-mcp` or `formicx mcp start`) that enables AI coding assistants (**Antigravity**, **Cursor**, **Claude Desktop**, **Copilot**) to inspect, manage, and communicate with Formicx agents directly inside your IDE environment.

### MCP Features
- **Native Tools**: `formicx_list_agents`, `formicx_register_agent`, `formicx_start_agent`, `formicx_stop_agent`, `formicx_send_message`, `formicx_get_inbox`, `formicx_daemon_status`.
- **Complete Context & Documentation**: AI assistants can invoke `formicx_get_documentation` or read `formicx://docs/*` MCP resources to get full context on Formicx SDK usage, manifests, CLI commands, and architecture.

### IDE Configuration (`mcpServers`)

Add Formicx to your IDE's MCP configuration settings file:

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

For detailed IDE setup guides and documentation, see the [MCP Integration Guide](docs/mcp_integration.md).

---

## Running Tests

Execute the complete Formicx test suite using `pytest`:

```bash
pytest
```

Or using `uv`:

```bash
uv run pytest
```

---

## Contributing

Formicx welcomes open-source contributions! Whether you are fixing a bug, extending CLI commands, or building new agent templates, check out our guides:

- [Contributing Guide](CONTRIBUTING.md) — Setup local dev environment, run tests, and submit pull requests.
- [Good First Issues Guide](docs/GOOD_FIRST_ISSUES.md) — Curated beginner-friendly tasks with clear pointers and acceptance criteria.

---

## License

Formicx is released under the [MIT License](LICENSE).

---

Made with ❤️. If you encounter any issues, please open an issue/thread along with a detailed description.
