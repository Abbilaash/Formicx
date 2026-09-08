import os
import threading
import time
from pathlib import Path
import pytest
import uvicorn

from formicx import CommunicationDeniedError
from formicx.client.daemon_client import DaemonClient, DaemonAPIError
from formicx.communication.peer import PeerNode
from formicx.daemon.main import FormicxDaemon
from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent as AgentModel, AgentRuntime
from formicx.runtime.manager import AgentManager


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8797):
        super().__init__(daemon=True)
        self.config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def test_phase6_e2e_distributed_agent_networking(tmp_path: Path):
    port_a = 8797
    port_b = 8798
    url_a = f"http://127.0.0.1:{port_a}"
    url_b = f"http://127.0.0.1:{port_b}"

    # Node A setup (laptop)
    manager_a = AgentManager()
    daemon_a = FormicxDaemon(host="127.0.0.1", port=port_a, node_name="laptop", manager=manager_a)

    # Node B setup (raspberry-pi)
    manager_b = AgentManager()
    daemon_b = FormicxDaemon(host="127.0.0.1", port=port_b, node_name="raspberry-pi", manager=manager_b)

    # Register peers across nodes
    peer_pi = PeerNode(name="raspberry-pi", host="127.0.0.1", port=port_b)
    peer_laptop = PeerNode(name="laptop", host="127.0.0.1", port=port_a)
    daemon_a.peer_registry.register_peer(peer_pi)
    daemon_b.peer_registry.register_peer(peer_laptop)

    server_a = ServerThread(daemon_a.app, host="127.0.0.1", port=port_a)
    server_b = ServerThread(daemon_b.app, host="127.0.0.1", port=port_b)
    server_a.start()
    server_b.start()
    time.sleep(0.5)

    client_a = DaemonClient(base_url=url_a, timeout=30.0)
    client_b = DaemonClient(base_url=url_b, timeout=30.0)

    try:
        # 1. Register agents on respective nodes
        agt_research = AgentModel(
            agent_id="agt_res_01",
            name="research-agent",
            version="1.0.0",
            runtime=AgentRuntime(language="python"),
            entrypoint="main.py",
            status=AgentStatus.RUNNING,
        )
        agt_vision = AgentModel(
            agent_id="agt_vis_02",
            name="vision-agent",
            version="1.0.0",
            runtime=AgentRuntime(language="python"),
            entrypoint="main.py",
            status=AgentStatus.RUNNING,
        )
        manager_a.register_agent(agt_research)
        manager_b.register_agent(agt_vision)

        # 2. Test node info and ping endpoints
        info_a = client_a.get_node_info()
        assert info_a["name"] == "laptop"

        ping_res = client_a.ping_peer("raspberry-pi")
        assert ping_res["status"] == "ONLINE"
        assert ping_res["peer"] == "raspberry-pi"
        assert ping_res["latency_ms"] >= 0

        # 3. Test cross-node message routing: research-agent@laptop -> vision-agent@raspberry-pi
        send_res = client_a.send_message(
            sender="research-agent",
            recipient="vision-agent@raspberry-pi",
            message_type="REQUEST",
            payload={"task": "analyze_camera_feed"},
        )
        assert send_res["status"] == "DELIVERED"
        assert send_res["recipient_agent_id"] == "vision-agent@raspberry-pi"

        # Verify message arrived on Node B in vision-agent's inbox
        inbox_b = client_b.get_inbox("vision-agent", history=False)
        assert len(inbox_b) == 1
        msg = inbox_b[0]
        assert msg["sender"] == "research-agent@laptop"
        assert msg["recipient"] == "agt_vis_02"
        assert msg["payload"] == {"task": "analyze_camera_feed"}

        # 4. Test communication policy enforcement across nodes
        daemon_a.comm_service.policy_engine.set_policy("research-agent", ["local-agent"])
        with pytest.raises(DaemonAPIError) as exc_info:
            client_a.send_message(
                sender="research-agent",
                recipient="vision-agent@raspberry-pi",
                message_type="REQUEST",
                payload={"task": "blocked_task"},
            )

        assert "is not permitted to communicate with remote target" in str(exc_info.value)

    finally:
        manager_a.shutdown_all()
        manager_b.shutdown_all()
        server_a.stop()
        server_b.stop()
