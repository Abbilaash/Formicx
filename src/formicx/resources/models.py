"""Domain models for agent-aware OS resource usage."""

from __future__ import annotations

import time
from typing import Optional
from pydantic import BaseModel, Field


class AgentResourceUsage(BaseModel):
    """Normalized operating system resource metrics for a Formicx agent."""

    agent_id: str = Field(..., description="Unique agent identifier (e.g. agt_123 or research-agent)")
    agent_name: str = Field(..., description="Display name of the agent")
    pid: Optional[int] = Field(default=None, description="Operating system Process ID (PID)")
    status: str = Field(default="STOPPED", description="Current status of agent process (e.g. RUNNING, STOPPED, FAILED, UNKNOWN)")
    cpu_percent: float = Field(default=0.0, description="CPU usage percentage (e.g. 14.2)")
    memory_bytes: int = Field(default=0, description="Canonical Resident Set Size (RSS) memory usage in bytes")
    memory_percent: float = Field(default=0.0, description="Percentage of total physical RAM used")
    thread_count: int = Field(default=0, description="Number of active OS threads spawned by process")
    last_sampled_at: Optional[float] = Field(default_factory=time.time, description="Unix timestamp of measurement sample")

    @property
    def is_active(self) -> bool:
        """Check if process is actively running."""
        return self.status.upper() == "RUNNING" and self.pid is not None
