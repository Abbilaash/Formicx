# [Good First Issue] feat(cli): Add color-coded status highlights in agent resource table

**Labels**: `good first issue`, `ux`, `cli`  
**Target File**: `src/formicx/cli/commands/agent.py`

## Description
Enhance `formicx agent resources` output using Typer/Rich styling:
- Highlight `RUNNING` status in green and `STOPPED`/`FAILED` in red.
- Highlight CPU usage above 80% in yellow/red.

## Acceptance Criteria
- [ ] `formicx agent resources` applies colored terminal formatting.
- [ ] Terminal output remains clean when piping.
- [ ] Add unit test verifying CLI output formatting in `tests/test_cli_resources.py`.
