# Formicx Specification: Node Primitive

## Definition
A **Node** represents a physical machine, workstation, single-board computer (such as a Raspberry Pi), or cloud VM running the Formicx operating environment.

## Primitive Fields

### `NodeResources`
| Field | Type | Description | Required | Validation |
|---|---|---|---|---|
| `cpu_cores` | `int` | Number of available CPU cores. | Yes | `> 0` |
| `memory_mb` | `int` | Available system RAM in megabytes. | Yes | `> 0` |

### `Node`
| Field | Type | Description | Required | Validation |
|---|---|---|---|---|
| `node_id` | `str` | Unique node identifier (e.g. `node_12345678`). Automatically generated if omitted. | Yes | Non-empty |
| `name` | `str` | Name of the host device (e.g. `home-pi`). | Yes | Non-empty |
| `architecture` | `str` | CPU architecture string (e.g. `arm64`, `x86_64`). | Yes | Non-empty |
| `resources` | `NodeResources` | Embedded CPU and RAM specifications. | Yes | Validated nested model |
| `status` | `NodeStatus` | Current operational state. Default: `ONLINE`. | Yes | Enum match (`ONLINE`, `OFFLINE`, `UNAVAILABLE`) |

---

## Python Representation

```python
from formicx.models import Node, NodeResources
from formicx.enums import NodeStatus

node = Node(
    name="home-pi",
    architecture="arm64",
    resources=NodeResources(
        cpu_cores=4,
        memory_mb=8192
    ),
    status=NodeStatus.ONLINE
)
```

---

## JSON Serialization Example

```json
{
  "node_id": "node_12345678",
  "name": "home-pi",
  "architecture": "arm64",
  "resources": {
    "cpu_cores": 4,
    "memory_mb": 8192
  },
  "status": "online"
}
```
