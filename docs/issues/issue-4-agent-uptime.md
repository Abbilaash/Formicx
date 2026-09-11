# [Good First Issue] feat(runtime): Track and display agent uptime in agent status

**Labels**: `good first issue`, `feature`, `runtime`  
**Target Files**: `src/formicx/models/agent.py`, `src/formicx/cli/commands/agent.py`

## Description
Track `started_at` timestamp in agent runtime state. When querying `formicx agent status <agent>`, calculate and display human-readable uptime (e.g. `Uptime: 2h 14m 05s`).

## Acceptance Criteria
- [ ] Record start timestamp when agent transitions to `RUNNING`.
- [ ] Format uptime dynamically in `formicx agent status`.
- [ ] Add unit test coverage in `tests/test_cli_agent.py`.
