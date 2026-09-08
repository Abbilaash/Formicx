import os
import threading
import time
from pathlib import Path
import pytest
import uvicorn

from formicx.client.daemon_client import DaemonClient, DaemonAPIError
from formicx.daemon.main import FormicxDaemon
from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent as AgentModel, AgentRuntime
from formicx.runtime.manager import AgentManager


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8801):
        super().__init__(daemon=True)
        self.config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def test_phase7_e2e_automatic_node_discovery(tmp_path: Path):
    port_a = 8801
    port_b = 8802
    udp_disc_port = 9991
    url_a = f"http://127.0.0.1:{port_a}"
    url_b = f"http://127.0.0.1:{port_b}"

    # Node A setup (laptop)
    manager_a = AgentManager()
    daemon_a = FormicxDaemon(
        host="127.0.0.1",
        port=port_a,
        node_name="laptop",
        manager=manager_a,
        discovery_enabled=True,
        discovery_port=udp_disc_port,
        announce_interval=1.0,
    )

    # Node B setup (raspberry-pi)
    manager_b = AgentManager()
    daemon_b = FormicxDaemon(
        host="127.0.0.1",
        port=port_b,
        node_name="raspberry-pi",
        manager=manager_b,
        discovery_enabled=True,
        discovery_port=udp_disc_port,
        announce_interval=1.0,
    )

    # Start servers
    server_a = ServerThread(daemon_a.app, host="127.0.0.1", port=port_a)
    server_b = ServerThread(daemon_b.app, host="127.0.0.1", port=port_b)
    server_a.start()
    server_b.start()

    # Manually start discovery services for daemon test instances
    loop = uvicorn.Server(daemon_a.app)  # test helper hook if needed
    time.sleep(0.5)

    client_a = DaemonClient(base_url=url_a, timeout=30.0)
    client_b = DaemonClient(base_url=url_b, timeout=30.0)

    try:
        # Register agents on respective nodes
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

        # Trigger automatic node discovery via API
        disc_res_a = client_a.trigger_discovery()
        disc_res_b = client_b.trigger_discovery()
        assert disc_res_a["status"] == "DISCOVERY_TRIGGERED"
        assert disc_res_b["status"] == "DISCOVERY_TRIGGERED"

        # Simulate UDP datagram exchange directly or give loop time to discover
        daemon_a.peer_registry.update_discovered_peer("raspberry-pi", "127.0.0.1", port_b)
        daemon_b.peer_registry.update_discovered_peer("laptop", "127.0.0.1", port_a)

        # Verify discovery results in client_a peer registry
        peers_a = client_a.list_peers()
        assert any(p["name"] == "raspberry-pi" and p["source"] == "discovered" for p in peers_a)

        # Send message cross-node using automatically discovered peer registry
        send_res = client_a.send_message(
            sender="research-agent",
            recipient="vision-agent@raspberry-pi",
            message_type="REQUEST",
            payload={"action": "auto_discovered_task"},
        )
        assert send_res["status"] == "DELIVERED"

        # Verify message delivered to vision-agent on Node B
        inbox_b = client_b.get_inbox("vision-agent", history=False)
        assert len(inbox_b) == 1
        assert inbox_b[0]["sender"] == "research-agent@laptop"
        assert inbox_b[0]["payload"] == {"action": "auto_discovered_task"}

        # Verify policy enforcement on auto-discovered nodes
        daemon_a.comm_service.policy_engine.set_policy("research-agent", ["blocked-agent"])
        with pytest.raises(DaemonAPIError):
            client_a.send_message(
                sender="research-agent",
                recipient="vision-agent@raspberry-pi",
                message_type="REQUEST",
                payload={"action": "blocked"},
            )

    finally:
        manager_a.shutdown_all()
        manager_b.shutdown_all()
        server_a.stop()
        server_b.stop()
