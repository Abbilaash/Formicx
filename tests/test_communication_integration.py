import os
import threading
import time
from pathlib import Path
import pytest
import uvicorn

from formicx.client.daemon_client import DaemonClient
from formicx.daemon.main import FormicxDaemon
from formicx.runtime.manager import AgentManager


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8794):
        super().__init__(daemon=True)
        self.config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def test_end_to_end_agent_communication(repo_root: Path, monkeypatch):
    test_port = 8794
    daemon_url = f"http://127.0.0.1:{test_port}"
    monkeypatch.setenv("FORMICX_DAEMON_URL", daemon_url)

    manager = AgentManager()
    daemon = FormicxDaemon(host="127.0.0.1", port=test_port, manager=manager)

    server_thread = ServerThread(daemon.app, host="127.0.0.1", port=test_port)
    server_thread.start()
    time.sleep(0.5)

    client = DaemonClient(base_url=daemon_url, timeout=30.0)

    try:
        res_research = client.register_agent(repo_root / "agents" / "research-agent")
        res_coord = client.register_agent(repo_root / "agents" / "coordinator-agent")

        research_id = res_research["agent_id"]
        coord_id = res_coord["agent_id"]

        client.start_agent("research-agent")
        time.sleep(1.0)

        client.start_agent("coordinator-agent")
        time.sleep(1.0)

        # Poll until both agents complete message exchange or 10s timeout
        start_t = time.time()
        history_research = []
        history_coord = []
        while time.time() - start_t < 10.0:
            history_research = client.get_inbox("research-agent", history=True)
            history_coord = client.get_inbox("coordinator-agent", history=True)
            if len(history_research) >= 1 and len(history_coord) >= 1:
                break
            time.sleep(0.5)

        assert len(history_research) >= 1
        req_msg = history_research[0]
        assert req_msg["sender"] == coord_id
        assert req_msg["message_type"].upper() == "REQUEST"

        assert len(history_coord) >= 1
        resp_msg = history_coord[0]
        assert resp_msg["sender"] == research_id
        assert resp_msg["message_type"].upper() == "RESPONSE"
        assert resp_msg["correlation_id"] == req_msg["message_id"]
        assert resp_msg["payload"]["answer"] == "Paris"

    finally:
        manager.shutdown_all()
        server_thread.stop()
