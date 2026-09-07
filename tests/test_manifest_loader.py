from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from formicx.manifests import load_agent_manifest


def test_load_valid_manifest(tmp_path: Path):
    entrypoint = tmp_path / "main.py"
    entrypoint.write_text("print('hello')\n")

    manifest = tmp_path / "agent.yaml"
    manifest.write_text("""
name: test-agent
version: 0.1.0
runtime:
  language: python
  framework: custom
entrypoint: main.py
capabilities:
  - test
permissions:
  - net
""")

    agent = load_agent_manifest(manifest)
    assert agent.name == "test-agent"
    assert agent.version == "0.1.0"
    assert agent.runtime.language == "python"
    assert agent.runtime.framework == "custom"
    assert agent.entrypoint == str(entrypoint.resolve())
    assert agent.capabilities == ["test"]
    assert agent.permissions == ["net"]
    assert agent.agent_id.startswith("agt_")


def test_load_manifest_non_existent_file():
    with pytest.raises(FileNotFoundError):
        load_agent_manifest("non_existent_dir/agent.yaml")


def test_load_manifest_invalid_yaml(tmp_path: Path):
    manifest = tmp_path / "agent.yaml"
    manifest.write_text("name: [unclosed list")

    with pytest.raises(ValueError):
        load_agent_manifest(manifest)


def test_load_manifest_missing_required_field(tmp_path: Path):
    entrypoint = tmp_path / "main.py"
    entrypoint.write_text("pass\n")

    manifest = tmp_path / "agent.yaml"
    manifest.write_text("""
name: test-agent
entrypoint: main.py
""")

    with pytest.raises(ValueError):
        load_agent_manifest(manifest)


def test_load_manifest_missing_entrypoint_script(tmp_path: Path):
    manifest = tmp_path / "agent.yaml"
    manifest.write_text("""
name: test-agent
version: 0.1.0
runtime:
  language: python
entrypoint: missing.py
""")

    with pytest.raises(FileNotFoundError):
        load_agent_manifest(manifest)
