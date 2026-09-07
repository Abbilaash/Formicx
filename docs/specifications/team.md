# Formicx Specification: Team Primitive

## Definition
A **Team** represents a logical group of agents collaborating to accomplish a shared goal.

## Primitive Fields

| Field | Type | Description | Required | Validation |
|---|---|---|---|---|
| `team_id` | `str` | Unique team identifier (e.g. `team_789xyz12`). Automatically generated if omitted. | Yes | Non-empty |
| `name` | `str` | Name of the team (e.g. `startup-team`). | Yes | Non-empty |
| `goal` | `str` | Shared mission or goal statement. | Yes | Non-empty |
| `members` | `list[str]` | List of member `agent_id` strings. | Yes | Must be unique list of agent IDs |
| `coordinator` | `str \| None` | Optional coordinator `agent_id`. | No | If specified, MUST exist in `members` |

---

## Validation Rules

1. `name` cannot be empty or whitespace.
2. `goal` cannot be empty or whitespace.
3. `members` must contain unique agent IDs (no duplicate elements).
4. If `coordinator` is provided, it **must** be a member of the team (i.e. `coordinator in members`).

---

## Python Representation

```python
from formicx.models import Team

team = Team(
    name="startup-team",
    goal="Build and evaluate a startup prototype",
    members=[
        "agt_a81f3e92",
        "agt_b92c4d11",
        "agt_c34d5e22"
    ],
    coordinator="agt_a81f3e92"
)
```

---

## JSON Serialization Example

```json
{
  "team_id": "team_789xyz12",
  "name": "startup-team",
  "goal": "Build and evaluate a startup prototype",
  "members": [
    "agt_a81f3e92",
    "agt_b92c4d11",
    "agt_c34d5e22"
  ],
  "coordinator": "agt_a81f3e92"
}
```

---

## Future Expansion Notes
In future phases, Teams will incorporate dynamic orchestration policies, shared context key-value memory stores, workflow DAG execution contracts, and automatic message routing rules. In Phase 0, Teams exclusively store declarative member IDs and goal definitions.
