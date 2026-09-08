from pathlib import Path
import pytest
from formicx.communication.peer import PeerNode, PeerRegistry
from formicx.communication.exceptions import NodeUnavailableError


def test_peer_node_properties():
    peer = PeerNode(name="raspberry-pi", host="192.168.1.50", port=8000)
    assert peer.name == "raspberry-pi"
    assert peer.host == "192.168.1.50"
    assert peer.port == 8000
    assert peer.url == "http://192.168.1.50:8000"


def test_peer_registry_operations():
    registry = PeerRegistry()
    peer1 = PeerNode(name="raspberry-pi", host="192.168.1.50", port=8000)
    peer2 = PeerNode(name="home-server", host="192.168.1.60", port=9000)

    registry.register_peer(peer1)
    registry.register_peer(peer2)

    assert registry.contains("raspberry-pi")
    assert registry.contains("RASPBERRY-PI")  # Case insensitive
    assert len(registry.list_peers()) == 2

    retrieved = registry.get_peer("raspberry-pi")
    assert retrieved.host == "192.168.1.50"

    with pytest.raises(NodeUnavailableError):
        registry.get_peer("unknown-node")

    registry.unregister_peer("raspberry-pi")
    assert not registry.contains("raspberry-pi")
    assert len(registry.list_peers()) == 1


def test_peer_registry_dict_loading():
    registry = PeerRegistry()
    config = {
        "node": {"name": "laptop", "host": "0.0.0.0", "port": 8765},
        "peers": {
            "raspberry-pi": {"host": "192.168.1.50", "port": 8000},
            "home-server": "192.168.1.60:9000",
        },
    }
    registry.load_from_dict(config)

    assert registry.contains("raspberry-pi")
    assert registry.contains("home-server")
    p1 = registry.get_peer("raspberry-pi")
    assert p1.port == 8000
    p2 = registry.get_peer("home-server")
    assert p2.port == 9000
