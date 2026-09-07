from __future__ import annotations

from typer.testing import CliRunner
from formicx.cli.main import app as cli_app

runner = CliRunner()


def test_cli_global_help():
    res = runner.invoke(cli_app, ["--help"])
    assert res.exit_code == 0
    assert "Formicx — Agent Operating Environment CLI" in res.stdout
    assert "agent" in res.stdout
    assert "daemon" in res.stdout


def test_cli_agent_group_help():
    res = runner.invoke(cli_app, ["agent", "--help"])
    assert res.exit_code == 0
    assert "Manage Formicx agents." in res.stdout
    assert "register" in res.stdout
    assert "list" in res.stdout
    assert "start" in res.stdout
    assert "stop" in res.stdout
    assert "restart" in res.stdout
    assert "status" in res.stdout


def test_cli_daemon_group_help():
    res = runner.invoke(cli_app, ["daemon", "--help"])
    assert res.exit_code == 0
    assert "Inspect and manage the Formicx daemon runtime." in res.stdout
    assert "health" in res.stdout
    assert "status" in res.stdout


def test_cli_specific_command_help():
    res = runner.invoke(cli_app, ["agent", "start", "--help"])
    assert res.exit_code == 0
    assert "Start a registered Formicx agent." in res.stdout
    assert "agent" in res.stdout.lower()


def test_cli_custom_help_command():
    res = runner.invoke(cli_app, ["help"])
    assert res.exit_code == 0
    assert "Formicx — Agent Operating Environment" in res.stdout
    assert "Examples:" in res.stdout

    res = runner.invoke(cli_app, ["help", "agent"])
    assert res.exit_code == 0
    assert "Agent Management Commands:" in res.stdout

    res = runner.invoke(cli_app, ["help", "daemon"])
    assert res.exit_code == 0
    assert "Daemon Inspection Commands:" in res.stdout
