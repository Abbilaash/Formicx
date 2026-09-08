import pytest
from formicx.communication.address import AgentAddress
from formicx.communication.exceptions import InvalidAgentAddressError


def test_parse_local_address():
    addr = AgentAddress.parse("research-agent")
    assert addr.agent_name == "research-agent"
    assert addr.node_name is None
    assert not addr.is_remote
    assert addr.to_string() == "research-agent"
    assert str(addr) == "research-agent"


def test_parse_qualified_address():
    addr = AgentAddress.parse("vision-agent@raspberry-pi")
    assert addr.agent_name == "vision-agent"
    assert addr.node_name == "raspberry-pi"
    assert addr.is_remote
    assert addr.to_string() == "vision-agent@raspberry-pi"


def test_is_local_to():
    local_addr = AgentAddress.parse("agent-a")
    assert local_addr.is_local_to("laptop")

    remote_same = AgentAddress.parse("agent-a@laptop")
    assert remote_same.is_local_to("laptop")
    assert not remote_same.is_local_to("raspberry-pi")

    remote_diff = AgentAddress.parse("agent-a@raspberry-pi")
    assert not remote_diff.is_local_to("laptop")


def test_invalid_addresses():
    invalid_cases = [
        "",
        "   ",
        "@raspberry-pi",
        "vision-agent@",
        "agent@@node",
        "a@b@c",
    ]
    for case in invalid_cases:
        with pytest.raises(InvalidAgentAddressError):
            AgentAddress.parse(case)
