# [Professional Feature] feat(ipc): High-Performance Linux Unix Domain Socket Transport for Local IPC

**Labels**: `feature`, `linux`, `ipc`, `performance`, `messaging`  
**Target Files**: `src/formicx/communication/unix_transport.py`, `src/formicx/communication/router.py`

## Overview
Replace TCP/HTTP localhost transport for local agent-to-agent messaging with Linux Unix Domain Sockets (`/var/run/formicx/formicx.sock` or `~/.formicx/formicx.sock`).

## Key Benefits
- **Zero TCP Stack Overhead**: Up to 10x lower latency and higher throughput for local message passing.
- **POSIX File Security**: Protect socket permissions with Linux file modes (`0600` / `0660`) ensuring kernel-enforced process isolation.
- **Streaming Payloads**: Enables fast binary payload streaming between agents.

## Acceptance Criteria
- [ ] Implement `UnixSocketTransport` implementing Formicx `Transport` interface.
- [ ] Auto-detect OS support and use Unix Domain Sockets on Linux/macOS and fallback to TCP on Windows.
- [ ] Add benchmark and integration test suite.
