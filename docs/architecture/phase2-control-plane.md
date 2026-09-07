# Formicx Architecture: Phase 2 Control Plane

## Architectural Concept

Phase 2 adds the developer-facing **Control Plane** (`formicx` CLI) to manage the persistent **Formicx Agent Runtime** (`formicxd`).

```text
Developer
    │
    │ Terminal Command (formicx agent list)
    ▼
┌─────────────────┐
│   formicx CLI   │
└────────┬────────┘
         │
         │ Local HTTP Control Request (127.0.0.1:8765)
         ▼
┌─────────────────┐
│    formicxd     │
│    Daemon       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent Manager   │
├─────────────────┤
│ Agent Registry  │
├─────────────────┤
│ Process Manager │
└────────┬────────┘
         │
         ├──── Agent Process A (PID 1001)
         ├──── Agent Process B (PID 1002)
         └──── Agent Process C (PID 1003)
```

---

## Key Design Rules

1. **Daemon Runtime Ownership:** `formicxd` is the sole owner of the `AgentManager` instance, `AgentRegistry`, and child process handles.
2. **CLI Client Separation:** The `formicx` CLI is a thin client invoking `DaemonClient`. The CLI never instantiates its own `AgentManager` or accesses internal process handles directly.
3. **Local Loopback Security:** The FastAPI control server inside `formicxd` binds strictly to `127.0.0.1:8765` and is inaccessible from external network interfaces.
4. **Control Plane vs. Communication Plane:**
   - **Control Plane (Phase 2):** Synchronous HTTP command interface (`CLI -> formicxd`).
   - **Communication Plane (Future Phase):** Asynchronous inter-agent messaging channels (`Agent -> Agent`).

---

## Control API Routes (`127.0.0.1:8765`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/health` | Daemon health check (`{"status": "ok", "daemon": "formicxd"}`). |
| `GET` | `/v1/daemon/status` | Managed and running agent counts. |
| `POST` | `/v1/agents/register` | Register an agent directory or manifest (`{"path": "..."}`). |
| `GET` | `/v1/agents` | List all registered agents. |
| `GET` | `/v1/agents/{identifier}` | Get detailed agent status by ID or name. |
| `POST` | `/v1/agents/{identifier}/start` | Start an agent process. |
| `POST` | `/v1/agents/{identifier}/stop` | Stop a running agent process. |
| `POST` | `/v1/agents/{identifier}/restart` | Restart an agent process. |

---

## Error Handling Philosophy

If `formicxd` is not running when a CLI command is executed, `DaemonClient` catches low-level socket connection failures and displays a clean error without Python stack traces:

```text
Unable to connect to formicxd.

The Formicx daemon does not appear to be running.

Start it with:

    formicxd
```
