from __future__ import annotations

import sys
import typer
from formicx.client.daemon_client import DaemonClient, DaemonClientError

daemon_app = typer.Typer(
    help="Inspect and manage the Formicx daemon runtime.",
    no_args_is_help=True,
)


def _get_client() -> DaemonClient:
    return DaemonClient()


@daemon_app.command("health")
def daemon_health() -> None:
    """Check whether formicxd is running and reachable.

    Examples:
        formicx daemon health
    """
    try:
        client = _get_client()
        client.health()
        typer.echo("formicxd is running and reachable.")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@daemon_app.command("status")
def daemon_status() -> None:
    """Display operational metrics of the running formicxd daemon.

    Examples:
        formicx daemon status
    """
    try:
        client = _get_client()
        data = client.daemon_status()
        status_str = str(data.get("status", "unknown")).upper()
        managed_count = data.get("managed_agents", 0)
        running_count = data.get("running_agents", 0)

        typer.echo("Formicx Daemon\n")
        typer.echo(f"Status: {status_str}\n")
        typer.echo(f"Managed Agents: {managed_count}")
        typer.echo(f"Running Agents: {running_count}")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
