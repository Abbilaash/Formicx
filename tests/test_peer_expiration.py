import time
import pytest

from formicx.communication.exceptions import NodeUnavailableError
from formicx.communication.peer import PeerNode, PeerRegistry


def test_peer_registry_discovered_updates():
    registry = PeerRegistry()

    # Register discovered peer
    peer1 = registry.update_discovered_peer("raspberry-pi", "192.168.1.50", 8000)
    assert peer1.source == "discovered"
    assert peer1.active is True
    assert peer1.last_seen is not None
    assert registry.contains("raspberry-pi")

    # Re-discover peer with updated port/host
    peer2 = registry.update_discovered_peer("raspberry-pi", "192.168.1.55", 8001)
    assert peer2.host == "192.168.1.55"
    assert peer2.port == 8001
    assert len(registry.list_peers()) == 1


def test_peer_expiration_logic():
    registry = PeerRegistry()

    # Manual peer (never expires)
    manual_peer = PeerNode(name="manual-server", host="10.0.0.1", port=8000, source="manual")
    registry.register_peer(manual_peer)

    # Discovered peer
    disc_peer = registry.update_discovered_peer("temp-node", "10.0.0.2", 8000)

    # Set last_seen artificially in the past (100s ago)
    disc_peer.last_seen = time.time() - 100.0

    # Run check_expirations with 60s timeout
    expired = registry.check_expirations(timeout_seconds=60.0)

    assert "temp-node" in expired
    assert not registry.contains("temp-node")

    # Manual peer remains active
    assert registry.contains("manual-server")

    # Getting expired peer raises NodeUnavailableError
    with pytest.raises(NodeUnavailableError):
        registry.get_peer("temp-node", active_only=True)

    # But un-filtered listing contains inactive peer for historical inspection
    all_peers = registry.list_peers(active_only=False)
    assert any(p.name == "temp-node" and not p.active for p in all_peers)
