#!/usr/bin/env python3
"""
Formicx — Phase 1 Agent Runtime Demonstration Script.

This script demonstrates loading agent manifests, starting multiple agents concurrently
as independent OS processes, monitoring PIDs and statuses, detecting unexpected failures,
and cleanly terminating agent processes.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure src/ directory is in python path for standalone execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formicx import AgentManager, load_agent_manifest


def main() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    agents_dir = root_dir / "agents"

    print("=" * 65)
    print(" FORMICX — Phase 1 Agent Runtime Demonstration")
    print("=" * 65)

    manager = AgentManager()

    try:
        # 1. Load agent manifests
        hello_manifest = agents_dir / "hello-agent" / "agent.yaml"
        worker_manifest = agents_dir / "worker-agent" / "agent.yaml"
        failing_manifest = agents_dir / "failing-agent" / "agent.yaml"

        print("\n1. Loading Agent Manifests...")
        hello_agt = load_agent_manifest(hello_manifest)
        worker_agt = load_agent_manifest(worker_manifest)
        failing_agt = load_agent_manifest(failing_manifest)

        print(f"   Loaded: {hello_agt.name} [{hello_agt.agent_id}]")
        print(f"   Loaded: {worker_agt.name} [{worker_agt.agent_id}]")
        print(f"   Loaded: {failing_agt.name} [{failing_agt.agent_id}]")

        # 2. Register all agents
        print("\n2. Registering Agents in Runtime Registry...")
        manager.register_agent(hello_agt)
        manager.register_agent(worker_agt)
        manager.register_agent(failing_agt)

        print(f"   Total registered agents: {len(manager.list_agents())}")

        # 3. Start all agents concurrently
        print("\n3. Starting Agents concurrently as independent OS processes...")
        manager.start_agent(hello_agt.agent_id)
        manager.start_agent(worker_agt.agent_id)
        manager.start_agent(failing_agt.agent_id)

        # Inspect initial process state
        print("\n4. Initial Agent Process State:")
        for agt in manager.list_agents():
            handle = manager.process_manager.get_process_handle(agt.agent_id)
            pid = handle.pid if handle else "N/A"
            print(f"   - {agt.name:<15} | Status: {agt.status.value:<10} | PID: {pid}")

        # 4. Wait for failing-agent to complete failure simulation
        print("\n5. Waiting 1.5 seconds to observe process execution...")
        time.sleep(1.5)

        # 5. Refresh statuses
        print("\n6. Refreshing Agent Statuses...")
        manager.refresh_all_statuses()

        print("   Post-refresh Agent Statuses:")
        for agt in manager.list_agents():
            handle = manager.process_manager.get_process_handle(agt.agent_id)
            pid = handle.pid if handle else "N/A"
            exit_code = handle.poll() if handle else None
            print(f"   - {agt.name:<15} | Status: {agt.status.value:<10} | PID: {pid:<6} | Exit Code: {exit_code}")

        # 6. Stop remaining active agents
        print("\n7. Gracefully Stopping Remaining Active Agents...")
        manager.stop_agent(hello_agt.agent_id)
        manager.stop_agent(worker_agt.agent_id)

        print("\n8. Final Agent Status Summary:")
        manager.refresh_all_statuses()
        for agt in manager.list_agents():
            print(f"   - {agt.name:<15} | Status: {agt.status.value}")

        print("\n" + "=" * 65)
        print(" Phase 1 Agent Runtime demonstration completed successfully!")
        print("=" * 65)

    finally:
        # Guarantee process cleanup
        manager.shutdown_all()


if __name__ == "__main__":
    main()
