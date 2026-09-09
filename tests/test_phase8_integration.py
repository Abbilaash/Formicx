import os
import sys
import threading
import time
from pathlib import Path
import pytest
import uvicorn

from formicx.client.daemon_client import DaemonClient
from formicx.daemon.main import FormicxDaemon
from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent as AgentModel, AgentRuntime
from formicx.runtime.manager import AgentManager


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8820):
        super().__init__(daemon=True)
        self.config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def test_phase8_e2e_agent_resource_monitoring(tmp_path: Path):
    port = 8820
    url = f"http://127.0.0.1:{port}"

    # Create dummy agent entrypoints
    entry_a = tmp_path / "main_a.py"
    entry_a.write_text("import time\nwhile True:\n    time.sleep(0.1)\n", encoding="utf-8")

    entry_b = tmp_path / "main_b.py"
    entry_b.write_text("import time\nwhile True:\n    time.sleep(0.1)\n", encoding="utf-8")

    manager = AgentManager()
    daemon = FormicxDaemon(
        host="127.0.0.1",
        port=port,
        node_name="test-node",
        manager=manager,
        resource_interval=0.5,
    )

    server = ServerThread(daemon.app, host="127.0.0.1", port=port)
    server.start()
    time.sleep(0.5)

    client = DaemonClient(base_url=url, timeout=30.0)

    try:
        # 1. Register and start 2 agent processes
        agt_a = AgentModel(
            agent_id="agt_proc_a",
            name="worker-a",
            version="1.0.0",
            runtime=AgentRuntime(language="python"),
            entrypoint=str(entry_a),
            status=AgentStatus.STOPPED,
        )
        agt_b = AgentModel(
            agent_id="agt_proc_b",
            name="worker-b",
            version="1.0.0",
            runtime=AgentRuntime(language="python"),
            entrypoint=str(entry_b),
            status=AgentStatus.STOPPED,
        )
        manager.register_agent(agt_a)
        manager.register_agent(agt_b)

        manager.start_agent("agt_proc_a")
        manager.start_agent("agt_proc_b")
        time.sleep(1.0)

        # 2. Query resource metrics via DaemonClient
        all_resources = client.get_all_resources()
        assert len(all_resources) == 2

        res_a = client.get_agent_resources("worker-a")
        assert res_a["agent_id"] == "agt_proc_a"
        assert res_a["status"] == "RUNNING"
        assert res_a["pid"] is not None
        assert res_a["pid"] > 0
        assert res_a["memory_bytes"] > 0
        assert res_a["thread_count"] >= 1
        assert res_a["cpu_percent"] >= 0.0

        res_b = client.get_agent_resources("worker-b")
        assert res_b["agent_id"] == "agt_proc_b"
        assert res_b["status"] == "RUNNING"
        assert res_b["pid"] is not None
        assert res_b["pid"] > 0

        # 3. Stop worker-a and verify resource metric update
        manager.stop_agent("agt_proc_a")
        time.sleep(0.5)

        res_a_stopped = client.get_agent_resources("worker-a")
        assert res_a_stopped["status"] == "STOPPED"
        assert res_a_stopped["cpu_percent"] == 0.0
        assert res_a_stopped["memory_bytes"] == 0

    finally:
        manager.shutdown_all()
        server.stop()
