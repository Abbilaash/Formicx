import sys
from formicx import Agent


class EchoAgent(Agent):
    """Demo Echo Agent inheriting from Formicx Agent base class."""

    def on_start(self):
        print(f"[{self.name}] Started with identity ID={self.id}")
        sys.stdout.flush()

    def on_message(self, message):
        print(f"[{self.name}] Received message from '{message.sender}': {message.payload}")
        sys.stdout.flush()
        self.reply(
            message,
            {
                "echo": message.payload,
                "status": "echoed",
            },
        )
        print(f"[{self.name}] Replied to message {message.message_id}")
        sys.stdout.flush()

    def on_stop(self):
        print(f"[{self.name}] Stopping cleanly.")
        sys.stdout.flush()


if __name__ == "__main__":
    EchoAgent().run()
