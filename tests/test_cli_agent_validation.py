from pathlib import Path
import pytest
from typer.testing import CliRunner

from formicx.cli.main import app as cli_app

runner = CliRunner()


def test_agent_validate_help():
    res = runner.invoke(cli_app, ["agent", "validate", "--help"])
    assert res.exit_code == 0
    assert "Validate a Formicx agent project" in res.stdout


def test_agent_validate_success(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # First create
    runner.invoke(cli_app, ["agent", "create", "valid-agent"])
    # Then validate
    res = runner.invoke(cli_app, ["agent", "validate", "./valid-agent"])
    assert res.exit_code == 0
    assert "Agent validation successful" in res.stdout
    assert "✓ Manifest valid" in res.stdout
    assert "✓ Python syntax valid" in res.stdout


def test_agent_validate_missing_path():
    res = runner.invoke(cli_app, ["agent", "validate", "./non_existent_dir_12345"])
    assert res.exit_code == 1
    assert "Error:" in res.output


def test_agent_validate_missing_manifest(tmp_path: Path):
    empty_dir = tmp_path / "empty_agent"
    empty_dir.mkdir()

    res = runner.invoke(cli_app, ["agent", "validate", str(empty_dir)])
    assert res.exit_code == 1
    assert "Manifest not found" in res.output


def test_agent_validate_syntax_error(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(cli_app, ["agent", "create", "broken-agent"])
    agent_dir = tmp_path / "broken-agent"

    # Introduce python syntax error in agent.py
    (agent_dir / "agent.py").write_text("class BrokenAgent(Agent:\n  pass", encoding="utf-8")

    res = runner.invoke(cli_app, ["agent", "validate", str(agent_dir)])
    assert res.exit_code == 1
    assert "Python syntax error" in res.output
