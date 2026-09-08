"""CLI commands for Formicx agent communication policy inspection."""

import typer
from formicx.client.daemon_client import DaemonClient, DaemonClientError

policy_app = typer.Typer(
    help="Inspect Formicx agent communication policies.",
    no_args_is_help=True,
)


def _get_client() -> DaemonClient:
    return DaemonClient()


@policy_app.command("list")
def policy_list() -> None:
    """List all configured agent communication policies.

    Examples:
        formicx policy list
    """
    try:
        client = _get_client()
        policies = client.list_policies()

        if not policies:
            typer.echo("No explicit communication policies configured (all agents communicate freely by default).")
            return

        typer.echo("Agent Communication Policies\n")
        for source, pol in policies.items():
            allowed = pol.get("allowed_destinations", [])
            typer.echo(f"{source}")
            typer.echo("  Allowed:")
            if not allowed:
                typer.echo("    none")
            else:
                for dest in sorted(allowed):
                    typer.echo(f"    - {dest}")
            typer.echo("")
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@policy_app.command("check")
def policy_check(
    source: str = typer.Argument(..., help="Source agent ID or name."),
    destination: str = typer.Argument(..., help="Destination agent ID or name."),
) -> None:
    """Check whether communication from source to destination is permitted.

    Examples:
        formicx policy check whatsapp-agent mail-agent
        formicx policy check whatsapp-agent research-agent
    """
    try:
        client = _get_client()
        res = client.check_policy(source, destination)
        status_str = str(res.get("status", "UNKNOWN")).upper()
        typer.echo(status_str)
        if status_str == "DENIED":
            raise typer.Exit(code=1)
    except DaemonClientError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
