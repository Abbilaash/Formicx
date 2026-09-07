from __future__ import annotations

from pathlib import Path
import time
import pytest

from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent, AgentRuntime
from formicx.runtime.manager import AgentManager


@pytest.fixture
def dummy_agent(tmp_path: Path) -> Agent:
    script = tmp_path / "main.py"
    script.write_text("import time; time.sleep(10)\n")

    return Agent(
        agent_id="agt_mgr_1",
        name="test-mgr-agent",
        version="0.1.0",
        runtime=AgentRuntime(language="python"),
        entrypoint=str(script.resolve()),
    )


@pytest.fixture
def failing_agent(tmp_path: Path) -> Agent:
    script = tmp_path / "fail.py"
    script.write_text("import sys; sys.exit(1)\n")

    return Agent(
        agent_id="agt_fail",
        name="failing-mgr-agent",
        version="0.1.0",
        runtime=AgentRuntime(language="python"),
        entrypoint=str(script.resolve()),
    )


def test_agent_manager_start_and_stop(dummy_agent: Agent):
    manager = AgentManager()
    manager.register_agent(dummy_agent)

    assert dummy_agent.status == AgentStatus.CREATED

    started_agent = manager.start_agent(dummy_agent.agent_id)
    assert started_agent.status == AgentStatus.RUNNING
    assert manager.process_manager.is_running(dummy_agent.agent_id)

    stopped_agent = manager.stop_agent(dummy_agent.agent_id)
    assert stopped_agent.status == AgentStatus.STOPPED
    assert not manager.process_manager.is_running(dummy_agent.agent_id)


def test_agent_manager_duplicate_start_raises(dummy_agent: Agent):
    manager = AgentManager()
    manager.register_agent(dummy_agent)
    manager.start_agent(dummy_agent.agent_id)

    try:
        with pytest.raises(RuntimeError):
            manager.start_agent(dummy_agent.agent_id)
    finally:
        manager.shutdown_all()


def test_agent_manager_restart(dummy_agent: Agent):
    manager = AgentManager()
    manager.register_agent(dummy_agent)
    manager.start_agent(dummy_agent.agent_id)

    handle1 = manager.process_manager.get_process_handle(dummy_agent.agent_id)
    pid1 = handle1.pid

    restarted = manager.restart_agent(dummy_agent.agent_id)
    assert restarted.status == AgentStatus.RUNNING

    handle2 = manager.process_manager.get_process_handle(dummy_agent.agent_id)
    pid2 = handle2.pid

    try:
        assert pid1 != pid2
    finally:
        manager.shutdown_all()


def test_agent_manager_detect_unexpected_failure(failing_agent: Agent):
    manager = AgentManager()
    manager.register_agent(failing_agent)
    manager.start_agent(failing_agent.agent_id)

    # Wait for process exit
    time.sleep(0.5)

    status = manager.refresh_agent_status(failing_agent.agent_id)
    assert status == AgentStatus.FAILED
    assert failing_agent.status == AgentStatus.FAILED


def test_agent_manager_unregister_running_raises(dummy_agent: Agent):
    manager = AgentManager()
    manager.register_agent(dummy_agent)
    manager.start_agent(dummy_agent.agent_id)

    try:
        with pytest.raises(RuntimeError):
            manager.unregister_agent(dummy_agent.agent_id)
    finally:
        manager.shutdown_all()
