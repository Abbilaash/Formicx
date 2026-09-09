# Formicx Phase 8 — Agent-Aware Resource Monitoring Architecture

## 1. Overview
Phase 8 connects the logical Formicx agent abstraction with the underlying operating system process model. While Linux sees running agents as generic `python` processes (`PID 1234`, `PID 1235`), Formicx inspects OS telemetry and maps process statistics directly to agent identities (`research-agent`, `vision-agent`), exposing real-time CPU, Memory, Thread, and Process status via `formicxd` control plane APIs and the `formicx agent resources` CLI.

---

## 2. Architecture & Data Flow

```text
┌─────────────────────────────────────────────────────────────┐
│ Formicx Runtime (formicxd)                                  │
│                                                             │
│ ┌──────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│ │ Agent Registry   │  │ ProcessManager  │  │ Agent Models │ │
│ └─────────┬────────┘  └────────┬────────┘  └──────────────┘ │
│           │                    │                            │
│ ┌─────────▼────────────────────▼──────────────────────────┐ │
│ │ ResourceService                                         │ │
│ │                                                         │ │
│ │ ├── AgentResourceMonitor (psutil process sampler)       │ │
│ │ └── Background Sampling Task (default interval: 5.0s)   │ │
│ └─────────────────────────┬───────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
               GET /v1/resources API & CLI
```

### Core Components
- **`AgentResourceUsage`** (`formicx.resources.models`): Domain model containing normalized agent telemetry (`agent_id`, `agent_name`, `pid`, `status`, `cpu_percent`, `memory_bytes`, `memory_percent`, `thread_count`, `last_sampled_at`).
- **`AgentResourceMonitor`** (`formicx.resources.monitor`): Process monitoring engine using `psutil` with safe exception guards (`NoSuchProcess`, `AccessDenied`, `ZombieProcess`) and non-blocking CPU calculation.
- **`ResourceService`** (`formicx.resources.service`): Service managing background async sampling loops, metric caching, and resolution by agent ID or name.

---

## 3. Canonical Metric Units & Observability Focus

1. **Canonical Memory Representation**: Memory is represented and transmitted in canonical bytes (`memory_bytes`). CLI views convert bytes into human-readable strings (`420.0 MB`, `1.20 GB`).
2. **Non-Blocking Telemetry**: `psutil.Process(pid).cpu_percent(interval=None)` initializes process baselines to prevent blocking daemon event loops.
3. **Observability Scope**: Phase 8 provides observability and telemetry without imposing cgroups, CPU limits, or container isolation (which are deferred to future phases).

---

## 4. API Endpoints & CLI Commands

### Daemon REST API Endpoints
- **`GET /v1/resources`**: Returns resource telemetry for all registered agents.
- **`GET /v1/agents/{identifier}/resources`**: Returns resource telemetry for a specific agent by ID or display name.

### CLI Commands
```bash
# List OS resource metrics for all registered Formicx agents
formicx agent resources

# Detailed single-agent resource inspection
formicx agent resources research-agent
```

### Example CLI Output
```text
FORMICX AGENT RESOURCES

AGENT              PID        CPU        MEMORY         STATUS
-----------------------------------------------------------------
research-agent     1234       14.2%      420.0 MB       RUNNING
vision-agent       1235       62.8%      1.20 GB        RUNNING
mail-agent         1236        1.4%      110.0 MB       RUNNING
```
