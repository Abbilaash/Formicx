# Formicx Specification: Agent Manifest

## Purpose
The **Agent Manifest** (`agent.yaml`) is a declarative specification describing an Agent's identity, runtime requirements, entrypoint script, functional capabilities, and required permissions.

The manifest allows developers to define agents in a standard format that is loaded directly by Formicx into the standard `Agent` domain model.

---

## Manifest Fields

| Field | Type | Description | Required | Default |
|---|---|---|---|---|
| `name` | `str` | Name of the agent (e.g. `hello-agent`). | Yes | N/A |
| `version` | `str` | Semantic version string (e.g. `0.1.0`). | Yes | N/A |
| `runtime` | `dict` | Nested dict specifying `language` and optional `framework`. | Yes | N/A |
| `runtime.language` | `str` | Programming language (e.g. `python`). | Yes | N/A |
| `runtime.framework` | `str` | Agent framework (e.g. `custom`, `langgraph`, `crewai`). | No | `"custom"` |
| `entrypoint` | `str` | Relative path to the executable script (e.g. `main.py`). | Yes | N/A |
| `capabilities` | `list[str]` | List of declared functional capability strings. | No | `[]` |
| `permissions` | `list[str]` | List of requested security permissions. | No | `[]` |

---

## Relative Entrypoint Resolution
The `entrypoint` specified in `agent.yaml` is resolved relative to the directory containing the `agent.yaml` manifest.

For example, given:
```text
agents/
└── hello-agent/
    ├── agent.yaml
    └── main.py
```

If `agent.yaml` specifies `entrypoint: main.py`, the Formicx Manifest Loader resolves the absolute path as `<absolute-path-to-hello-agent>/main.py`. This ensures runtime execution works independently of the caller's working directory.

---

## YAML Manifest Example

```yaml
name: hello-agent
version: 0.1.0

runtime:
  language: python
  framework: custom

entrypoint: main.py

capabilities:
  - greeting

permissions: []
```

---

## Python Loading API

```python
from formicx.manifests import load_agent_manifest

agent = load_agent_manifest("agents/hello-agent/agent.yaml")
print(agent.agent_id)    # Automatically generated agt_* ID
print(agent.entrypoint)  # Absolute path to main.py
```
