"""CLI entrypoint for formicx-mcp binary."""

from __future__ import annotations

import sys
from formicx.mcp.server import FormicxMCPServer


def main() -> None:
    """Run the Formicx Model Context Protocol (MCP) server over STDIO."""
    server = FormicxMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
