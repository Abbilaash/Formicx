from pathlib import Path
import pytest
from typer.testing import CliRunner

from formicx.cli.main import app as cli_app
from formicx.client.daemon_client import DaemonClient

runner = CliRunner()


def test_cli_policy_help():
    res = runner.invoke(cli_app, ["policy", "--help"])
    assert res.exit_code == 0
    assert "Inspect Formicx agent communication policies" in res.stdout


def test_cli_policy_list_empty(monkeypatch):
    monkeypatch.setattr(DaemonClient, "list_policies", lambda self: {})

    res = runner.invoke(cli_app, ["policy", "list"])
    assert res.exit_code == 0
    assert "No explicit communication policies configured" in res.stdout


def test_cli_policy_list_with_policies(monkeypatch):
    fake_policies = {
        "whatsapp-agent": {
            "source_agent_id": "whatsapp-agent",
            "allowed_destinations": ["mail-agent", "calendar-agent"],
        },
        "isolated-agent": {
            "source_agent_id": "isolated-agent",
            "allowed_destinations": [],
        },
    }
    monkeypatch.setattr(DaemonClient, "list_policies", lambda self: fake_policies)

    res = runner.invoke(cli_app, ["policy", "list"])
    assert res.exit_code == 0
    assert "whatsapp-agent" in res.stdout
    assert "- mail-agent" in res.stdout
    assert "- calendar-agent" in res.stdout
    assert "isolated-agent" in res.stdout
    assert "none" in res.stdout


def test_cli_policy_check_allowed(monkeypatch):
    monkeypatch.setattr(
        DaemonClient,
        "check_policy",
        lambda self, src, dst: {"source": src, "destination": dst, "status": "ALLOWED", "allowed": True},
    )

    res = runner.invoke(cli_app, ["policy", "check", "whatsapp-agent", "mail-agent"])
    assert res.exit_code == 0
    assert "ALLOWED" in res.stdout


def test_cli_policy_check_denied(monkeypatch):
    monkeypatch.setattr(
        DaemonClient,
        "check_policy",
        lambda self, src, dst: {"source": src, "destination": dst, "status": "DENIED", "allowed": False},
    )

    res = runner.invoke(cli_app, ["policy", "check", "whatsapp-agent", "research-agent"])
    assert res.exit_code == 1
    assert "DENIED" in res.output
