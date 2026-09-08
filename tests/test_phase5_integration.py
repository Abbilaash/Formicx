import os
import threading
import time
from pathlib import Path
import pytest
import uvicorn

from formicx import Agent, AgentContext, CommunicationDeniedError
from formicx.client.daemon_client import DaemonClient, DaemonAPIError
from formicx.daemon.main import FormicxDaemon
from formicx.models.agent import Agent as AgentModel, AgentRuntime
from formicx.enums.agent_status import AgentStatus
from formicx.runtime.manager import AgentManager


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8796):
        super().__init__(daemon=True)
        self.config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def test_phase5_e2e_communication_policy_enforcement(monkeypatch, tmp_path: Path):
    test_port = 8796
    daemon_url = f"http://127.0.0.1:{test_port}"
    monkeypatch.setenv("FORMICX_DAEMON_URL", daemon_url)

    manager = AgentManager()
    daemon = FormicxDaemon(host="127.0.0.1", port=test_port, manager=manager)

    # Configure communication policies in daemon
    daemon.comm_service.policy_engine.set_policy("whatsapp-agent", ["mail-agent"])
    daemon.comm_service.policy_engine.set_policy("isolated-agent", [])

    server_thread = ServerThread(daemon.app, host="127.0.0.1", port=test_port)
    server_thread.start()
    time.sleep(0.5)

    client = DaemonClient(base_url=daemon_url, timeout=30.0)

    try:
        # Register test agents in manager/registry
        agt_wa = AgentModel(
            agent_id="agt_wa_01",
            name="whatsapp-agent",
            version="1.0.0",
            runtime=AgentRuntime(language="python"),
            entrypoint="main.py",
            status=AgentStatus.RUNNING,
        )
        agt_mail = AgentModel(
            agent_id="agt_mail_02",
            name="mail-agent",
            version="1.0.0",
            runtime=AgentRuntime(language="python"),
            entrypoint="main.py",
            status=AgentStatus.RUNNING,
        )
        agt_res = AgentModel(
            agent_id="agt_res_03",
            name="research-agent",
            version="1.0.0",
            runtime=AgentRuntime(language="python"),
            entrypoint="main.py",
            status=AgentStatus.RUNNING,
        )
        agt_iso = AgentModel(
            agent_id="agt_iso_04",
            name="isolated-agent",
            version="1.0.0",
            runtime=AgentRuntime(language="python"),
            entrypoint="main.py",
            status=AgentStatus.RUNNING,
        )
        manager.register_agent(agt_wa)
        manager.register_agent(agt_mail)
        manager.register_agent(agt_res)
        manager.register_agent(agt_iso)

        # 1. Test allowed communication: whatsapp-agent -> mail-agent
        ctx_wa = AgentContext(agent_id="agt_wa_01", agent_name="whatsapp-agent")
        send_res = ctx_wa.send(to="mail-agent", payload={"task": "send_email"}, message_type="REQUEST")
        assert send_res["status"] == "DELIVERED"

        # Verify message arrived in mail-agent inbox
        inbox_mail = client.get_inbox("mail-agent", history=False)
        assert len(inbox_mail) == 1
        assert inbox_mail[0]["sender"] == "agt_wa_01"

        # 2. Test denied communication: whatsapp-agent -> research-agent
        with pytest.raises(CommunicationDeniedError) as exc_info:
            ctx_wa.send(to="research-agent", payload={"task": "analyze"}, message_type="REQUEST")

        assert "is not permitted to communicate with" in str(exc_info.value)

        # 3. Test empty allow list: isolated-agent -> mail-agent
        ctx_iso = AgentContext(agent_id="agt_iso_04", agent_name="isolated-agent")
        with pytest.raises(CommunicationDeniedError):
            ctx_iso.send(to="mail-agent", payload={"task": "ping"}, message_type="REQUEST")

        # 4. Test client policy endpoints
        policies = client.list_policies()
        assert "whatsapp-agent" in policies
        assert policies["whatsapp-agent"]["allowed_destinations"] == ["mail-agent"]

        check_allowed = client.check_policy("whatsapp-agent", "mail-agent")
        assert check_allowed["status"] == "ALLOWED"

        check_denied = client.check_policy("whatsapp-agent", "research-agent")
        assert check_denied["status"] == "DENIED"

    finally:
        manager.shutdown_all()
        server_thread.stop()
