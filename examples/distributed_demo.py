"""Formicx Phase 6 Distributed Networking Demonstration Script.

Simulates two Formicx Nodes ('laptop' on port 8797 and 'raspberry-pi' on port 8798)
and demonstrates cross-node agent communication.
"""

import threading
import time
import uvicorn

from formicx.client.daemon_client import DaemonClient
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


def main():
    port_laptop = 8797
    port_pi = 8798

    print("============================================================")
    print("      FORMICX PHASE 6 — DISTRIBUTED NETWORKING DEMO        ")
    print("============================================================\n")

    # 1. Initialize Node 1 (laptop)
    manager_laptop = AgentManager()
    daemon_laptop = FormicxDaemon(host="127.0.0.1", port=port_laptop, node_name="laptop", manager=manager_laptop)

    # 2. Initialize Node 2 (raspberry-pi)
    manager_pi = AgentManager()
    daemon_pi = FormicxDaemon(host="127.0.0.1", port=port_pi, node_name="raspberry-pi", manager=manager_pi)

    # 3. Configure Peer Registry
    peer_pi = PeerNode(name="raspberry-pi", host="127.0.0.1", port=port_pi)
    peer_laptop = PeerNode(name="laptop", host="127.0.0.1", port=port_laptop)
    daemon_laptop.peer_registry.register_peer(peer_pi)
    daemon_pi.peer_registry.register_peer(peer_laptop)

    # 4. Start Daemon Servers
    thread_laptop = ServerThread(daemon_laptop.app, host="127.0.0.1", port=port_laptop)
    thread_pi = ServerThread(daemon_pi.app, host="127.0.0.1", port=port_pi)
    thread_laptop.start()
    thread_pi.start()
    time.sleep(0.5)

    client_laptop = DaemonClient(base_url=f"http://127.0.0.1:{port_laptop}")
    client_pi = DaemonClient(base_url=f"http://127.0.0.1:{port_pi}")

    try:
        # 5. Register Agents on respective Nodes
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
        manager_laptop.register_agent(agt_research)
        manager_pi.register_agent(agt_vision)

        print("[Demo] Node 'laptop' info:", client_laptop.get_node_info())
        print("[Demo] Node 'raspberry-pi' info:", client_pi.get_node_info())

        # 6. Ping Peer Node
        ping_res = client_laptop.ping_peer("raspberry-pi")
        print(f"\n[Demo] Ping laptop -> raspberry-pi: {ping_res['status']} ({ping_res['latency_ms']} ms)")

        # 7. Send Cross-Node Message: research-agent@laptop -> vision-agent@raspberry-pi
        print("\n[Demo] Sending message from research-agent@laptop to vision-agent@raspberry-pi...")
        send_res = client_laptop.send_message(
            sender="research-agent",
            recipient="vision-agent@raspberry-pi",
            message_type="REQUEST",
            payload={"task": "analyze_camera_feed", "camera_id": "cam-001"},
        )
        print("[Demo] Delivery Confirmation:", send_res)

        # 8. Inspect Inbox on Remote Node B (raspberry-pi)
        inbox_vision = client_pi.get_inbox("vision-agent", history=False)
        print("\n[Demo] Inbox for vision-agent on node 'raspberry-pi':")
        for msg in inbox_vision:
            print(f"  - Message ID: {msg['message_id']}")
            print(f"    From:       {msg['sender']}")
            print(f"    To:         {msg['recipient']}")
            print(f"    Payload:    {msg['payload']}")

        print("\n============================================================")
        print("      DISTRIBUTED MESSAGING DEMO COMPLETED SUCCESSFULLY!    ")
        print("============================================================")

    finally:
        manager_laptop.shutdown_all()
        manager_pi.shutdown_all()
        thread_laptop.stop()
        thread_pi.stop()


if __name__ == "__main__":
    main()
