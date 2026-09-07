"""CLI commands for Formicx agent message debugging."""

import json
from typing import Optional
import typer

from formicx.client.daemon_client import DaemonClient, DaemonClientError

message_app = typer.Typer(
    help="Debug and inspect Formicx agent messages.",
    no_args_is_help=True,
)


def _get_client() -> DaemonClient:
    return DaemonClient()


@message_app.command("send")
def message_send(
    sender: str = typer.Argument(..., help="Sender agent name or ID."),
    recipient: str = typer.Argument(..., help="Recipient agent name or ID."),
    payload: str = typer.Argument(..., help="JSON payload string."),
    type: str = typer.Option("REQUEST", "--type", "-t", help="Message type (REQUEST, RESPONSE, EVENT, NOTIFICATION)."),
    correlation_id: Optional[str] = typer.Option(None, "--correlation-id", "-c", help="Optional correlation ID."),
) -> None:
    """Send a message to a registered agent.

    Examples:
        formicx message send coordinator-agent research-agent '{"task":"Analyze data"}'
        formicx message send agt_001 agt_002 '{"query":"ping"}' --type EVENT
    """
    try:
        raw_payload = payload.strip()
        if (raw_payload.startswith("'") and raw_payload.endswith("'")) or (
            raw_payload.startswith('"') and raw_payload.endswith('"')
        ):
            raw_payload = raw_payload[1:-1].strip()

        payload_dict = None
        # 1. Standard JSON
        try:
            res = json.loads(raw_payload)
            if isinstance(res, dict):
                payload_dict = res
        except Exception:
            pass

        # 2. Python dict literal (ast.literal_eval)
        if payload_dict is None:
            try:
                import ast
                res = ast.literal_eval(raw_payload)
                if isinstance(res, dict):
                    payload_dict = res
            except Exception:
                pass

        # 3. Windows CMD quote-stripping parser: handles '{key:val}' or 'key:val'
        if payload_dict is None:
            clean = raw_payload
            if (clean.startswith("'") and clean.endswith("'")) or (clean.startswith('"') and clean.endswith('"')):
                clean = clean[1:-1].strip()

            if clean.startswith("{") and clean.endswith("}"):
                clean = clean[1:-1].strip()

            if ":" in clean:
                try:
                    parsed = {}
                    for pair in clean.split(","):
                        if ":" in pair:
                            k, v = pair.split(":", 1)
                            k = k.strip().strip('"').strip("'")
                            v = v.strip().strip('"').strip("'")
                            if v.isdigit():
                                v_val: int | str | bool = int(v)
                            elif v.lower() == "true":
                                v_val = True
                            elif v.lower() == "false":
                                v_val = False
                            else:
                                v_val = v
                            parsed[k] = v_val
                    if parsed:
                        payload_dict = parsed
                except Exception:
                    pass

        # 4. PyYAML fallback
        if payload_dict is None:
            try:
                import yaml
                res = yaml.safe_load(raw_payload)
                if isinstance(res, dict) and any(v is not None for v in res.values()):
                    payload_dict = res
            except Exception:
                pass

        if not isinstance(payload_dict, dict):
            typer.echo("Error: Invalid JSON payload: Must be a valid JSON or dictionary object.", err=True)
            raise typer.Exit(code=1)

        client = _get_client()
        result = client.send_message(
            sender=sender,
            recipient=recipient,
            message_type=type.upper(),
            payload=payload_dict,
            correlation_id=correlation_id,
        )

        typer.echo("Message delivered successfully\n")
        typer.echo(f"Message ID: {result.get('message_id')}")
        typer.echo(f"From: {sender}")
        typer.echo(f"To: {recipient} ({result.get('recipient_agent_id')})")
        typer.echo(f"Status: {result.get('status')}")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@message_app.command("inbox")
def message_inbox(
    agent: str = typer.Argument(..., help="Agent name or Agent ID.")
) -> None:
    """Inspect pending unconsumed messages in an agent's inbox.

    Examples:
        formicx message inbox research-agent
        formicx message inbox agt_a81f3e92
    """
    try:
        client = _get_client()
        messages = client.get_inbox(agent, history=False)

        if not messages:
            typer.echo(f"Inbox for agent '{agent}' is empty.")
            return

        header = f"{'ID':<15} {'FROM':<18} {'TYPE':<12} {'PAYLOAD'}"
        divider = "-" * 65
        typer.echo(header)
        typer.echo(divider)

        for msg in messages:
            mid = msg.get("message_id", "")
            sender = msg.get("sender", "")
            msg_type = str(msg.get("message_type", "")).upper()
            payload_str = json.dumps(msg.get("payload", {}))
            if len(payload_str) > 30:
                payload_str = payload_str[:27] + "..."
            typer.echo(f"{mid:<15} {sender:<18} {msg_type:<12} {payload_str}")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@message_app.command("history")
def message_history(
    agent: str = typer.Argument(..., help="Agent name or Agent ID.")
) -> None:
    """Inspect recent message history for an agent.

    Examples:
        formicx message history research-agent
    """
    try:
        client = _get_client()
        messages = client.get_inbox(agent, history=True)

        if not messages:
            typer.echo(f"No message history found for agent '{agent}'.")
            return

        header = f"{'ID':<15} {'FROM':<18} {'TYPE':<12} {'PAYLOAD'}"
        divider = "-" * 65
        typer.echo(header)
        typer.echo(divider)

        for msg in messages:
            mid = msg.get("message_id", "")
            sender = msg.get("sender", "")
            msg_type = str(msg.get("message_type", "")).upper()
            payload_str = json.dumps(msg.get("payload", {}))
            if len(payload_str) > 30:
                payload_str = payload_str[:27] + "..."
            typer.echo(f"{mid:<15} {sender:<18} {msg_type:<12} {payload_str}")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
