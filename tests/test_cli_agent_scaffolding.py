from pathlib import Path
import pytest
from typer.testing import CliRunner

from formicx.cli.main import app as cli_app

runner = CliRunner()


def test_agent_create_help():
    res = runner.invoke(cli_app, ["agent", "create", "--help"])
    assert res.exit_code == 0
    assert "Create a new Formicx agent project" in res.stdout


def test_agent_create_success(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    res = runner.invoke(cli_app, ["agent", "create", "test-agent"])
    assert res.exit_code == 0
    assert "Created Formicx agent project:" in res.stdout

    agent_dir = tmp_path / "test-agent"
    assert agent_dir.is_dir()
    assert (agent_dir / "agent.yaml").is_file()
    assert (agent_dir / "agent.py").is_file()
    assert (agent_dir / "README.md").is_file()
    assert (agent_dir / "tests" / "test_agent.py").is_file()

    # Check rendered contents
    yaml_content = (agent_dir / "agent.yaml").read_text(encoding="utf-8")
    assert "name: test-agent" in yaml_content

    py_content = (agent_dir / "agent.py").read_text(encoding="utf-8")
    assert "class TestAgent(Agent):" in py_content


def test_agent_create_invalid_name():
    res = runner.invoke(cli_app, ["agent", "create", "invalid name!"])
    assert res.exit_code == 1
    assert "Error:" in res.output


def test_agent_create_path_traversal_rejection():
    res = runner.invoke(cli_app, ["agent", "create", "../evil-agent"])
    assert res.exit_code == 1
    assert "Error:" in res.output


def test_agent_create_existing_dir_rejection(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "existing-agent").mkdir()

    res = runner.invoke(cli_app, ["agent", "create", "existing-agent"])
    assert res.exit_code == 1
    assert "already exists" in res.output
