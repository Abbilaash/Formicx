from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from formicx.enums.agent_status import AgentStatus
from formicx.enums.message_type import MessageType
from formicx.manifests.loader import load_agent_manifest
from formicx.models.agent import Agent
from formicx.models.message import Message
from formicx.runtime.manager import AgentManager
from formicx.communication.exceptions import (
    AgentNotFoundError,
    AmbiguousAgentError,
    InvalidMessageError,
    MessageDeliveryError,
)
from formicx.communication.service import CommunicationService


class RegisterRequest(BaseModel):
    """Payload for registering an agent from a manifest file or directory."""

    path: str


class BroadcastRequest(BaseModel):
    """Payload for broadcasting a message to multiple agents."""

    from_agent_id: str
    message_type: str = "EVENT"
    payload: Dict[str, Any] = Field(default_factory=dict)
    running_only: bool = False


def _serialize_agent(agent: Agent, manager: AgentManager) -> Dict[str, Any]:
    """Serialize an Agent model into a JSON-safe API response dictionary."""
    handle = manager.process_manager.get_process_handle(agent.agent_id)
    is_running = handle.is_running() if handle else False
    pid = handle.pid if (handle and is_running) else None

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "version": agent.version,
        "status": agent.status.value,
        "pid": pid,
        "entrypoint": agent.entrypoint,
        "runtime": agent.runtime.model_dump(),
        "capabilities": agent.capabilities,
        "permissions": agent.permissions,
        "node_id": agent.node_id,
    }


def create_daemon_app(
    manager: AgentManager,
    comm_service: Optional[CommunicationService] = None,
) -> FastAPI:
    """Create the FastAPI local control application bound to an AgentManager instance."""
    app = FastAPI(
        title="Formicx Daemon Control API",
        description="Local control and native communication interface for formicxd daemon.",
        version="0.3.0",
    )

    communication_service = (
        comm_service
        if comm_service is not None
        else CommunicationService(registry=manager.registry)
    )

    def _resolve_agent(identifier: str) -> Agent:
        manager.refresh_all_statuses()
        agents = manager.list_agents()

        # Try exact ID match
        for agt in agents:
            if agt.agent_id == identifier:
                return agt

        # Try name match
        named_matches = [agt for agt in agents if agt.name == identifier]
        if len(named_matches) == 1:
            return named_matches[0]
        elif len(named_matches) > 1:
            matching_ids = ", ".join([a.agent_id for a in named_matches])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ambiguous agent name '{identifier}'. Multiple agents match: {matching_ids}",
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: '{identifier}'",
        )

    # Global Exception Handlers
    @app.exception_handler(AgentNotFoundError)
    async def agent_not_found_handler(request: Request, exc: AgentNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(AmbiguousAgentError)
    async def ambiguous_agent_handler(request: Request, exc: AmbiguousAgentError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InvalidMessageError)
    async def invalid_message_handler(request: Request, exc: InvalidMessageError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(MessageDeliveryError)
    async def message_delivery_handler(request: Request, exc: MessageDeliveryError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc).strip("'")},
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    # API Endpoints
    @app.get("/v1/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok", "daemon": "formicxd"}

    @app.get("/v1/daemon/status")
    async def daemon_status() -> Dict[str, Any]:
        manager.refresh_all_statuses()
        agents = manager.list_agents()
        running_count = sum(1 for a in agents if a.status == AgentStatus.RUNNING)
        return {
            "status": "running",
            "managed_agents": len(agents),
            "running_agents": running_count,
        }

    @app.post("/v1/agents/register", status_code=status.HTTP_201_CREATED)
    async def register_agent(req: RegisterRequest) -> Dict[str, Any]:
        raw_path = Path(req.path).resolve()
        if raw_path.is_dir():
            manifest_file = raw_path / "agent.yaml"
        else:
            manifest_file = raw_path

        if not manifest_file.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent manifest file not found: '{manifest_file}'",
            )

        agent = load_agent_manifest(manifest_file)
        manager.register_agent(agent)
        return _serialize_agent(agent, manager)

    @app.get("/v1/agents")
    async def list_agents(status: Optional[str] = None) -> List[Dict[str, Any]]:
        manager.refresh_all_statuses()
        agents = manager.list_agents()
        if status:
            target_status = status.upper()
            agents = [a for a in agents if a.status.value.upper() == target_status]
        return [_serialize_agent(agt, manager) for agt in agents]

    @app.get("/v1/agents/{identifier}")
    async def get_agent_details(identifier: str) -> Dict[str, Any]:
        agent = _resolve_agent(identifier)
        return _serialize_agent(agent, manager)

    @app.post("/v1/agents/{identifier}/start")
    async def start_agent(identifier: str) -> Dict[str, Any]:
        agent = _resolve_agent(identifier)
        updated_agent = manager.start_agent(agent.agent_id)
        return _serialize_agent(updated_agent, manager)

    @app.post("/v1/agents/{identifier}/stop")
    async def stop_agent(identifier: str) -> Dict[str, Any]:
        agent = _resolve_agent(identifier)
        updated_agent = manager.stop_agent(agent.agent_id)
        return _serialize_agent(updated_agent, manager)

    @app.post("/v1/agents/{identifier}/restart")
    async def restart_agent(identifier: str) -> Dict[str, Any]:
        agent = _resolve_agent(identifier)
        updated_agent = manager.restart_agent(agent.agent_id)
        return _serialize_agent(updated_agent, manager)

    # --- Phase 3 Native Agent Communication Endpoints ---

    @app.post("/v1/messages", status_code=status.HTTP_200_OK)
    async def send_message(message: Message) -> Dict[str, Any]:
        return communication_service.send_message(message)

    @app.get("/v1/agents/{identifier}/messages/next")
    async def receive_next_message(
        identifier: str, timeout: Optional[float] = Query(None)
    ) -> Any:
        msg = communication_service.receive_next(identifier, timeout=timeout)
        if msg is None:
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        return msg.model_dump(mode="json")

    @app.get("/v1/agents/{identifier}/messages")
    async def peek_or_list_inbox(
        identifier: str, history: bool = Query(False)
    ) -> List[Dict[str, Any]]:
        if history:
            messages = communication_service.list_history(identifier)
        else:
            messages = communication_service.peek_inbox(identifier)
        return [m.model_dump(mode="json") for m in messages]

    @app.post("/v1/messages/broadcast", status_code=status.HTTP_200_OK)
    async def broadcast_message(req: BroadcastRequest) -> Dict[str, Any]:
        msg_type = MessageType(req.message_type.lower())
        recipients = communication_service.broadcast(
            sender_identifier=req.from_agent_id,
            message_type=msg_type,
            payload=req.payload,
            running_only=req.running_only,
        )
        return {"recipients": recipients}

    return app
