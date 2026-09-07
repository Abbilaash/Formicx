# Formicx

Formicx is an open-source Linux-based operating environment designed specifically for developing, deploying, running, and coordinating persistent autonomous AI agents.

> **Core Philosophy:** Linux manages processes. Formicx manages agents.

While Linux handles processes, memory, CPU scheduling, filesystems, networking, and hardware, Formicx provides an agent abstraction layer managing operational identities, lifecycles, framework-independent communication, multi-agent teams, reusable service integrations, and agent nodes.

---

## Current Status — Phase 0

Formicx is currently in **Phase 0 (Domain Model & Specifications)**.

Phase 0 establishes the fundamental domain models, specifications, validation contracts, and serialization logic for the five Formicx primitives:

1. **Agent** (`Agent`, `AgentRuntime`, `AgentStatus`)
2. **Message** (`Message`, `MessageType`)
3. **Node** (`Node`, `NodeResources`, `NodeStatus`)
4. **Service** (`Service`)
5. **Team** (`Team`)

---

## Installation

Formicx requires Python 3.11+.

Clone the repository and install in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

---

## Running the Phase 0 Demo

Run the Phase 0 demonstration script to inspect domain model creation, validation, and JSON serialization:

```bash
python examples/phase0_demo.py
```

---

## Running Tests

Execute the unit test suite using `pytest`:

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
│   │   └── overview.md
│   └── specifications/
│       ├── agent.md
│       ├── message.md
│       ├── node.md
│       ├── service.md
│       └── team.md
├── src/
│   └── formicx/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   ├── message.py
│       │   ├── node.py
│       │   ├── service.py
│       │   └── team.py
│       ├── enums/
│       │   ├── __init__.py
│       │   ├── agent_status.py
│       │   ├── message_type.py
│       │   └── node_status.py
│       └── utils/
│           ├── __init__.py
│           └── ids.py
├── examples/
│   └── phase0_demo.py
└── tests/
    ├── __init__.py
    ├── test_agent.py
    ├── test_message.py
    ├── test_node.py
    ├── test_service.py
    └── test_team.py
```

---

## License

Formicx is released under the [MIT License](LICENSE).
