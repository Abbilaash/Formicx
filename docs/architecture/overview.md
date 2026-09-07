# Formicx Architecture Overview — Phase 0

## Architectural Concept

Linux manages core operating system concerns:
* Processes & memory management
* CPU scheduling
* Filesystem access
* Networking stack
* Hardware abstraction

Formicx introduces an **Agent Abstraction Layer** running on top of Linux to manage:
* Autonomous agent operational identities
* Agent lifecycles & runtime specifications
* Inter-agent communication contracts
* Persistent agent team compositions
* Service capability bindings
* Agent node hardware representations

> **Core Axiom:** Linux manages processes. Formicx manages agents.

---

## Phase 0 Domain Model Architecture

In Phase 0, Formicx defines the fundamental conceptual and object domain model. This structure underpins all future runtime components (`formicxd`, `formicxctl`, message buses, networking engines, and SDKs).

```text
                         FORMICX

        ┌──────────────────────────────────┐
        │              AGENT               │
        │                                  │
        │ ID                               │
        │ Runtime                          │
        │ Lifecycle                        │
        │ Capabilities                     │
        │ Permissions                      │
        └───────────────┬──────────────────┘
                        │
              communicates using
                        │
                        ▼
        ┌──────────────────────────────────┐
        │             MESSAGE              │
        │                                  │
        │ Sender                           │
        │ Recipient                        │
        │ Type                             │
        │ Payload                          │
        └──────────────────────────────────┘

        ┌────────────────┐   ┌─────────────┐
        │      TEAM      │   │   SERVICE   │
        │                │   │             │
        │ Agent IDs      │   │ Capability  │
        │ Goal           │   │ Permission  │
        │ Coordinator    │   │ Status      │
        └────────────────┘   └─────────────┘

                        │
                        ▼

        ┌──────────────────────────────────┐
        │              NODE                │
        │                                  │
        │ Device running Formicx           │
        │ Architecture                     │
        │ Resources                        │
        │ Status                           │
        └──────────────────────────────────┘

                        │
                        ▼

                    Linux / Debian
```

> **Note:** The diagram above describes the declarative domain model contract established in Phase 0. Physical process scheduling, network sockets, containerization, and message brokers are added in subsequent phases.

---

## The Five Primitives

1. **Agent (`formicx.models.Agent`)**: Represents an independently executable, identifiable, and manageable autonomous computational entity registered with Formicx.
2. **Message (`formicx.models.Message`)**: Defines the standard structured payload for asynchronous agent-to-agent communication.
3. **Node (`formicx.models.Node`)**: Represents a physical or virtual host device running the Formicx environment.
4. **Service (`formicx.models.Service`)**: Encapsulates a reusable capability provided through Formicx to agents (e.g. Mail, GitHub, Browser, Filesystem).
5. **Team (`formicx.models.Team`)**: Defines a logical group of agents collaborating to accomplish a shared goal.

---

## Operational vs. Reasoning Separation

Formicx enforces a clean separation between **Operational Identity** and **Reasoning Framework**:

* **Formicx** manages the operational identity, permissions, lifecycle states, message formats, and node residency.
* **Agent Frameworks** (such as LangGraph, CrewAI, OpenAI Agents SDK, AutoGen, or custom Python code) govern how the agent thinks, plans, and reasons.

This framework-agnostic design allows heterogeneous agent stacks to interoperate seamlessly within a unified Formicx environment.
