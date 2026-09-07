from __future__ import annotations

from pathlib import Path
import typer
from formicx.client.daemon_client import DaemonClient, DaemonClientError

agent_app = typer.Typer(
    help="Manage Formicx agents.",
    no_args_is_help=True,
)


def _get_client() -> DaemonClient:
    return DaemonClient()


@agent_app.command("register")
def agent_register(
    path: str = typer.Argument(
        ...,
        help="Path to the agent directory or agent.yaml manifest file.",
    )
) -> None:
    """Register an agent directory or manifest with formicxd.

    Examples:
        formicx agent register ./agents/hello-agent
        formicx agent register ./agents/hello-agent/agent.yaml
    """
    try:
        abs_path = Path(path).resolve()
        client = _get_client()
        data = client.register_agent(abs_path)

        typer.echo("Agent registered successfully\n")
        typer.echo(f"Name: {data.get('name')}")
        typer.echo(f"ID: {data.get('agent_id')}")
        typer.echo(f"Status: {str(data.get('status')).upper()}")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@agent_app.command("list")
def agent_list() -> None:
    """List all registered Formicx agents.

    Examples:
        formicx agent list
    """
    try:
        client = _get_client()
        agents = client.list_agents()

        if not agents:
            typer.echo("No registered agents found.")
            return

        header = f"{'ID':<15} {'NAME':<18} {'STATUS':<12} {'PID'}"
        divider = "-" * 55
        typer.echo(header)
        typer.echo(divider)

        for agt in agents:
            aid = agt.get("agent_id", "")
            name = agt.get("name", "")
            status_str = str(agt.get("status", "")).upper()
            pid_str = str(agt.get("pid")) if agt.get("pid") is not None else "-"
            typer.echo(f"{aid:<15} {name:<18} {status_str:<12} {pid_str}")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@agent_app.command("start")
def agent_start(
    agent: str = typer.Argument(
        ...,
        help="Agent name or Agent ID.",
    )
) -> None:
    """Start a registered Formicx agent.

    Examples:
        formicx agent start hello-agent
        formicx agent start agt_a81f3e92
    """
    try:
        client = _get_client()
        data = client.start_agent(agent)

        typer.echo("Agent started successfully\n")
        typer.echo(f"Name: {data.get('name')}")
        typer.echo(f"ID: {data.get('agent_id')}")
        typer.echo(f"Status: {str(data.get('status')).upper()}")
        pid_val = data.get("pid")
        if pid_val:
            typer.echo(f"PID: {pid_val}")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@agent_app.command("stop")
def agent_stop(
    agent: str = typer.Argument(
        ...,
        help="Agent name or Agent ID.",
    )
) -> None:
    """Stop a running Formicx agent.

    Examples:
        formicx agent stop hello-agent
        formicx agent stop agt_a81f3e92
    """
    try:
        client = _get_client()
        data = client.stop_agent(agent)

        typer.echo("Agent stopped successfully\n")
        typer.echo(f"Name: {data.get('name')}")
        typer.echo(f"ID: {data.get('agent_id')}")
        typer.echo(f"Status: {str(data.get('status')).upper()}")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@agent_app.command("restart")
def agent_restart(
    agent: str = typer.Argument(
        ...,
        help="Agent name or Agent ID.",
    )
) -> None:
    """Restart a registered Formicx agent.

    Examples:
        formicx agent restart hello-agent
        formicx agent restart agt_a81f3e92
    """
    try:
        client = _get_client()
        data = client.restart_agent(agent)

        typer.echo("Agent restarted successfully\n")
        typer.echo(f"Name: {data.get('name')}")
        typer.echo(f"ID: {data.get('agent_id')}")
        typer.echo(f"Status: {str(data.get('status')).upper()}")
        pid_val = data.get("pid")
        if pid_val:
            typer.echo(f"PID: {pid_val}")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@agent_app.command("status")
def agent_status(
    agent: str = typer.Argument(
        ...,
        help="Agent name or Agent ID.",
    )
) -> None:
    """Display detailed status for a registered Formicx agent.

    Examples:
        formicx agent status hello-agent
        formicx agent status agt_a81f3e92
    """
    try:
        client = _get_client()
        data = client.get_agent(agent)

        runtime = data.get("runtime", {})
        lang = runtime.get("language", "python")
        framework = runtime.get("framework", "custom")
        pid_str = str(data.get("pid")) if data.get("pid") is not None else "-"

        typer.echo("Agent\n")
        typer.echo(f"Name: {data.get('name')}")
        typer.echo(f"ID: {data.get('agent_id')}\n")
        typer.echo(f"Status: {str(data.get('status')).upper()}\n")
        typer.echo(f"Runtime: {lang} ({framework})")
        typer.echo(f"PID: {pid_str}\n")
        typer.echo("Entrypoint:")
        typer.echo(f"{data.get('entrypoint')}")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
