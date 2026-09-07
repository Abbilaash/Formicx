# Formicx Specification: Service Primitive

## Definition
A **Service** represents a reusable capability or integration provided through Formicx to autonomous agents.

## Architectural Context
Instead of each agent directly embedding third-party API SDKs, OAuth flows, or platform credentials, Formicx abstracts capabilities behind standard Service contracts.

```text
Agent ──> Formicx Service ──> External Platform (GitHub, Mail, Filesystem, Browser)
```

## Primitive Fields

| Field | Type | Description | Required | Validation |
|---|---|---|---|---|
| `service_id` | `str` | Unique service identifier (e.g. `svc_abc12345`). Automatically generated if omitted. | Yes | Non-empty |
| `name` | `str` | Name of the service capability (e.g. `github`, `mail`). | Yes | Non-empty |
| `capabilities` | `list[str]` | Exported functional capability tags (e.g. `["read_repository", "read_issues"]`). | No | Default `[]` |
| `permissions` | `list[str]` | Security permissions required to invoke service (e.g. `["github.read"]`). | No | Default `[]` |
| `status` | `str` | Operational status. Default: `"active"`. | Yes | Non-empty |

---

## Python Representation

```python
from formicx.models import Service

service = Service(
    name="github",
    capabilities=[
        "read_repository",
        "read_issues"
    ],
    permissions=[
        "github.read"
    ],
    status="active"
)
```

---

## JSON Serialization Example

```json
{
  "service_id": "svc_abc12345",
  "name": "github",
  "capabilities": [
    "read_repository",
    "read_issues"
  ],
  "permissions": [
    "github.read"
  ],
  "status": "active"
}
```
