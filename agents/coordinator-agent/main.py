import sys
import time
from formicx.sdk import AgentContext


def main():
    context = AgentContext()
    print(
        f"[coordinator-agent] Started with identity: ID={context.agent_id}, Name={context.agent_name}"
    )
    sys.stdout.flush()

    print("[coordinator-agent] Discovering available agents...")
    agents = context.discover()
    print(f"[coordinator-agent] Discovered {len(agents)} agents.")
    sys.stdout.flush()

    target = "research-agent"
    question = "What is the capital of France?"

    print(f"[coordinator-agent] Sending REQUEST to '{target}'...")
    send_res = context.send(
        to=target,
        payload={"question": question},
        message_type="REQUEST",
    )
    orig_msg_id = send_res.get("message_id")
    print(f"[coordinator-agent] Request sent. Message ID: {orig_msg_id}")
    print("[coordinator-agent] Waiting for response...")
    sys.stdout.flush()

    resp = context.receive(timeout=10.0)
    if resp:
        print(f"[coordinator-agent] Response received from sender '{resp.sender}'!")
        print(f"[coordinator-agent] Response Correlation ID: {resp.correlation_id}")
        if resp.correlation_id == orig_msg_id:
            print("[coordinator-agent] Correlation ID verified!")
        else:
            print("[coordinator-agent] ERROR: Correlation ID mismatch!")

        answer = resp.payload.get("answer")
        print(f"[coordinator-agent] Result: {answer}")
    else:
        print("[coordinator-agent] ERROR: Timeout waiting for response.")

    sys.stdout.flush()


if __name__ == "__main__":
    main()
