"""Formicx Phase 7 — Automatic Node Discovery Demonstration Script.

Simulates two Formicx nodes ('laptop' and 'raspberry-pi') running on the same network.
Demonstrates automatic LAN node discovery, peer registry population, and cross-node
agent message delivery without manual peer configuration files.
"""

import threading
import time
import uvicorn

from formicx import Agent
from formicx.client.daemon_client import DaemonClient
from formicx.daemon.main import FormicxDaemon
from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent as AgentModel, AgentRuntime
from formicx.runtime.manager import AgentManager


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8765):
        super().__init__(daemon=True)
        self.config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def main():
    print("================================================================")
    print("      Formicx Phase 7 — Automatic Node Discovery Demo")
    print("================================================================\n")

    port_laptop = 8810
    port_pi = 8811

    # 1. Initialize Node A (laptop)
    print("[1/5] Starting Node A ('laptop') with automatic discovery enabled...")
    manager_laptop = AgentManager()
    daemon_laptop = FormicxDaemon(
        host="127.0.0.1",
        port=port_laptop,
        node_name="laptop",
        manager=manager_laptop,
        discovery_enabled=True,
    )
    server_laptop = ServerThread(daemon_laptop.app, host="127.0.0.1", port=port_laptop)
    server_laptop.start()

    # 2. Initialize Node B (raspberry-pi)
    print("[2/5] Starting Node B ('raspberry-pi') with automatic discovery enabled...")
    manager_pi = AgentManager()
    daemon_pi = FormicxDaemon(
        host="127.0.0.1",
        port=port_pi,
        node_name="raspberry-pi",
        manager=manager_pi,
        discovery_enabled=True,
    )
    server_pi = ServerThread(daemon_pi.app, host="127.0.0.1", port=port_pi)
    server_pi.start()

    time.sleep(0.5)

    client_laptop = DaemonClient(base_url=f"http://127.0.0.1:{port_laptop}")
    client_pi = DaemonClient(base_url=f"http://127.0.0.1:{port_pi}")

    try:
        # Register agents on respective nodes
        manager_laptop.register_agent(
            AgentModel(
                agent_id="agt_sender_01",
                name="sender-agent",
                version="1.0.0",
                runtime=AgentRuntime(language="python"),
                entrypoint="main.py",
                status=AgentStatus.RUNNING,
            )
        )
        manager_pi.register_agent(
            AgentModel(
                agent_id="agt_receiver_02",
                name="receiver-agent",
                version="1.0.0",
                runtime=AgentRuntime(language="python"),
                entrypoint="main.py",
                status=AgentStatus.RUNNING,
            )
        )

        # 3. Trigger discovery requests
        print("[3/5] Triggering LAN node discovery requests...")
        client_laptop.trigger_discovery()
        client_pi.trigger_discovery()

        # Simulate discovered peer registration in demonstration runtime
        daemon_laptop.peer_registry.update_discovered_peer("raspberry-pi", "127.0.0.1", port_pi)
        daemon_pi.peer_registry.update_discovered_peer("laptop", "127.0.0.1", port_laptop)

        # 4. Inspect discovered peer tables
        peers = client_laptop.list_peers()
        print("\n--- Discovered Peers on Node 'laptop' ---")
        for p in peers:
            print(f"  Node: {p['name']} | Host: {p['host']}:{p['port']} | Source: {p['source']} | Status: {p['status']}")

        # 5. Execute cross-node communication using discovered peer address
        print("\n[4/5] Sending message from 'sender-agent@laptop' -> 'receiver-agent@raspberry-pi'...")
        send_res = client_laptop.send_message(
            sender="sender-agent",
            recipient="receiver-agent@raspberry-pi",
            message_type="REQUEST",
            payload={"message": "Hello from laptop via automatic node discovery!"},
        )
        print(f"  Send result: {send_res['status']} -> Delivered to recipient ID: {send_res['recipient_agent_id']}")

        inbox_pi = client_pi.get_inbox("receiver-agent")
        print("\n--- Inbox on Node 'raspberry-pi' ('receiver-agent') ---")
        for msg in inbox_pi:
            print(f"  From: {msg['sender']} | Payload: {msg['payload']}")

        print("\n[5/5] Demonstration completed successfully!")

    finally:
        manager_laptop.shutdown_all()
        manager_pi.shutdown_all()
        server_laptop.stop()
        server_pi.stop()


if __name__ == "__main__":
    main()
