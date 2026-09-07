from __future__ import annotations

import pytest
from pydantic import ValidationError

from formicx import Node, NodeResources, NodeStatus


def test_node_creation():
    node = Node(
        name="home-pi",
        architecture="arm64",
        resources=NodeResources(cpu_cores=4, memory_mb=8192),
    )

    assert node.node_id.startswith("node_")
    assert node.name == "home-pi"
    assert node.architecture == "arm64"
    assert node.resources.cpu_cores == 4
    assert node.resources.memory_mb == 8192
    assert node.status == NodeStatus.ONLINE


def test_node_invalid_resources():
    with pytest.raises(ValidationError):
        NodeResources(cpu_cores=0, memory_mb=8192)

    with pytest.raises(ValidationError):
        NodeResources(cpu_cores=4, memory_mb=-100)


def test_node_invalid_empty_fields():
    with pytest.raises(ValidationError):
        Node(
            name="",
            architecture="arm64",
            resources=NodeResources(cpu_cores=4, memory_mb=8192),
        )


def test_node_serialization():
    node = Node(
        name="workstation",
        architecture="x86_64",
        resources=NodeResources(cpu_cores=16, memory_mb=32768),
        status=NodeStatus.ONLINE,
    )

    json_str = node.model_dump_json()
    assert "workstation" in json_str

    deserialized = Node.model_validate_json(json_str)
    assert deserialized.node_id == node.node_id
    assert deserialized.resources.cpu_cores == 16
    assert deserialized.status == NodeStatus.ONLINE
