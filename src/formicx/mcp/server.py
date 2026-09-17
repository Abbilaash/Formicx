"""Formicx Model Context Protocol (MCP) Server Implementation."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, List, Optional

from formicx.client.daemon_client import DaemonClient, DaemonClientError

logger = logging.getLogger("formicx.mcp.server")

DOCUMENTATION_TOPICS = {
    "overview": (
        "# Formicx Overview & Core Philosophy\n\n"
        "Formicx is an open-source Linux-based operating environment designed specifically for "
        "developing, deploying, running, and coordinating persistent autonomous AI agents.\n\n"
        "**Core Philosophy:** *Linux manages processes. Formicx manages agents.*\n\n"
        "Key Capabilities:\n"
        "- 1:1 Kernel PID Mapping with first-class operational identities\n"
        "- Supervisor Daemon (`formicxd`) for background lifecycle governance\n"
        "- High-level Python SDK (`formicx.Agent`) for event-driven messaging\n"
        "- Developer CLI control plane (`formicx`)\n"
        "- Zero-config mDNS LAN peer node discovery\n"
        "- Authoritative ACL policy control plane\n"
    ),
    "sdk": (
        "# Formicx Agent SDK Reference\n\n"
        "Build autonomous agents by subclassing `formicx.Agent`:\n\n"
        "```python\n"
        "from formicx import Agent\n\n\n"
        "class MyAgent(Agent):\n"
        "    def on_start(self):\n"
        "        print(f'[{self.name}] Agent active with ID {self.id}')\n\n"
        "    def on_message(self, message):\n"
        "        # message.sender: Sender agent ID or name\n"
        "        # message.payload: Dict containing JSON payload\n"
        "        payload = message.payload or {}\n"
        "        action = payload.get('action')\n\n"
        "        if action == 'my_action':\n"
        "            # Process task...\n"
        "            self.reply(\n"
        "                message,\n"
        "                {\n"
        "                    'status': 'success',\n"
        "                    'result': 'task_output',\n"
        "                }\n"
        "            )\n\n"
        "    def on_stop(self):\n"
        "        print(f'[{self.name}] Stopping cleanly.')\n\n\n"
        "if __name__ == '__main__':\n"
        "    MyAgent().run()\n"
        "```\n\n"
        "Key SDK Methods:\n"
        "- `self.send(to, payload)`: Send message to another agent.\n"
        "- `self.reply(message, payload)`: Reply to an incoming message.\n"
        "- `self.broadcast(payload)`: Broadcast event to all agents.\n"
        "- `self.stop()`: Signal agent loop to terminate.\n"
    ),
    "manifest": (
        "# Formicx Agent Manifest Specification (`agent.yaml`)\n\n"
        "Every Formicx agent directory must contain an `agent.yaml` manifest:\n\n"
        "```yaml\n"
        "name: calculator-agent\n"
        "version: 0.1.0\n\n"
        "runtime:\n"
        "  language: python\n"
        "  framework: custom\n\n"
        "entrypoint: main.py\n\n"
        "capabilities:\n"
        "  - add\n"
        "  - subtract\n\n"
        "permissions: []\n"
        "```\n\n"
        "Fields:\n"
        "- `name`: Unique display name of the agent.\n"
        "- `version`: SemVer string.\n"
        "- `runtime`: Specifies execution environment (`python`).\n"
        "- `entrypoint`: Relative path to Python executable script.\n"
        "- `capabilities`: List of capability tags offered by the agent.\n"
    ),
    "cli": (
        "# Formicx Developer CLI Reference\n\n"
        "Start Daemon:\n"
        "  `formicxd`\n\n"
        "Manage Agents:\n"
        "  `formicx agent register ./agent-dir`  # Register manifest\n"
        "  `formicx agent start agent-name`      # Start process\n"
        "  `formicx agent stop agent-name`       # Stop process\n"
        "  `formicx agent list`                  # List agents and PIDs\n"
        "  `formicx agent status agent-name`     # Detailed state\n\n"
        "Messaging & Output:\n"
        "  `formicx message send sender recipient '{\"action\":\"task\"}'`\n"
        "  `formicx message history agent-name`  # Inspect inbox log\n"
        "  `formicx message inbox agent-name`    # Inspect unread messages\n\n"
        "MCP Server:\n"
        "  `formicx mcp start`                   # Run STDIO MCP server\n"
        "  `formicx mcp tools`                   # List exposed MCP tools\n"
    ),
    "mcp": (
        "# Formicx MCP Integration Guide\n\n"
        "The Formicx MCP Server (`formicx-mcp` or `formicx mcp start`) exposes Formicx capabilities "
        "to AI coding assistants (Antigravity, Cursor, Claude Desktop, Copilot) via standard STDIO JSON-RPC.\n\n"
        "Configuration in `mcpServers`:\n"
        "```json\n"
        "{\n"
        "  \"mcpServers\": {\n"
        "    \"formicx\": {\n"
        "      \"command\": \"formicx-mcp\",\n"
        "      \"args\": []\n"
        "    }\n"
        "  }\n"
        "}\n"
        "```\n"
    ),
}

TOOL_DEFINITIONS = [
    {
        "name": "formicx_get_documentation",
        "description": "Fetch complete documentation, architecture specs, SDK references, manifest schemas, and CLI guides for Formicx.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic name: 'all', 'overview', 'sdk', 'manifest', 'cli', or 'mcp'. Default: 'all'.",
                },
            },
        },
    },
    {
        "name": "formicx_list_agents",
        "description": "List all registered Formicx agents, their current statuses (CREATED, RUNNING, STOPPED, FAILED), and operational PIDs.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "formicx_register_agent",
        "description": "Register an agent directory or agent.yaml manifest with the formicxd daemon.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the agent directory or manifest file.",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "formicx_start_agent",
        "description": "Start a registered Formicx agent process by name or Agent ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Registered agent name or ID.",
                },
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "formicx_stop_agent",
        "description": "Gracefully stop a running Formicx agent process by name or Agent ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Registered agent name or ID.",
                },
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "formicx_send_message",
        "description": "Send a message or task payload to a Formicx agent inbox.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sender": {
                    "type": "string",
                    "description": "Sender registered agent name or ID.",
                },
                "recipient": {
                    "type": "string",
                    "description": "Recipient agent name or ID.",
                },
                "payload": {
                    "type": "object",
                    "description": "JSON payload object containing parameters/task data.",
                },
                "type": {
                    "type": "string",
                    "description": "Message type (REQUEST, RESPONSE, EVENT, NOTIFICATION). Default: REQUEST.",
                },
                "correlation_id": {
                    "type": "string",
                    "description": "Optional correlation ID for message tracking.",
                },
            },
            "required": ["sender", "recipient", "payload"],
        },
    },
    {
        "name": "formicx_get_inbox",
        "description": "Inspect pending inbox messages or message history for a Formicx agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Target agent name or ID.",
                },
                "history": {
                    "type": "boolean",
                    "description": "If true, returns historical messages; if false, pending inbox.",
                },
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "formicx_daemon_status",
        "description": "Retrieve overall operational metrics, node health, and managed process stats from the formicxd daemon.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]

RESOURCE_DEFINITIONS = [
    {
        "uri": f"formicx://docs/{topic}",
        "name": f"Formicx {topic.upper()} Documentation",
        "description": f"Documentation and context guide for Formicx {topic}.",
        "mimeType": "text/markdown",
    }
    for topic in DOCUMENTATION_TOPICS.keys()
]

PROMPT_DEFINITIONS = [
    {
        "name": "formicx_context_guide",
        "description": "Provides full context on how to create, register, run, and interact with Formicx agents.",
        "arguments": [],
    }
]


class FormicxMCPServer:
    """STDIO Model Context Protocol (MCP) Server for Formicx."""

    def __init__(self, daemon_client: Optional[DaemonClient] = None) -> None:
        self.client = daemon_client or DaemonClient()

    def get_documentation(self, topic: str = "all") -> str:
        """Return markdown documentation for Formicx."""
        topic_clean = topic.strip().lower()
        if topic_clean == "all" or not topic_clean:
            return "\n\n---\n\n".join(DOCUMENTATION_TOPICS.values())
        return DOCUMENTATION_TOPICS.get(
            topic_clean, f"Unknown topic '{topic}'. Available topics: {', '.join(DOCUMENTATION_TOPICS.keys())}, all."
        )

    def handle_tool_call(self, name: str, args: Dict[str, Any]) -> Any:
        """Execute a Formicx MCP tool call."""
        try:
            if name == "formicx_get_documentation":
                topic = args.get("topic", "all")
                return self.get_documentation(topic)
            elif name == "formicx_list_agents":
                return self.client.list_agents()
            elif name == "formicx_register_agent":
                path = args.get("path", "")
                return self.client.register_agent(path)
            elif name == "formicx_start_agent":
                identifier = args.get("identifier", "")
                return self.client.start_agent(identifier)
            elif name == "formicx_stop_agent":
                identifier = args.get("identifier", "")
                return self.client.stop_agent(identifier)
            elif name == "formicx_send_message":
                sender = args.get("sender", "")
                recipient = args.get("recipient", "")
                payload = args.get("payload", {})
                msg_type = args.get("type", "REQUEST")
                correlation_id = args.get("correlation_id")
                return self.client.send_message(
                    sender=sender,
                    recipient=recipient,
                    message_type=msg_type.upper(),
                    payload=payload,
                    correlation_id=correlation_id,
                )
            elif name == "formicx_get_inbox":
                identifier = args.get("identifier", "")
                history = bool(args.get("history", False))
                return self.client.get_inbox(identifier, history=history)
            elif name == "formicx_daemon_status":
                return self.client.daemon_status()
            else:
                raise ValueError(f"Unknown tool: {name}")
        except DaemonClientError as exc:
            return {"error": str(exc), "status": "failed"}

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process an incoming JSON-RPC MCP request."""
        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {},
                    },
                    "serverInfo": {
                        "name": "formicx-mcp",
                        "version": "0.1.0",
                    },
                },
            }
        elif method in ("notifications/initialized", "notifications/cancelled"):
            return None
        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": TOOL_DEFINITIONS,
                },
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            result = self.handle_tool_call(tool_name, tool_args)
            result_text = result if isinstance(result, str) else json.dumps(result, indent=2)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text,
                        }
                    ]
                },
            }
        elif method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "resources": RESOURCE_DEFINITIONS,
                },
            }
        elif method == "resources/read":
            uri = params.get("uri", "")
            topic = uri.replace("formicx://docs/", "")
            doc_text = self.get_documentation(topic)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "text/markdown",
                            "text": doc_text,
                        }
                    ]
                },
            }
        elif method == "prompts/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "prompts": PROMPT_DEFINITIONS,
                },
            }
        elif method == "prompts/get":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "description": "Formicx Full System Context Guide for AI Coding Agents",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": (
                                    "You are an expert AI assistant working with Formicx.\n\n"
                                    + self.get_documentation("all")
                                ),
                            },
                        }
                    ],
                },
            }
        else:
            if req_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }
            return None

    def run_stdio(self) -> None:
        """Run the STDIO JSON-RPC loop reading stdin and writing stdout."""
        sys.stderr.write("[formicx-mcp] Formicx MCP Server running on STDIO...\n")
        sys.stderr.flush()

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                res = self.handle_request(req)
                if res is not None:
                    sys.stdout.write(json.dumps(res) + "\n")
                    sys.stdout.flush()
            except Exception as exc:
                sys.stderr.write(f"[formicx-mcp] Error: {exc}\n")
                sys.stderr.flush()
