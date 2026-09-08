import json
import pytest

from formicx.discovery.protocol import (
    DiscoveryMessage,
    DiscoveryMessageType,
    PROTOCOL_IDENTIFIER,
    PROTOCOL_VERSION,
    parse_discovery_message,
)


def test_discovery_message_serialization():
    msg = DiscoveryMessage(
        message_type=DiscoveryMessageType.ANNOUNCE,
        node_name="raspberry-pi",
        host="192.168.1.50",
        port=8000,
    )

    json_str = msg.to_json()
    assert PROTOCOL_IDENTIFIER in json_str
    assert "raspberry-pi" in json_str

    parsed = parse_discovery_message(msg.to_bytes())
    assert parsed is not None
    assert parsed.node_name == "raspberry-pi"
    assert parsed.host == "192.168.1.50"
    assert parsed.port == 8000
    assert parsed.message_type == DiscoveryMessageType.ANNOUNCE


def test_parse_invalid_discovery_messages():
    # Malformed JSON
    assert parse_discovery_message(b"not json") is None

    # Invalid protocol
    bad_proto = {
        "protocol": "other-protocol",
        "version": "1",
        "message_type": "ANNOUNCE",
        "node_name": "node-1",
        "host": "127.0.0.1",
        "port": 8000,
    }
    assert parse_discovery_message(json.dumps(bad_proto)) is None

    # Unsupported version
    bad_ver = {
        "protocol": PROTOCOL_IDENTIFIER,
        "version": "999",
        "message_type": "ANNOUNCE",
        "node_name": "node-1",
        "host": "127.0.0.1",
        "port": 8000,
    }
    assert parse_discovery_message(json.dumps(bad_ver)) is None

    # Missing node_name
    missing_name = {
        "protocol": PROTOCOL_IDENTIFIER,
        "version": PROTOCOL_VERSION,
        "message_type": "ANNOUNCE",
        "node_name": "  ",
        "host": "127.0.0.1",
        "port": 8000,
    }
    assert parse_discovery_message(json.dumps(missing_name)) is None

    # Invalid port range
    bad_port = {
        "protocol": PROTOCOL_IDENTIFIER,
        "version": PROTOCOL_VERSION,
        "message_type": "ANNOUNCE",
        "node_name": "node-1",
        "host": "127.0.0.1",
        "port": 70000,
    }
    assert parse_discovery_message(json.dumps(bad_port)) is None
