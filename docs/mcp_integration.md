# Formicx Model Context Protocol (MCP) Integration Guide

The **Formicx MCP Server** (`formicx-mcp`) allows AI coding assistants (such as **Antigravity**, **Cursor**, **Claude Desktop**, and **VS Code**) to manage Formicx agents, register manifests, inspect telemetry, and send tasks directly from the IDE interface.

---

## 1. Quickstart

### Start via Executable
```bash
formicx-mcp
```

### Start via Formicx CLI
```bash
formicx mcp start
```

### Inspect Available MCP Tools
```bash
formicx mcp tools
```

---

## 2. Configuration for AI Coding Assistants

### **Antigravity / Cursor / Claude Desktop / VS Code**

Add `formicx` to your `mcpServers` configuration:

```json
{
  "mcpServers": {
    "formicx": {
      "command": "formicx-mcp",
      "args": []
    }
  }
}
```

*Note: Ensure `formicxd` is running in the background (`formicxd`) so the MCP server can reach the Formicx control plane API.*

---

## 3. Available MCP Tools

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `formicx_list_agents` | `status: str` (optional) | List all registered Formicx agents, their statuses, and operational PIDs. |
| `formicx_register_agent` | `path: str` | Register an agent manifest directory or `agent.yaml` file with `formicxd`. |
| `formicx_start_agent` | `identifier: str` | Start a registered Formicx agent process. |
| `formicx_stop_agent` | `identifier: str` | Gracefully stop a running Formicx agent process. |
| `formicx_send_message` | `sender: str`, `recipient: str`, `payload: dict`, `type: str` | Send a message/task payload to a Formicx agent inbox. |
| `formicx_get_inbox` | `identifier: str`, `history: bool` | Fetch pending or historical inbox messages for an agent. |
| `formicx_daemon_status` | *None* | Retrieve daemon metrics, node health, and process counts. |

---

## 4. Example Prompts in AI Assistants

Once configured, you can prompt your AI assistant directly:

- *"List all running Formicx agents on my machine."*
- *"Register the calculator agent in `./calculator-agent` and start it."*
- *"Send an add request `{action: 'add', a: 10, b: 20}` to calculator-agent and show me the output."*
