# Phase 6 Specification — Distributed Agent Networking

Formicx Phase 6 introduces distributed agent networking, allowing agents running on separate `formicxd` daemon nodes across a network (e.g. Laptops, Raspberry Pis, Servers) to communicate seamlessly using qualified agent addresses (`agent-name@node-name`) while maintaining 100% backward compatibility with local messaging, communication policies, and SDK abstractions.

---

## 1. High-Level Architecture

Every machine running `formicxd` acts as a **Formicx Node** with a unique node identity (`node_name`).

```text
Laptop (Node: laptop)                       Raspberry Pi (Node: raspberry-pi)

formicxd (port: 8765)                      formicxd (port: 8000)
   │                                           │
   ├── research-agent                          ├── vision-agent
   └── coding-agent                            └── sensor-agent
```

Cross-node communication uses qualified agent addresses:

```text
research-agent@laptop ────── Formicx Network ─────► vision-agent@raspberry-pi
```

---

## 2. Qualified Distributed Agent Identity

Local agent names remain unchanged (`research-agent`). Distributed messages target qualified addresses:

```text
agent-name@node-name
```

Examples:
- `vision-agent@raspberry-pi`
- `sensor-agent@home-server`
- `research-agent@laptop`

The `AgentAddress` domain model validates address strings, rejecting malformed patterns (`@node`, `agent@`, `agent@@node`).

---

## 3. Distributed Message Flow

### Outgoing Remote Message:
1. Agent SDK calls `self.send(to="vision-agent@raspberry-pi", payload=...)`.
2. `MessageRouter` parses the destination address using `AgentAddress`.
3. If destination is remote (`node_name != local_node_name`), `MessageRouter` evaluates local sender policy.
4. `MessageRouter` looks up `raspberry-pi` in `PeerRegistry`.
5. `NetworkHTTPTransport` transmits the message envelope to `http://192.168.1.50:8000/v1/messages/remote`.

### Incoming Remote Message:
1. Destination node's `formicxd` receives HTTP POST `/v1/messages/remote`.
2. The remote endpoint evaluates local policy for the incoming message.
3. `MessageRouter` routes the message to the destination agent's local inbox.

---

## 4. Peer Configuration (`formicx.yaml`)

Configure local node settings and remote peers in `formicx.yaml`:

```yaml
node:
  name: laptop
  host: 0.0.0.0
  port: 8765

peers:
  raspberry-pi:
    host: 192.168.1.50
    port: 8000

  home-server:
    host: 192.168.1.60
    port: 9000
```

---

## 5. CLI Node Commands

Inspect node details, list peers, and ping remote nodes directly from the CLI:

```bash
# Display local node details
formicx node info

# List known remote peers
formicx node peers

# Ping remote peer to check status and latency
formicx node ping raspberry-pi
```
