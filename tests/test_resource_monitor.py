import os
import psutil
import pytest
from unittest.mock import MagicMock

from formicx.resources.monitor import AgentResourceMonitor


def test_resource_monitor_sample_self_process():
    monitor = AgentResourceMonitor()
    current_pid = os.getpid()

    usage = monitor.sample_agent(
        agent_id="self-agent",
        agent_name="self-agent",
        pid=current_pid,
        is_running=True,
    )

    assert usage.agent_id == "self-agent"
    assert usage.pid == current_pid
    assert usage.status == "RUNNING"
    assert usage.memory_bytes > 0
    assert usage.thread_count >= 1
    assert usage.cpu_percent >= 0.0


def test_resource_monitor_sample_stopped_process():
    monitor = AgentResourceMonitor()

    usage = monitor.sample_agent(
        agent_id="stopped-agent",
        agent_name="stopped-agent",
        pid=999999,
        is_running=False,
    )

    assert usage.status == "STOPPED"
    assert usage.cpu_percent == 0.0
    assert usage.memory_bytes == 0
    assert usage.thread_count == 0


def test_resource_monitor_handles_non_existent_pid():
    monitor = AgentResourceMonitor()

    # Highly unlikely PID
    fake_pid = 999998
    usage = monitor.sample_agent(
        agent_id="dead-agent",
        agent_name="dead-agent",
        pid=fake_pid,
        is_running=True,
    )

    assert usage.status in ("STOPPED", "UNKNOWN")
    assert usage.cpu_percent == 0.0
    assert usage.memory_bytes == 0
