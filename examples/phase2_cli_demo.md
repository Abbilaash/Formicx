# Formicx Phase 2 — CLI + Daemon Control Plane Demonstration Walkthrough

This document outlines the step-by-step terminal workflow for operating the Formicx Control Plane using `formicxd` and `formicx`.

---

## Prerequisites

Install Formicx in editable mode with CLI scripts:

```bash
pip install -e ".[dev]"
```

---

## Workflow Demonstration

### Terminal 1 — Start the Formicx Daemon

Launch the daemon:

```bash
formicxd
```

Output:
```text
Formicx daemon started.
Local control interface available on http://127.0.0.1:8765
Listening on localhost only.
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

---

### Terminal 2 — Developer CLI Operations

#### 1. Check Daemon Health & Status

```bash
formicx daemon health
```
Output:
```text
formicxd is running and reachable.
```

```bash
formicx daemon status
```
Output:
```text
Formicx Daemon

Status: RUNNING

Managed Agents: 0
Running Agents: 0
```

---

#### 2. Register Agents

Register the demonstration agents:

```bash
formicx agent register ./agents/hello-agent
```
Output:
```text
Agent registered successfully

Name: hello-agent
ID: agt_a81f3e92
Status: CREATED
```

```bash
formicx agent register ./agents/worker-agent
```
Output:
```text
Agent registered successfully

Name: worker-agent
ID: agt_b92c4d11
Status: CREATED
```

---

#### 3. Start Agents

Start `hello-agent`:

```bash
formicx agent start hello-agent
```
Output:
```text
Agent started successfully

Name: hello-agent
ID: agt_a81f3e92
Status: RUNNING
PID: 43210
```

---

#### 4. List Registered Agents

```bash
formicx agent list
```
Output:
```text
ID              NAME               STATUS       PID
-------------------------------------------------------
agt_a81f3e92    hello-agent        RUNNING      43210
agt_b92c4d11    worker-agent       CREATED      -
```

---

#### 5. Inspect Agent Details

```bash
formicx agent status hello-agent
```
Output:
```text
Agent

Name: hello-agent
ID: agt_a81f3e92

Status: RUNNING

Runtime: python (custom)
PID: 43210

Entrypoint:
a:\PROJECTS\Formicx\agents\hello-agent\main.py
```

---

#### 6. Stop Agent

```bash
formicx agent stop hello-agent
```
Output:
```text
Agent stopped successfully

Name: hello-agent
ID: agt_a81f3e92
Status: STOPPED
```
