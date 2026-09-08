# Formicx Phase 5 — Agent Communication Policies Architecture

This document describes the architectural design, configuration schema, and enforcement model of **Agent Communication Policies** in Formicx.

---

## 1. Overview

Agent Communication Policies allow developers to specify optional directional permissions governing inter-agent messaging.

> **Core Rule**: By default, all agents can communicate freely with all other agents. Restrictions are optional and apply to the sender agent.

```text
               AUTHORITATIVE DAEMON ENFORCEMENT

     Agent A ──────► POST /v1/messages ──────► MessageRouter
                                                     │
                                                     ▼
                                         CommunicationPolicyEngine
                                                     │
                                   ┌─────────────────┴────────────────┐
                                   │                                  │
                                ALLOWED                             DENIED
                                   │                                  │
                                   ▼                                  ▼
                            Enqueue Inbox                  403 FORBIDDEN Response
                            Deliver to Agent B             CommunicationDeniedError
```

---

## 2. Configuration Schema

Policies can be loaded from YAML configuration files (e.g., `communication.yaml` or daemon configuration):

```yaml
communication:
  default_policy: allow

agent_policies:
  whatsapp-agent:
    allow:
      - mail-agent
      - calendar-agent

  research-agent:
    allow:
      - web-agent
      - summarizer-agent

  isolated-agent:
    allow: []
```

### Policy Rules
1. **Default Open**: If an agent has no entry in `agent_policies`, its outgoing messages are **ALLOWED** by default.
2. **Explicit Allow List**: If an agent is defined in `agent_policies`, only destinations explicitly listed in `allow` are permitted.
3. **Empty Allow List**: Specifying `allow: []` explicitly prevents the agent from initiating communication with any other agent.
4. **Directionality**: Permitting `A -> B` does NOT imply `B -> A`. Permissions are evaluated independently for every sender.

---

## 3. Authoritative Daemon Enforcement

All communication policies are enforced by trusted infrastructure inside `formicxd` (`MessageRouter`). Child agent processes running in isolated operating system processes cannot bypass policy enforcement.

If a communication attempt is prohibited by policy:
- `MessageRouter.route()` raises `CommunicationDeniedError`.
- `formicxd` returns an **HTTP 403 Forbidden** JSON response.
- `LocalHTTPTransport` maps HTTP 403 to `CommunicationDeniedError` in the Agent SDK.

---

## 4. Broadcast & Reply Semantics

- **Broadcast (`broadcast()`)**: Checks policy permissions individually for each target. Messages are delivered to allowed recipients and silently skipped for denied recipients. The call does not raise an exception.
- **Reply (`reply()`)**: Replies are evaluated through the policy engine like any standard message based on `(reply_sender, reply_recipient)`.

---

## 5. CLI Policy Commands

Formicx provides `formicx policy` subcommands for policy inspection:

```bash
# List all configured communication policies
formicx policy list

# Check if communication from source to destination is permitted
formicx policy check whatsapp-agent mail-agent
formicx policy check whatsapp-agent research-agent
```
