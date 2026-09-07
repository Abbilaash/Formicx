# Formicx Architecture: Phase 1 Agent Runtime

## Overview

Phase 1 introduces the **Formicx Agent Runtime** engine (`formicxd`), transitioning Formicx from purely declarative domain models to active operating system process management.

The core philosophy of Formicx remains:
> **Linux manages processes. Formicx manages agents.**

---

## Runtime Architecture Flow

```text
agent.yaml
      │
      ▼
Manifest Loader (formicx.manifests)
      │
      ▼
Agent Model (formicx.models.Agent)
      │
      ▼
Agent Registry (formicx.runtime.AgentRegistry)
      │
      ▼
Agent Manager (formicx.runtime.AgentManager)
      │
      ▼
Process Manager (formicx.runtime.ProcessManager)
      │
      ▼
Independent OS Process (sys.executable entrypoint.py)
```

---

## Component Responsibilities

```text
                         FORMICXD
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       AGENT MANAGER                AGENT REGISTRY
              │                           │
              │                           │
              ▼                           │
       PROCESS MANAGER                    │
              │                           │
      ┌───────┼────────┐                  │
      │       │        │                  │
      ▼       ▼        ▼                  │
   Agent A  Agent B  Agent C ◄────────────┘
   PID      PID      PID
```

### 1. Manifest Loader (`formicx.manifests.load_agent_manifest`)
Reads YAML agent manifests (`agent.yaml`), resolves entrypoint paths to absolute filesystem locations, validates fields, and constructs standard `Agent` models.

### 2. Agent Registry (`formicx.runtime.AgentRegistry`)
In-memory registry storing `Agent` definitions indexed by `agent_id`. Validates uniqueness of registered IDs and allows querying/listing known agent specifications.

### 3. Process Manager (`formicx.runtime.ProcessManager`)
Manages OS-level child processes spawned via Python's `subprocess.Popen`. It tracks process PIDs, start timestamps, exit codes, and provides cross-platform graceful process termination (`terminate()` with `kill()` fallback).

### 4. Agent Manager (`formicx.runtime.AgentManager`)
Central orchestrator binding `AgentRegistry` and `ProcessManager`. It handles agent lifecycle transitions (`CREATED` -> `STARTING` -> `RUNNING` -> `STOPPING` -> `STOPPED` / `FAILED`), prevents duplicate process execution, supports agent restarts, and performs periodic status refreshing to detect unexpected child process crashes.

### 5. Formicx Daemon (`formicx.daemon.FormicxDaemon`)
Long-running owner daemon (`formicxd`) managing the application lifecycle and handling OS shutdown signals (`SIGINT`, `SIGTERM`) to guarantee clean termination of all child agent processes.

---

## Agent Definition vs. Running Agent Process

Formicx enforces a clear architectural distinction between an Agent's static specification and its dynamic OS execution state:

| Concept | Managed By | Fields / State |
|---|---|---|
| **Agent Definition** | `AgentRegistry` | `agent_id`, `name`, `version`, `runtime`, `entrypoint`, `capabilities`, `permissions` |
| **Running Agent** | `ProcessManager` | `pid`, `process` handle, `start_time`, `exit_code`, `intentional_stop` |

---

## Concurrent Multi-Process Execution & Failure Isolation

Each agent runs as an independent operating system process spawned with `sys.executable`. The host operating system kernel handles preemptive CPU scheduling and parallel execution.

### Failure Isolation
Because agents execute in isolated processes:
* If an agent process crashes (e.g. non-zero exit code or uncaught exception), `AgentManager.refresh_agent_status()` detects the exit and updates its status to `FAILED`.
* Other running agent processes and `formicxd` continue operating normally without disruption.
