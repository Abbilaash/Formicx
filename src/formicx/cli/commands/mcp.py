"""CLI commands for Formicx Model Context Protocol (MCP) server."""

import typer
from formicx.mcp.server import FormicxMCPServer

mcp_app = typer.Typer(
    help="Model Context Protocol (MCP) integration for AI coding assistants.",
    no_args_is_help=True,
)


@mcp_app.command("start")
def mcp_start() -> None:
    """Start the Formicx Model Context Protocol (MCP) server on STDIO.

    Examples:
        formicx mcp start
    """
    server = FormicxMCPServer()
    server.run_stdio()


@mcp_app.command("tools")
def mcp_tools() -> None:
    """List available MCP tools exposed by Formicx.

    Examples:
        formicx mcp tools
    """
    from formicx.mcp.server import TOOL_DEFINITIONS
    typer.echo(f"Available Formicx MCP Tools ({len(TOOL_DEFINITIONS)}):\n")
    for tool in TOOL_DEFINITIONS:
        typer.echo(f"  - {tool['name']:<25} {tool['description']}")
