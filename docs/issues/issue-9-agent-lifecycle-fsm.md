# [Good First Issue] feat(runtime): Formalize Agent Lifecycle Finite State Machine (FSM) and add PAUSED state

**Labels**: `good first issue`, `runtime`, `architecture`  
**Target Files**: `src/formicx/enums/agent_status.py`, `src/formicx/models/agent.py`, `src/formicx/runtime/manager.py`

## Overview
Formalize Formicx agent lifecycle transitions into an explicit Finite State Machine (FSM) and introduce a `PAUSED` state. This makes status recovery, retries, and status telemetry predictable.

## Proposed States & Transition Rules
```text
CREATED  ──▶  STARTING  ──▶  RUNNING  ──▶  PAUSED
                │               │            │
                ▼               ▼            ▼
             FAILED          STOPPING ──▶ STOPPED
```

## Requirements & Acceptance Criteria
- [ ] Add `PAUSED` to `AgentStatus` enum (`src/formicx/enums/agent_status.py`).
- [ ] Implement explicit `can_transition(from_state, to_state)` validation helper in `AgentManager`.
- [ ] Add `formicx agent pause <agent>` and `formicx agent resume <agent>` CLI commands.
- [ ] Add unit test coverage in `tests/test_runtime.py` and `tests/test_cli_agent.py`.
