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
    CommunicationDeniedError,
    DiscoveryError,
    InvalidAgentAddressError,
    InvalidMessageError,
    MessageDeliveryError,
    NodeUnavailableError,
)
from formicx.communication.service import CommunicationService
from formicx.discovery.service import DiscoveryService
from formicx.resources.service import ResourceService


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
    discovery_service: Optional[DiscoveryService] = None,
    resource_service: Optional[ResourceService] = None,
    node_name: Optional[str] = None,
    node_host: Optional[str] = None,
    node_port: Optional[int] = None,
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

    if discovery_service is not None:
        @app.on_event("startup")
        async def _start_discovery():
            await discovery_service.start()

        @app.on_event("shutdown")
        async def _stop_discovery():
            await discovery_service.stop()

    if resource_service is not None:
        @app.on_event("startup")
        async def _start_resources():
            await resource_service.start()

        @app.on_event("shutdown")
        async def _stop_resources():
            await resource_service.stop()


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

    @app.exception_handler(CommunicationDeniedError)
    async def communication_denied_handler(request: Request, exc: CommunicationDeniedError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)},
        )

    @app.exception_handler(NodeUnavailableError)
    async def node_unavailable_handler(request: Request, exc: NodeUnavailableError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InvalidAgentAddressError)
    async def invalid_address_handler(request: Request, exc: InvalidAgentAddressError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(DiscoveryError)
    async def discovery_error_handler(request: Request, exc: DiscoveryError):
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
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "daemon": "formicxd",
            "node": node_name or "local",
        }

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

    # Agent Lifecycle Endpoints
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
        # Clean up any old stopped agent instances with the same name to prevent name resolution ambiguity
        existing_matches = [a for a in manager.list_agents() if a.name == agent.name]
        for existing in existing_matches:
            if not manager.process_manager.is_running(existing.agent_id):
                manager.unregister_agent(existing.agent_id)
        manager.register_agent(agent)
        return _serialize_agent(agent, manager)

    @app.get("/v1/agents")
    async def list_agents(status: Optional[str] = None) -> List[Dict[str, Any]]:
        manager.refresh_all_statuses()
        agents = manager.list_agents()
        if status:
            target_status = status.upper()
            agents = [a for a in agents if a.status.value.upper() == target_status]
        return [_serialize_agent(a, manager) for a in agents]

    @app.get("/v1/agents/{identifier}")
    async def get_agent(identifier: str) -> Dict[str, Any]:
        agent = _resolve_agent(identifier)
        manager.refresh_agent_status(agent.agent_id)
        return _serialize_agent(agent, manager)

    @app.post("/v1/agents/{identifier}/start")
    async def start_agent(identifier: str) -> Dict[str, Any]:
        agent = _resolve_agent(identifier)
        started = manager.start_agent(agent.agent_id)
        return _serialize_agent(started, manager)

    @app.post("/v1/agents/{identifier}/stop")
    async def stop_agent(identifier: str) -> Dict[str, Any]:
        agent = _resolve_agent(identifier)
        stopped = manager.stop_agent(agent.agent_id)
        return _serialize_agent(stopped, manager)

    @app.post("/v1/agents/{identifier}/restart")
    async def restart_agent(identifier: str) -> Dict[str, Any]:
        agent = _resolve_agent(identifier)
        restarted = manager.restart_agent(agent.agent_id)
        return _serialize_agent(restarted, manager)

    # --- Phase 3 Native Communication Layer Endpoints ---

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

    # --- Phase 5 Agent Communication Policies Endpoints ---

    @app.get("/v1/policies")
    async def list_policies() -> Dict[str, Any]:
        policies = communication_service.policy_engine.list_policies()
        return {k: v.model_dump(mode="json") for k, v in policies.items()}

    @app.get("/v1/policies/check")
    async def check_policy(source: str = Query(...), destination: str = Query(...)) -> Dict[str, Any]:
        allowed = communication_service.policy_engine.can_communicate(source, destination)
        return {
            "source": source,
            "destination": destination,
            "status": "ALLOWED" if allowed else "DENIED",
            "allowed": allowed,
        }

    # --- Phase 6 Distributed Agent Networking Endpoints ---

    @app.post("/v1/messages/remote", status_code=status.HTTP_200_OK)
    async def receive_remote_message(message: Message) -> Dict[str, Any]:
        """Receive incoming message from a remote Formicx node and route locally."""
        return communication_service.send_message(message)

    @app.get("/v1/node/info")
    async def get_node_info() -> Dict[str, Any]:
        """Get local Formicx node information and discovery status."""
        peers = communication_service.peer_registry.list_peers(active_only=True)
        disc_enabled = discovery_service.enabled if discovery_service else False
        disc_port = discovery_service.discovery_port if discovery_service else 9999
        return {
            "name": node_name or "local",
            "host": node_host or "127.0.0.1",
            "port": node_port or 8765,
            "status": "ONLINE",
            "discovery_enabled": disc_enabled,
            "discovery_port": disc_port,
            "peer_count": len(peers),
        }

    @app.get("/v1/node/peers")
    async def list_peers(active_only: bool = Query(False)) -> List[Dict[str, Any]]:
        """List registered peer nodes in the peer registry."""
        peers = communication_service.peer_registry.list_peers(active_only=active_only)
        return [p.model_dump(mode="json") for p in peers]

    @app.post("/v1/node/discover", status_code=status.HTTP_200_OK)
    async def trigger_node_discovery() -> Dict[str, Any]:
        """Trigger an immediate LAN discovery broadcast."""
        if discovery_service is None or not discovery_service.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formicx node discovery service is disabled or unavailable.",
            )
        discovery_service.send_discovery_request()
        return {
            "status": "DISCOVERY_TRIGGERED",
            "node": node_name or "local",
        }

    @app.get("/v1/node/ping/{peer_name}")
    async def ping_peer(peer_name: str) -> Dict[str, Any]:
        """Ping a remote peer node health endpoint."""
        peer = communication_service.peer_registry.get_peer(peer_name)
        return communication_service.network_transport.ping_peer(peer)

    # --- Phase 8 Agent-Aware Resource Monitoring Endpoints ---

    @app.get("/v1/resources")
    async def get_all_agent_resources() -> List[Dict[str, Any]]:
        """Get resource usage metrics for all registered agents."""
        if resource_service is None:
            return []
        resources = resource_service.get_all_resources()
        return [r.model_dump(mode="json") for r in resources]

    @app.get("/v1/agents/{identifier}/resources")
    async def get_agent_resources(identifier: str) -> Dict[str, Any]:
        """Get resource usage metrics for a specific agent by ID or name."""
        if resource_service is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formicx resource service is disabled.",
            )
        usage = resource_service.get_agent_resources(identifier)
        return usage.model_dump(mode="json")

    return app

