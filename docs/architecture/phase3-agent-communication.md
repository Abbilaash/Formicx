# Formicx Phase 3 Architecture: Native Agent Communication Layer

## Overview

Phase 3 introduces the native **Agent-to-Agent Communication Layer** to Formicx. This layer enables independent OS-level agent processes managed by `formicxd` to discover each other, route structured messages, and receive correlated responses without coupling to transport protocols or daemon internals.

The core principle remains:
> **Linux manages processes. Formicx manages agents and agent communication.**

---

## Communication Architecture

```text
                                formicxd
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │ Communication       │
                        │ Service             │
                        └──────────┬──────────┘
                                   │
                        ┌──────────┴──────────┐
                        │ Message Router      │
                        └──────────┬──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
         Agent Inbox          Agent Inbox          Agent Inbox
          (Agent A)            (Agent B)            (Agent C)
              │                    │                    │
              ▼                    ▼                    ▼
           Agent A              Agent B              Agent C
```

---

## Component Breakdown

1. **Message Router (`MessageRouter`)**
   - Routes structured `Message` objects into target agent inboxes.
   - Resolves target recipients by canonical `Agent ID` or unique `Agent Name`.
   - Protects queue operations with thread-safe synchronization locks.
   - Enforces identity verification against `AgentRegistry`.

2. **Agent Inbox (`AgentInbox`)**
   - In-memory thread-safe pending queue (`queue.Queue`) and historical log.
   - `receive_next(timeout)` consumes and removes pending messages.
   - `peek()` inspects pending inbox messages without consuming.
   - `list_history()` returns historical messages for debugging.

3. **Agent Discovery (`AgentDiscoveryService`)**
   - Queries `AgentRegistry` as single source of truth.
   - Resolves direct `agent_id` or unique `name`.
   - Raises `AmbiguousAgentError` if multiple registered agents share a name.
   - Supports filtering by status (e.g. `RUNNING`).

4. **Transport Layer (`MessageTransport` / `LocalHTTPTransport`)**
   - Abstract interface hiding network/HTTP details from agent developers.
   - `LocalHTTPTransport` communicates with `formicxd` over localhost (`127.0.0.1:8765`).

5. **Agent SDK (`AgentContext`)**
   - Developer SDK for agent scripts.
   - Auto-detects process identity via `FORMICX_AGENT_ID` and `FORMICX_AGENT_NAME` injected into subprocesses.
   - High-level primitives: `send()`, `receive()`, `reply()`, `discover()`, `get_agent()`, `broadcast()`.

---

## Message Contract & Correlation

Every message adheres to the `Message` model contract:

```json
{
  "message_id": "msg_a1b2c3d4",
  "sender": "agt_coord_01",
  "recipient": "agt_res_02",
  "message_type": "REQUEST",
  "payload": {
    "question": "What is the capital of France?"
  },
  "timestamp": "2026-09-07T18:00:00Z",
  "correlation_id": null
}
```

When replying using `context.reply(original_msg, payload)`:
- `recipient` is automatically set to `original_msg.sender`
- `correlation_id` is set to `original_msg.message_id`
- `message_type` defaults to `RESPONSE`

---

## Daemon API Routes

- `POST /v1/messages`: Route a new message to an agent inbox.
- `GET /v1/agents/{identifier}/messages/next?timeout=5`: Consume next pending message. Returns 204 if empty.
- `GET /v1/agents/{identifier}/messages?history=false`: Inspect pending inbox (or history if `history=true`).
- `POST /v1/messages/broadcast`: Broadcast payload to all registered agents.

---

## CLI Debugging Commands

```bash
# Send a message to an agent
formicx message send coordinator-agent research-agent '{"question":"What is 2+2?"}'

# Inspect unconsumed pending inbox
formicx message inbox research-agent

# Inspect recent message history
formicx message history research-agent
```
