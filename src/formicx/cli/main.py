from __future__ import annotations

from typing import Optional
import typer

from formicx.cli.commands.agent import agent_app
from formicx.cli.commands.daemon import daemon_app
from formicx.cli.commands.message import message_app

app = typer.Typer(
    name="formicx",
    help="Formicx — Agent Operating Environment CLI",
    no_args_is_help=True,
    add_completion=False,
)

app.add_typer(agent_app, name="agent")
app.add_typer(daemon_app, name="daemon")
app.add_typer(message_app, name="message")


@app.command("help")
def custom_help(
    topic: Optional[str] = typer.Argument(
        None,
        help="Optional help topic: 'agent', 'daemon', 'message', or command name.",
    )
) -> None:
    """Display help information and command usage examples.

    Examples:
        formicx help
        formicx help agent
        formicx help daemon
        formicx help message
    """
    if topic is None or topic.lower() in ("global", "main"):
        typer.echo("Formicx — Agent Operating Environment\n")
        typer.echo("Usage:")
        typer.echo("    formicx <command> [options]\n")
        typer.echo("Command Groups:")
        typer.echo("    agent     Manage Formicx agents.")
        typer.echo("    daemon    Inspect the Formicx runtime daemon.")
        typer.echo("    message   Debug and inspect Formicx agent messages.\n")
        typer.echo("Examples:")
        typer.echo("    formicx agent register ./agents/hello-agent")
        typer.echo("    formicx agent start hello-agent")
        typer.echo("    formicx message send coordinator-agent research-agent '{\"task\":\"hello\"}'")
        typer.echo("    formicx message inbox research-agent")
        typer.echo("    formicx daemon status")
    elif topic.lower() == "agent":
        typer.echo("Agent Management Commands:\n")
        typer.echo("    register <path>   Register an agent directory or manifest.")
        typer.echo("    list              List all registered agents.")
        typer.echo("    start <agent>     Start a registered agent.")
        typer.echo("    stop <agent>      Stop a running agent.")
        typer.echo("    restart <agent>   Restart a registered agent.")
        typer.echo("    status <agent>    Display detailed agent status.\n")
        typer.echo("Examples:")
        typer.echo("    formicx agent register ./agents/hello-agent")
        typer.echo("    formicx agent start hello-agent")
    elif topic.lower() == "daemon":
        typer.echo("Daemon Inspection Commands:\n")
        typer.echo("    health            Check if formicxd is reachable.")
        typer.echo("    status            Display operational metrics of formicxd.\n")
        typer.echo("Examples:")
        typer.echo("    formicx daemon health")
        typer.echo("    formicx daemon status")
    elif topic.lower() == "message":
        typer.echo("Message Debugging Commands:\n")
        typer.echo("    send <from> <to> <payload>  Send a message to an agent.")
        typer.echo("    inbox <agent>              Inspect pending inbox messages.")
        typer.echo("    history <agent>            Inspect recent message history.\n")
        typer.echo("Examples:")
        typer.echo("    formicx message send agent-a agent-b '{\"hello\":\"world\"}'")
        typer.echo("    formicx message inbox agent-b")
    else:
        typer.echo(f"Help topic '{topic}': Run 'formicx {topic} --help' for detailed option usage.")


if __name__ == "__main__":
    app()
