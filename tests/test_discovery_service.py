import asyncio
import pytest

from formicx.communication.peer import PeerRegistry
from formicx.discovery.protocol import DiscoveryMessage, DiscoveryMessageType
from formicx.discovery.service import DiscoveryService


@pytest.mark.asyncio
async def test_discovery_service_self_filtering():
    peer_registry = PeerRegistry()
    service = DiscoveryService(
        local_node_name="laptop",
        local_node_host="127.0.0.1",
        local_node_port=8000,
        peer_registry=peer_registry,
        enabled=True,
    )

    # Self announcement message
    self_msg = DiscoveryMessage(
        message_type=DiscoveryMessageType.ANNOUNCE,
        node_name="laptop",
        host="127.0.0.1",
        port=8000,
    )

    # Process packet
    service._on_message_received(self_msg, ("127.0.0.1", 9999))

    # Should be ignored (no peer registered for laptop)
    assert not peer_registry.contains("laptop")


@pytest.mark.asyncio
async def test_discovery_service_peer_registration():
    peer_registry = PeerRegistry()
    service = DiscoveryService(
        local_node_name="laptop",
        local_node_host="127.0.0.1",
        local_node_port=8000,
        peer_registry=peer_registry,
        enabled=True,
    )

    remote_msg = DiscoveryMessage(
        message_type=DiscoveryMessageType.ANNOUNCE,
        node_name="raspberry-pi",
        host="192.168.1.50",
        port=8000,
    )

    service._on_message_received(remote_msg, ("192.168.1.50", 9999))

    assert peer_registry.contains("raspberry-pi")
    peer = peer_registry.get_peer("raspberry-pi")
    assert peer.host == "192.168.1.50"
    assert peer.port == 8000
    assert peer.source == "discovered"
