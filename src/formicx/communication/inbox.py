"""Thread-safe Agent Inbox implementation for Formicx."""

import queue
import threading
from typing import List, Optional

from formicx.models.message import Message


class AgentInbox:
    """Manages pending incoming messages and historical messages for a single agent."""

    def __init__(self, agent_id: str, max_history: int = 100) -> None:
        self.agent_id = agent_id
        self.max_history = max_history
        self._queue: queue.Queue[Message] = queue.Queue()
        self._history: List[Message] = []
        self._lock = threading.Lock()

    def enqueue(self, message: Message) -> None:
        """Enqueue a message into the agent's pending inbox and record in history."""
        self._queue.put(message)
        with self._lock:
            self._history.append(message)
            if len(self._history) > self.max_history:
                self._history.pop(0)

    def receive_next(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Consume and return the next pending message.

        Blocks up to timeout seconds if specified. Returns None if inbox is empty.
        """
        try:
            if timeout is None or timeout <= 0:
                return self._queue.get_nowait()
            else:
                return self._queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def peek(self) -> List[Message]:
        """Return a copy of pending messages without consuming them from queue."""
        with self._queue.mutex:
            return list(self._queue.queue)

    def list_history(self) -> List[Message]:
        """Return recent message history for debugging."""
        with self._lock:
            return list(self._history)

    @property
    def pending_count(self) -> int:
        """Return the number of pending unconsumed messages."""
        return self._queue.qsize()
