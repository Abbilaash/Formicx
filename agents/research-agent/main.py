import sys
import time
from formicx.sdk import AgentContext


def main():
    context = AgentContext()
    print(
        f"[research-agent] Started with identity: ID={context.agent_id}, Name={context.agent_name}"
    )
    sys.stdout.flush()

    knowledge = {
        "What is the capital of France?": "Paris",
        "What is 2 + 2?": "4",
        "What OS layer is Formicx built on?": "Linux",
    }

    while True:
        try:
            msg = context.receive(timeout=0.2)
            if msg is not None:
                print(
                    f"[research-agent] Received request {msg.message_id} from {msg.sender}"
                )
                question = msg.payload.get("question") or msg.payload.get("task", "")
                answer = knowledge.get(
                    question, f"Analysis completed for question: '{question}'"
                )

                context.reply(msg, payload={"answer": answer, "question": question})
                print(f"[research-agent] Replied with answer: {answer}")
                sys.stdout.flush()
        except Exception as exc:
            print(f"[research-agent] Exception in loop: {exc}")
            sys.stdout.flush()
        time.sleep(0.1)


if __name__ == "__main__":
    main()
