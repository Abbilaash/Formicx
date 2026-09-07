#!/usr/bin/env python3
"""
Formicx — Phase 0 Domain Model Demonstration Script.

This script demonstrates creation, validation, and JSON serialization of the 
five fundamental Formicx primitives: Node, Agent, Team, Service, and Message.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure src/ directory is in python path for standalone execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formicx import (
    Agent,
    AgentRuntime,
    AgentStatus,
    Message,
    MessageType,
    Node,
    NodeResources,
    NodeStatus,
    Service,
    Team,
)


def main() -> None:
    print("=" * 60)
    print(" FORMICX — Phase 0 Domain Model Demonstration")
    print("=" * 60)

    # 1. Create a Node
    node = Node(
        name="home-pi",
        architecture="arm64",
        resources=NodeResources(
            cpu_cores=4,
            memory_mb=8192,
        ),
        status=NodeStatus.ONLINE,
    )

    print("\n1. Created Node:")
    print(f"   Name: {node.name}")
    print(f"   ID: {node.node_id}")
    print(f"   Architecture: {node.architecture}")
    print(f"   Resources: {node.resources.cpu_cores} Cores, {node.resources.memory_mb} MB RAM")
    print(f"   Status: {node.status.value}")

    # 2. Create three Agents
    researcher = Agent(
        name="researcher",
        version="0.1.0",
        runtime=AgentRuntime(
            language="python",
            framework="langgraph",
        ),
        entrypoint="agents/researcher/main.py",
        capabilities=["research", "summarization", "literature_search"],
        permissions=["network.internet"],
        node_id=node.node_id,
    )

    developer = Agent(
        name="developer",
        version="0.1.0",
        runtime=AgentRuntime(
            language="python",
            framework="custom",
        ),
        entrypoint="agents/developer/main.py",
        capabilities=["code_generation", "refactoring", "unit_testing"],
        permissions=["filesystem.write", "network.internet"],
        node_id=node.node_id,
    )

    reviewer = Agent(
        name="reviewer",
        version="0.1.0",
        runtime=AgentRuntime(
            language="python",
            framework="crewai",
        ),
        entrypoint="agents/reviewer/main.py",
        capabilities=["code_review", "security_audit"],
        permissions=["filesystem.read"],
        node_id=node.node_id,
    )

    print("\n2. Created Agents:")
    for agt in (researcher, developer, reviewer):
        print(f"   - [{agt.agent_id}] {agt.name} (v{agt.version}) | Framework: {agt.runtime.framework} | Status: {agt.status.value}")

    # 3. Create a Team containing those Agents
    team = Team(
        name="startup-team",
        goal="Build and evaluate a startup prototype",
        members=[researcher.agent_id, developer.agent_id, reviewer.agent_id],
        coordinator=researcher.agent_id,
    )

    print("\n3. Created Team:")
    print(f"   Team Name: {team.name}")
    print(f"   ID: {team.team_id}")
    print(f"   Goal: {team.goal}")
    print(f"   Members Count: {len(team.members)}")
    print(f"   Coordinator: {team.coordinator}")

    # 4. Create a Service
    github_service = Service(
        name="github",
        capabilities=["read_repository", "read_issues", "create_pull_request"],
        permissions=["github.read", "github.write"],
        status="active",
    )

    print("\n4. Created Service:")
    print(f"   Service Name: {github_service.name}")
    print(f"   ID: {github_service.service_id}")
    print(f"   Capabilities: {', '.join(github_service.capabilities)}")

    # 5. Create a Message between two Agents
    task_message = Message(
        sender=researcher.agent_id,
        recipient=developer.agent_id,
        message_type=MessageType.TASK,
        payload={
            "task": "Analyze the repository architecture and implement Phase 0 models",
            "priority": "high",
            "deadline": "2026-09-10T00:00:00Z",
        },
    )

    print("\n5. Created Message:")
    print(f"   ID: {task_message.message_id}")
    print(f"   Sender: {task_message.sender} (researcher)")
    print(f"   Recipient: {task_message.recipient} (developer)")
    print(f"   Type: {task_message.message_type.value}")
    print(f"   Timestamp (UTC): {task_message.timestamp.isoformat()}")

    # 6. Print Serialized JSON Representations
    print("\n" + "=" * 60)
    print(" SERIALIZED DOMAIN OBJECTS (JSON)")
    print("=" * 60)

    demo_objects = {
        "node": node.model_dump(mode="json"),
        "agents": [
            researcher.model_dump(mode="json"),
            developer.model_dump(mode="json"),
            reviewer.model_dump(mode="json"),
        ],
        "team": team.model_dump(mode="json"),
        "service": github_service.model_dump(mode="json"),
        "message": task_message.model_dump(mode="json"),
    }

    print(json.dumps(demo_objects, indent=2))
    print("\nPhase 0 domain model demonstration completed successfully!")


if __name__ == "__main__":
    main()
