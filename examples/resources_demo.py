"""Formicx Phase 8 — Agent-Aware Resource Monitoring Demonstration Script.

Launches a local Formicx daemon, registers and starts 3 concurrent agents,
and demonstrates real-time OS process CPU, Memory, and Thread telemetry via
the Formicx DaemonClient API and CLI resource tables.
"""

from pathlib import Path
import tempfile
import threading
import time
import uvicorn

from formicx.client.daemon_client import DaemonClient
from formicx.daemon.main import FormicxDaemon
from formicx.enums.agent_status import AgentStatus
from formicx.models.agent import Agent as AgentModel, AgentRuntime
from formicx.runtime.manager import AgentManager


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8825):
        super().__init__(daemon=True)
        self.config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def main():
    print("================================================================")
    print("     Formicx Phase 8 — Agent-Aware Resource Monitoring Demo")
    print("================================================================\n")

    port = 8825
    base_url = f"http://127.0.0.1:{port}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create dummy entrypoints
        entry_res = tmp_path / "research.py"
        entry_res.write_text("import time\nwhile True:\n    time.sleep(0.1)\n", encoding="utf-8")

        entry_vis = tmp_path / "vision.py"
        entry_vis.write_text("import time\nwhile True:\n    time.sleep(0.1)\n", encoding="utf-8")

        entry_mail = tmp_path / "mail.py"
        entry_mail.write_text("import time\nwhile True:\n    time.sleep(0.1)\n", encoding="utf-8")

        # 1. Initialize Formicx Daemon with ResourceService enabled
        print("[1/4] Starting Formicx daemon with ResourceService enabled...")
        manager = AgentManager()
        daemon = FormicxDaemon(
            host="127.0.0.1",
            port=port,
            node_name="local-node",
            manager=manager,
            resources_enabled=True,
            resource_interval=1.0,
        )
        server = ServerThread(daemon.app, host="127.0.0.1", port=port)
        server.start()
        time.sleep(0.5)

        client = DaemonClient(base_url=base_url)

        try:
            # 2. Register and start 3 agents
            print("[2/4] Registering and starting 3 agents ('research-agent', 'vision-agent', 'mail-agent')...")
            manager.register_agent(
                AgentModel(
                    agent_id="agt_res_01",
                    name="research-agent",
                    version="1.0.0",
                    runtime=AgentRuntime(language="python"),
                    entrypoint=str(entry_res),
                    status=AgentStatus.STOPPED,
                )
            )
            manager.register_agent(
                AgentModel(
                    agent_id="agt_vis_02",
                    name="vision-agent",
                    version="1.0.0",
                    runtime=AgentRuntime(language="python"),
                    entrypoint=str(entry_vis),
                    status=AgentStatus.STOPPED,
                )
            )
            manager.register_agent(
                AgentModel(
                    agent_id="agt_mail_03",
                    name="mail-agent",
                    version="1.0.0",
                    runtime=AgentRuntime(language="python"),
                    entrypoint=str(entry_mail),
                    status=AgentStatus.STOPPED,
                )
            )

            manager.start_agent("agt_res_01")
            manager.start_agent("agt_vis_02")
            manager.start_agent("agt_mail_03")

            # Allow sampling loop to gather process telemetry
            print("[3/4] Collecting OS process telemetry...")
            time.sleep(1.2)

            # 3. Query all agent resource usages
            resources = client.get_all_resources()
            print("\n---------------- FORMICX AGENT RESOURCES ----------------")
            header = f"{'AGENT':<18} {'PID':<10} {'CPU':<10} {'MEMORY':<14} {'STATUS'}"
            print(header)
            print("-" * 65)

            for res in resources:
                name = res.get("agent_name", "")
                pid_str = str(res.get("pid")) if res.get("pid") is not None else "-"
                cpu_str = f"{res.get('cpu_percent', 0.0):.1f}%"
                mem_bytes = res.get("memory_bytes", 0)
                mem_mb = f"{mem_bytes / (1024 * 1024):.1f} MB"
                status_str = str(res.get("status", "")).upper()
                print(f"{name:<18} {pid_str:<10} {cpu_str:<10} {mem_mb:<14} {status_str}")

            # 4. Detailed single-agent inspection
            single_res = client.get_agent_resources("research-agent")
            print("\n---------------- DETAILED AGENT INSPECTION ----------------")
            print(f"Agent: {single_res['agent_name']}")
            print(f"PID: {single_res['pid']}")
            print(f"Status: {single_res['status']}")
            print(f"CPU %: {single_res['cpu_percent']}%")
            print(f"Memory: {single_res['memory_bytes'] / (1024 * 1024):.1f} MB")
            print(f"Threads: {single_res['thread_count']}")

            print("\n[4/4] Demonstration completed successfully!")

        finally:
            manager.shutdown_all()
            server.stop()


if __name__ == "__main__":
    main()
