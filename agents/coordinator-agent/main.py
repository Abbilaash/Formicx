import sys
import time
from formicx import Agent


class CoordinatorAgent(Agent):
    """Demo Coordinator Agent utilizing Phase 4 Agent Base Class."""

    def on_start(self):
        print(f"[{self.name}] Started with identity ID={self.id}")
        sys.stdout.flush()

        print(f"[{self.name}] Discovering available agents...")
        agents = self.discover()
        print(f"[{self.name}] Discovered {len(agents)} agents.")
        sys.stdout.flush()

        target = "research-agent"
        question = "What is the capital of France?"

        print(f"[{self.name}] Sending REQUEST to '{target}'...")
        send_res = self.send(
            to=target,
            payload={"question": question},
            message_type="REQUEST",
        )
        orig_msg_id = send_res.get("message_id")
        print(f"[{self.name}] Request sent. Message ID: {orig_msg_id}")
        print(f"[{self.name}] Waiting for response...")
        sys.stdout.flush()

    def on_message(self, message):
        print(f"[{self.name}] Response received from sender '{message.sender}'!")
        print(f"[{self.name}] Response Correlation ID: {message.correlation_id}")
        sys.stdout.flush()
        answer = message.payload.get("answer") or message.payload.get("echo")
        print(f"[{self.name}] Result: {answer}")
        sys.stdout.flush()
        self.stop()

    def on_stop(self):
        print(f"[{self.name}] Coordinator agent task execution finished.")
        sys.stdout.flush()


if __name__ == "__main__":
    CoordinatorAgent().run()
