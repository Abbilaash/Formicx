# [Good First Issue] feat(cli): Add --json flag to formicx agent list and status

**Labels**: `good first issue`, `enhancement`, `cli`  
**Target File**: `src/formicx/cli/commands/agent.py`

## Description
Add an optional `--json` flag to `formicx agent list` and `formicx agent status <agent>` commands. When passed, the output should be rendered as formatted JSON instead of a plain-text table, enabling programmatic scripting.

## Acceptance Criteria
- [ ] `formicx agent list --json` outputs formatted JSON array of agents.
- [ ] `formicx agent status <agent> --json` outputs formatted JSON object.
- [ ] Add unit test in `tests/test_cli_agent.py`.
