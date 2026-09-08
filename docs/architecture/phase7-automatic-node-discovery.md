# Formicx Phase 7 — Automatic Node Discovery Architecture

## 1. Overview
Phase 7 implements **Automatic Formicx Node Discovery** over Local Area Networks (LAN). Built on top of Phase 6 distributed networking, Phase 7 allows `formicxd` daemons to announce their presence, discover peer nodes automatically via UDP broadcasting, maintain peer liveness tracking, and update the in-memory `PeerRegistry` dynamically without requiring manual peer configuration files.

---

## 2. Architecture & Components

```text
┌─────────────────────────────────────────────────────────────┐
│ Formicx Node (formicxd)                                      │
│                                                             │
│ ┌──────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│ │ Agent Runtime    │  │ Message Router  │  │ PeerRegistry │ │
│ └──────────────────┘  └─────────────────┘  └──────▲───────┘ │
│                                                   │         │
│ ┌─────────────────────────────────────────────────┴───────┐ │
│ │ DiscoveryService                                        │ │
│ │                                                         │ │
│ │ ├── Broadcaster Loop (ANNOUNCE / DISCOVER datagrams)    │ │
│ │ ├── Listener Loop (DatagramProtocol on UDP:9999)        │ │
│ │ └── Expiration Monitor (liveness check & timeouts)      │ │
│ └─────────────────────────┬───────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            │ UDP Broadcast (Port 9999)
                            ▼
                     Local Area Network (LAN)
```

### Core Components
- **`DiscoveryMessage`** (`formicx.discovery.protocol`): Datagram payload format (`ANNOUNCE`, `DISCOVER`, `RESPONSE`).
- **`UDPDiscoveryTransport`** (`formicx.discovery.transport`): Manages async socket binding (`SO_BROADCAST`, `SO_REUSEADDR`, `SO_REUSEPORT`).
- **`DiscoveryService`** (`formicx.discovery.service`): Runs background loops for periodic announcements, UDP datagram processing, and peer expiration checks.
- **`PeerRegistry` Extension** (`formicx.communication.peer`): Tracks registration `source` (`"manual"` vs `"discovered"`), `last_seen` timestamps, and `active` liveness state.

---

## 3. UDP Discovery Protocol Format

Formicx discovery messages are lightweight JSON datagrams:

```json
{
  "protocol": "formicx-discovery",
  "version": "1",
  "message_type": "ANNOUNCE",
  "node_name": "raspberry-pi",
  "host": "192.168.1.50",
  "port": 8000,
  "timestamp": 1725838000.0
}
```

### Message Types
- **`ANNOUNCE`**: Periodic broadcast datagram sent by nodes (default every 15s).
- **`DISCOVER`**: Immediate query broadcast by a newly started node requesting active peers to identify themselves.
- **`RESPONSE`**: Direct or broadcast datagram sent by existing active nodes in response to a `DISCOVER` request.

---

## 4. Policy Separation & Peer Lifecycle

1. **Discovery ≠ Authorization**: Node discovery only establishes network reachability in `PeerRegistry`. Phase 5 communication policies remain 100% authoritative when an agent sends a message (`self.send(to="agent@node", ...)`).
2. **Manual Peer Immunity**: Peers loaded from manual YAML/dictionary config (`source: "manual"`) never expire due to discovery timeout.
3. **Discovered Peer Expiration**: Peers added via automatic discovery (`source: "discovered"`) update `last_seen` on each datagram. If no datagram is received within `peer_timeout` (default 60s), the peer is marked `OFFLINE` and inactive.

---

## 5. CLI & Configuration

### Daemon Environment Settings
```bash
FORMICX_DISCOVERY_ENABLED=true
FORMICX_DISCOVERY_PORT=9999
FORMICX_ANNOUNCE_INTERVAL=15.0
FORMICX_PEER_TIMEOUT=60.0
```

### CLI Commands
```bash
# Display node info including discovery metrics
formicx node info

# List discovered and manual peer nodes with status and last seen timestamp
formicx node peers

# Send an immediate LAN discovery request
formicx node discover
```
