# Formicx

Formicx is an open-source Linux-based operating environment designed specifically for developing, deploying, running, and coordinating persistent autonomous AI agents.

> **Core Philosophy:** Linux manages processes. Formicx manages agents.

While Linux handles processes, memory, CPU scheduling, filesystems, networking, and hardware, Formicx provides an agent operating layer managing operational identities, lifecycles, framework-independent process management, developer CLI control planes, multi-agent teams, reusable service integrations, and agent nodes.

---

## Current Status — Phase 2 Complete

Formicx is currently at **Phase 2 (CLI + Daemon Control Plane)**.

Phase 2 adds the developer-facing CLI (`formicx`) communicating over a local loopback HTTP control interface (`http://127.0.0.1:8765`) to the runtime daemon (`formicxd`).

### Control Plane Architecture

```text
formicx CLI ──> DaemonClient ──> FastAPI (127.0.0.1:8765) ──> formicxd ──> AgentManager ──> OS Processes
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

# Stop an agent process
formicx agent stop hello-agent
```

---

## Help System

Access CLI documentation globally or per command group:

```bash
formicx --help
formicx agent --help
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
│   │   └── phase2-control-plane.md
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
│       ├── daemon/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   └── api.py
│       ├── client/
│       │   ├── __init__.py
│       │   └── daemon_client.py
│       └── cli/
│           ├── __init__.py
│           ├── main.py
│           └── commands/
│               ├── __init__.py
│               ├── agent.py
│               └── daemon.py
├── examples/
│   ├── phase0_demo.py
│   ├── runtime_demo.py
│   └── phase2_cli_demo.md
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
    └── test_cli_help.py
```

---

## License

Formicx is released under the [MIT License](LICENSE).
