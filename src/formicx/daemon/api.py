from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from formicx.enums.agent_status import AgentStatus
from formicx.manifests.loader import load_agent_manifest
from formicx.models.agent import Agent
from formicx.runtime.manager import AgentManager


class RegisterRequest(BaseModel):
    """Payload for registering an agent from a manifest file or directory."""

    path: str


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


def create_daemon_app(manager: AgentManager) -> FastAPI:
    """Create the FastAPI local control application bound to an AgentManager instance."""
    app = FastAPI(
        title="Formicx Daemon Control API",
        description="Local control interface for formicxd daemon.",
        version="0.2.0",
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
    async def list_agents() -> List[Dict[str, Any]]:
        manager.refresh_all_statuses()
        return [_serialize_agent(agt, manager) for agt in manager.list_agents()]

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

    return app
