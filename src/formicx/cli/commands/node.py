"""Formicx CLI Node & Peer Management Commands."""

import typer
from rich.console import Console
from rich.table import Table

from formicx.client.daemon_client import DaemonClient, DaemonClientError

node_app = typer.Typer(name="node", help="Inspect Formicx node and peer network details.", no_args_is_help=True)
console = Console()


def get_client() -> DaemonClient:
    return DaemonClient()


@node_app.command("info")
def node_info() -> None:
    """Display information about the local Formicx node."""
    client = get_client()
    try:
        info = client.get_node_info()
    except DaemonClientError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(code=1)

    table = Table(title="Formicx Node Information", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Name", str(info.get("name")))
    table.add_row("Host", str(info.get("host")))
    table.add_row("Port", str(info.get("port")))
    table.add_row("Status", str(info.get("status")))

    console.print(table)


@node_app.command("peers")
def node_peers() -> None:
    """List known remote peer nodes in the Formicx network."""
    client = get_client()
    try:
        peers = client.list_peers()
    except DaemonClientError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(code=1)

    if not peers:
        console.print("[yellow]No registered peer nodes.[/yellow]")
        return

    table = Table(title="Known Peer Nodes", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="bold cyan")
    table.add_column("Host", style="green")
    table.add_column("Port", style="green")
    table.add_column("Status", style="yellow")

    for peer in peers:
        table.add_row(
            peer.get("name", ""),
            peer.get("host", ""),
            str(peer.get("port", "")),
            peer.get("status", "UNKNOWN"),
        )

    console.print(table)


@node_app.command("ping")
def node_ping(peer_name: str = typer.Argument(..., help="Name of the peer node to ping")) -> None:
    """Ping a remote Formicx peer node to check reachability and latency."""
    client = get_client()
    try:
        res = client.ping_peer(peer_name)
    except DaemonClientError as exc:
        console.print(f"[bold red]Error:[/] Ping failed for peer '{peer_name}': {exc}")
        raise typer.Exit(code=1)

    status_str = res.get("status", "UNKNOWN")
    latency = res.get("latency_ms", "N/A")
    host = res.get("host", "")
    port = res.get("port", "")

    if status_str == "ONLINE":
        console.print(
            f"[bold green]ONLINE[/bold green] Ping to peer '[bold cyan]{peer_name}[/bold cyan]' "
            f"({host}:{port}) succeeded in [bold yellow]{latency} ms[/bold yellow]."
        )
    else:
        console.print(f"[bold red]OFFLINE[/bold red] Peer '[bold cyan]{peer_name}[/bold cyan]' status: {status_str}")
