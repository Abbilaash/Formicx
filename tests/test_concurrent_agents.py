from __future__ import annotations

from pathlib import Path
import time
import pytest

from formicx.enums.agent_status import AgentStatus
from formicx.manifests.loader import load_agent_manifest
from formicx.runtime.manager import AgentManager


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_concurrent_agents_execution_and_failure_isolation(repo_root: Path):
    agents_dir = repo_root / "agents"
    hello_manifest = agents_dir / "hello-agent" / "agent.yaml"
    worker_manifest = agents_dir / "worker-agent" / "agent.yaml"
    failing_manifest = agents_dir / "failing-agent" / "agent.yaml"

    hello_agt = load_agent_manifest(hello_manifest)
    worker_agt = load_agent_manifest(worker_manifest)
    failing_agt = load_agent_manifest(failing_manifest)

    manager = AgentManager()
    manager.register_agent(hello_agt)
    manager.register_agent(worker_agt)
    manager.register_agent(failing_agt)

    try:
        # Start all 3 agents concurrently
        manager.start_agent(hello_agt.agent_id)
        manager.start_agent(worker_agt.agent_id)
        manager.start_agent(failing_agt.agent_id)

        h_hello = manager.process_manager.get_process_handle(hello_agt.agent_id)
        h_worker = manager.process_manager.get_process_handle(worker_agt.agent_id)
        h_failing = manager.process_manager.get_process_handle(failing_agt.agent_id)

        # 1. Confirm all have distinct PIDs
        pids = {h_hello.pid, h_worker.pid, h_failing.pid}
        assert len(pids) == 3

        # 2. Confirm all are RUNNING initially
        assert hello_agt.status == AgentStatus.RUNNING
        assert worker_agt.status == AgentStatus.RUNNING
        assert failing_agt.status == AgentStatus.RUNNING

        # 3. Stop hello-agent and confirm worker-agent and failing-agent remain unaffected
        manager.stop_agent(hello_agt.agent_id)
        assert hello_agt.status == AgentStatus.STOPPED
        assert manager.process_manager.is_running(worker_agt.agent_id)

        # 4. Wait for failing-agent process to exit cleanly (sleep 0.5s > 0.3s)
        time.sleep(0.6)

        # 5. Refresh statuses and verify failure isolation:
        # failing-agent must be FAILED, worker-agent must remain RUNNING
        manager.refresh_all_statuses()

        assert failing_agt.status == AgentStatus.FAILED
        assert worker_agt.status == AgentStatus.RUNNING
        assert manager.process_manager.is_running(worker_agt.agent_id)

    finally:
        # Guarantee all child processes are cleaned up
        manager.shutdown_all()
        for agt in manager.list_agents():
            assert not manager.process_manager.is_running(agt.agent_id)
