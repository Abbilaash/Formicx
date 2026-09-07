# Formicx

Formicx is an open-source Linux-based operating environment designed specifically for developing, deploying, running, and coordinating persistent autonomous AI agents.

> **Core Philosophy:** Linux manages processes. Formicx manages agents.

While Linux handles processes, memory, CPU scheduling, filesystems, networking, and hardware, Formicx provides an agent operating layer managing operational identities, lifecycles, framework-independent process management, multi-agent teams, reusable service integrations, and agent nodes.

---

## Current Status — Phase 1 Complete

Formicx is currently at **Phase 1 (Agent Runtime Implementation)**.

Phase 1 introduces the Formicx Agent Runtime engine (`formicxd`), capable of loading YAML agent manifests, registering agents, launching multiple agents concurrently as independent OS processes, tracking PIDs/exit codes, gracefully stopping processes, and detecting unexpected agent failures.

### Key Components

1. **Manifest Loader** (`load_agent_manifest`): Parses `agent.yaml` manifests into Formicx `Agent` models with entrypoint path resolution.
2. **Agent Registry** (`AgentRegistry`): In-memory store for registered agent definitions.
3. **Process Manager** (`ProcessManager`): Manages independent child OS processes using `sys.executable` and tracks PIDs and exit codes.
4. **Agent Manager** (`AgentManager`): Orchestrates lifecycle states (`CREATED`, `STARTING`, `RUNNING`, `WAITING`, `STOPPING`, `STOPPED`, `FAILED`) and supports starting, stopping, restarting, and failure detection.
5. **Daemon** (`FormicxDaemon`): Long-running daemon managing process lifecycles and signal handling.

---

## Installation

Formicx requires Python 3.11+.

Clone the repository and install in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

---

## Running the Demos

### Phase 1 Runtime Demo (Concurrent Agents & Failure Isolation)
Demonstrates loading manifests, running multiple agents concurrently as separate OS processes, detecting process crashes (`FAILED`), stopping active agents (`STOPPED`), and ensuring process cleanup:

```bash
python examples/runtime_demo.py
```

### Phase 0 Domain Model Demo
Inspects domain model creation, validation, and JSON serialization:

```bash
python examples/phase0_demo.py
```

---

## Running Tests

Execute the full unit test suite using `pytest`:

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
│   │   └── phase1-runtime.md
│   └── specifications/
│       ├── agent.md
│       ├── agent-manifest.md
│       ├── message.md
│       ├── node.md
│       ├── service.md
│       └── team.md
├── agents/
│   ├── hello-agent/
│   │   ├── agent.yaml
│   │   └── main.py
│   ├── worker-agent/
│   │   ├── agent.yaml
│   │   └── main.py
│   └── failing-agent/
│       ├── agent.yaml
│       └── main.py
├── src/
│   └── formicx/
│       ├── __init__.py
│       ├── models/
│       ├── enums/
│       ├── utils/
│       ├── manifests/
│       │   ├── __init__.py
│       │   └── loader.py
│       ├── runtime/
│       │   ├── __init__.py
│       │   ├── registry.py
│       │   ├── process.py
│       │   └── manager.py
│       └── daemon/
│           ├── __init__.py
│           └── main.py
├── examples/
│   ├── phase0_demo.py
│   └── runtime_demo.py
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
    └── test_concurrent_agents.py
```

---

## License

Formicx is released under the [MIT License](LICENSE).
