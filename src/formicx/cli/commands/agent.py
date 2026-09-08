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


import ast
import re
from string import Template
from typing import Optional

from formicx.manifests.loader import load_agent_manifest


def _validate_agent_name(name: str) -> None:
    if not name or not name.strip():
        raise ValueError("Agent name cannot be empty.")
    stripped = name.strip()
    if ".." in stripped or "/" in stripped or "\\" in stripped:
        raise ValueError(f"Invalid agent name '{name}': Path traversal characters are not allowed.")
    if not re.match(r"^[a-zA-Z0-9_-]+$", stripped):
        raise ValueError(
            f"Invalid agent name '{name}': Only alphanumeric characters, hyphens, and underscores are allowed."
        )


def _to_class_name(name: str) -> str:
    parts = re.split(r"[-_]+", name)
    return "".join(p.capitalize() for p in parts if p)


def _to_snake_name(name: str) -> str:
    return name.replace("-", "_").lower()


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


@agent_app.command("create")
def agent_create(
    name: str = typer.Argument(..., help="Name of the new agent project to create."),
    template: str = typer.Option("basic", "--template", "-t", help="Template to use (default: basic)."),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Optional custom output directory."),
) -> None:
    """Create a new Formicx agent project from a template.

    Examples:
        formicx agent create research-agent
        formicx agent create hello-agent --template basic
    """
    try:
        _validate_agent_name(name)

        target_dir = Path(output_dir).resolve() if output_dir else (Path.cwd() / name).resolve()

        if not target_dir.name or target_dir.name in (".", ".."):
            typer.echo(f"Error: Invalid target path '{target_dir}'.", err=True)
            raise typer.Exit(code=1)

        if target_dir.exists():
            typer.echo(f"Error: Directory '{target_dir}' already exists.", err=True)
            raise typer.Exit(code=1)

        package_root = Path(__file__).resolve().parent.parent.parent
        template_dir = package_root / "templates" / f"{template}-agent"
        if not template_dir.exists():
            template_dir = package_root / "templates" / template

        if not template_dir.exists() or not template_dir.is_dir():
            typer.echo(f"Error: Template '{template}' not found.", err=True)
            raise typer.Exit(code=1)

        class_name = _to_class_name(name)
        snake_name = _to_snake_name(name)
        substitutions = {
            "AGENT_NAME": name,
            "AGENT_CLASS_NAME": class_name,
            "AGENT_SNAKE_NAME": snake_name,
        }

        target_dir.mkdir(parents=True, exist_ok=True)
        tests_dir = target_dir / "tests"
        tests_dir.mkdir(exist_ok=True)

        for item in template_dir.glob("*.template"):
            base_name = item.stem  # e.g., agent.yaml, agent.py, README.md, test_agent.py
            with open(item, "r", encoding="utf-8") as f:
                content = f.read()

            rendered = Template(content).safe_substitute(substitutions)

            if base_name == "test_agent.py":
                dest_file = tests_dir / base_name
            else:
                dest_file = target_dir / base_name

            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(rendered)

        typer.echo(f"Created Formicx agent project:\n")
        typer.echo(f"  {name}/")
        typer.echo("    agent.yaml")
        typer.echo("    agent.py")
        typer.echo("    README.md")
        typer.echo("    tests/")
        typer.echo("      test_agent.py\n")
        typer.echo("Next steps:")
        typer.echo(f"  cd {name}")
        typer.echo("  formicx agent validate .")
        typer.echo("  formicx agent register .")
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as exc:
        typer.echo(f"Error creating agent project: {exc}", err=True)
        raise typer.Exit(code=1)


@agent_app.command("validate")
def agent_validate(
    path: str = typer.Argument(".", help="Path to the agent directory or agent.yaml manifest file.")
) -> None:
    """Validate a Formicx agent project manifest and entrypoint syntax.

    Examples:
        formicx agent validate .
        formicx agent validate ./agents/hello-agent
    """
    try:
        target_path = Path(path).resolve()
        if not target_path.exists():
            typer.echo(f"Error: Path '{target_path}' does not exist.", err=True)
            raise typer.Exit(code=1)

        if target_path.is_dir():
            manifest_path = target_path / "agent.yaml"
        else:
            manifest_path = target_path

        if not manifest_path.exists() or not manifest_path.is_file():
            typer.echo(f"Agent validation failed.\n\n✗ Manifest not found: {manifest_path}", err=True)
            raise typer.Exit(code=1)

        # 1. Validate manifest schema
        try:
            agent = load_agent_manifest(manifest_path)
        except Exception as exc:
            typer.echo(f"Agent validation failed.\n\n✗ Invalid manifest '{manifest_path}': {exc}", err=True)
            raise typer.Exit(code=1)

        # 2. Validate entrypoint python syntax without executing code
        entrypoint_path = Path(agent.entrypoint).resolve()
        if not entrypoint_path.exists() or not entrypoint_path.is_file():
            typer.echo(f"Agent validation failed.\n\n✗ Entrypoint file not found: {entrypoint_path}", err=True)
            raise typer.Exit(code=1)

        try:
            with open(entrypoint_path, "r", encoding="utf-8") as f:
                code_text = f.read()
            ast.parse(code_text, filename=str(entrypoint_path))
        except SyntaxError as exc:
            typer.echo(
                f"Agent validation failed.\n\n✗ Python syntax error in entrypoint '{entrypoint_path}' (line {exc.lineno}): {exc.msg}",
                err=True,
            )
            raise typer.Exit(code=1)

        typer.echo("Agent validation successful.\n")
        typer.echo(f"✓ Manifest found: {manifest_path.name}")
        typer.echo("✓ Manifest valid")
        typer.echo(f"✓ Entrypoint found: {entrypoint_path.name}")
        typer.echo("✓ Python syntax valid\n")
        typer.echo("Agent is ready for registration.")
    except typer.Exit:
        raise
    except Exception as exc:
        typer.echo(f"Error during validation: {exc}", err=True)
        raise typer.Exit(code=1)

