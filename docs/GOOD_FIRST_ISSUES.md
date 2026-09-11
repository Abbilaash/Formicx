# Formicx — Good First Issues Guide

This document lists beginner-friendly issues for open-source contributors looking to make their first contribution to **Formicx**.

Each issue below has been structured with clear requirements, target file pointers, and acceptance criteria.

---

## 📌 Current Issues (Immediate Tasks)

### 1. `[Good First Issue] feat(cli): Add --json flag to formicx agent list and status`

- **Category**: Current Issue / CLI UX
- **Difficulty**: Beginner
- **Labels**: `good first issue`, `enhancement`, `cli`
- **Target Files**: [src/formicx/cli/commands/agent.py](file:///a:/PROJECTS/Formicx/src/formicx/cli/commands/agent.py)

#### Description
Add an optional `--json` flag to `formicx agent list` and `formicx agent status <agent>` commands. When passed, the output should be rendered as formatted JSON instead of a plain-text table, enabling programmatic scripting.

#### Requirements & Acceptance Criteria
1. `formicx agent list --json` returns a JSON array of agent objects.
2. `formicx agent status <agent> --json` returns a formatted JSON object.
3. Add a unit test in `tests/test_cli_agent.py`.

---

### 2. `[Good First Issue] feat(cli): Add color-coded status highlights in agent resource table`

- **Category**: Current Issue / CLI UX
- **Difficulty**: Beginner
- **Labels**: `good first issue`, `ux`, `cli`
- **Target Files**: [src/formicx/cli/commands/agent.py](file:///a:/PROJECTS/Formicx/src/formicx/cli/commands/agent.py)

#### Description
Enhance `formicx agent resources` output using Typer/Rich styling:
- Highlight `RUNNING` status in green and `STOPPED`/`FAILED` in red.
- Highlight CPU usage above 80% in yellow/red.

#### Requirements & Acceptance Criteria
1. `formicx agent resources` applies colored terminal formatting.
2. Terminal output remains clean when piping (plain fallback).
3. Add a unit test verifying CLI output formatting.

---

## 🔮 Future Improvements (Planned Feature Enhancements)

### 3. `[Good First Issue] feat(templates): Add llm-agent boilerplate template`

- **Category**: Future Improvement / SDK Scaffolding
- **Difficulty**: Beginner–Intermediate
- **Labels**: `good first issue`, `templates`, `sdk`
- **Target Directory**: `src/formicx/templates/llm-agent/`

#### Description
Create a pre-packaged `llm-agent` template demonstrating how a Formicx agent can interact with LLM providers inside the `on_message` callback.

#### Requirements & Acceptance Criteria
1. Create `agent.yaml.template` and `agent.py.template` inside `src/formicx/templates/llm-agent/`.
2. Support `formicx agent create my-llm --template llm-agent`.
3. Validate that `formicx agent validate` works on the generated scaffold.

---

### 4. `[Good First Issue] feat(runtime): Track and display agent uptime in agent status`

- **Category**: Future Improvement / Telemetry
- **Difficulty**: Beginner
- **Labels**: `good first issue`, `feature`, `runtime`
- **Target Files**: [src/formicx/models/agent.py](file:///a:/PROJECTS/Formicx/src/formicx/models/agent.py), [src/formicx/cli/commands/agent.py](file:///a:/PROJECTS/Formicx/src/formicx/cli/commands/agent.py)

#### Description
Track `started_at` timestamp in agent runtime state. When querying `formicx agent status <agent>`, calculate and display human-readable uptime (e.g. `Uptime: 2h 14m 05s`).

#### Requirements & Acceptance Criteria
1. Record start timestamp when agent transitions to `RUNNING`.
2. Format uptime dynamically in `formicx agent status`.
3. Add unit test coverage.

---

### 5. `[Good First Issue] feat(cli): Add shell autocompletion support for bash, zsh, and fish`

- **Category**: Future Improvement / Developer Experience
- **Difficulty**: Beginner
- **Labels**: `good first issue`, `documentation`, `cli`
- **Target Files**: [src/formicx/cli/main.py](file:///a:/PROJECTS/Formicx/src/formicx/cli/main.py), [README.md](file:///a:/PROJECTS/Formicx/README.md)

#### Description
Enable Typer's built-in shell autocompletion for the `formicx` command (`formicx --install-completion`) and document installation steps in `README.md` and `CONTRIBUTING.md`.

#### Requirements & Acceptance Criteria
1. Verify `formicx --install-completion` works for bash, zsh, and fish.
2. Add a dedicated "Shell Autocompletion" section to `README.md`.
