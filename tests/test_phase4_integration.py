import os
import threading
import time
from pathlib import Path
import pytest
import uvicorn
from typer.testing import CliRunner

from formicx.cli.main import app as cli_app
from formicx.client.daemon_client import DaemonClient
from formicx.daemon.main import FormicxDaemon
from formicx.runtime.manager import AgentManager


runner = CliRunner()


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8795):
        super().__init__(daemon=True)
        self.config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def test_phase4_end_to_end_dx_workflow(tmp_path: Path, monkeypatch):
    test_port = 8795
    daemon_url = f"http://127.0.0.1:{test_port}"
    monkeypatch.setenv("FORMICX_DAEMON_URL", daemon_url)
    monkeypatch.chdir(tmp_path)

    # 1. Test CLI agent creation
    res_create = runner.invoke(cli_app, ["agent", "create", "phase4-test-agent"])
    assert res_create.exit_code == 0
    agent_dir = tmp_path / "phase4-test-agent"
    assert agent_dir.is_dir()

    # 2. Test CLI agent validation
    res_val = runner.invoke(cli_app, ["agent", "validate", str(agent_dir)])
    assert res_val.exit_code == 0
    assert "Agent validation successful" in res_val.stdout

    # 3. Spin up daemon server
    manager = AgentManager()
    daemon = FormicxDaemon(host="127.0.0.1", port=test_port, manager=manager)
    server_thread = ServerThread(daemon.app, host="127.0.0.1", port=test_port)
    server_thread.start()
    time.sleep(0.5)

    client = DaemonClient(base_url=daemon_url, timeout=30.0)

    try:
        # Register generated agent project
        reg_res = client.register_agent(agent_dir)
        agent_id = reg_res["agent_id"]
        assert reg_res["name"] == "phase4-test-agent"

        # Also register echo-agent as sender
        repo_root = Path(__file__).resolve().parent.parent
        reg_sender = client.register_agent(repo_root / "agents" / "echo-agent")
        sender_id = reg_sender["agent_id"]

        # Start target agent process
        client.start_agent("phase4-test-agent")
        time.sleep(0.5)

        # Send request message from registered sender_id to phase4-test-agent
        send_res = client.send_message(
            sender=sender_id,
            recipient="phase4-test-agent",
            message_type="REQUEST",
            payload={"ping": "hello_phase4"},
        )
        msg_id = send_res["message_id"]

        # Wait for agent on_message() to execute and reply back to sender_id
        start_t = time.time()
        reply_history = []
        while time.time() - start_t < 10.0:
            reply_history = client.get_inbox(sender_id, history=True)
            if len(reply_history) >= 1:
                break
            time.sleep(0.3)

        assert len(reply_history) >= 1
        reply_msg = reply_history[0]
        assert reply_msg["sender"] == agent_id
        assert reply_msg["message_type"].upper() == "RESPONSE"
        assert reply_msg["correlation_id"] == msg_id
        assert reply_msg["payload"]["echo"] == {"ping": "hello_phase4"}

        # Stop agent
        client.stop_agent("phase4-test-agent")
        time.sleep(0.3)
        status_res = client.get_agent("phase4-test-agent")
        assert status_res["status"].upper() == "STOPPED"

    finally:
        manager.shutdown_all()
        server_thread.stop()
