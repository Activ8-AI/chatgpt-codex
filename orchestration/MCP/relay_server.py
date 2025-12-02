"""
FastAPI relay that exposes MCP-facing health and activation endpoints.
"""
from __future__ import annotations

from typing import Dict
from pathlib import Path
import sys

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_hub.activate import AgentHub
from custody.custodian_ledger import CustodianLedger
from memory.sql_store.sql_store import SQLStore
from telemetry.emit_heartbeat import HeartbeatEmitter


class ActivationRequest(BaseModel):
    task: str


class ActivationResponse(BaseModel):
    status: str
    responses: Dict[str, Dict[str, str]]


def build_app() -> FastAPI:
    store = SQLStore()
    ledger = CustodianLedger(store)
    emitter = HeartbeatEmitter(ledger)
    hub = AgentHub(ledger)

    app = FastAPI(title="Codex MCP Relay", version="1.0.0")

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/heartbeat")
    def heartbeat() -> Dict[str, object]:
        heartbeat_payload = emitter.emit(source="api")
        return {"status": "ok", "heartbeat": heartbeat_payload}

    @app.post("/activate", response_model=ActivationResponse)
    def activate(request: ActivationRequest) -> ActivationResponse:
        responses = hub.activate(request.task)
        return ActivationResponse(status="ok", responses=responses)

    return app


app = build_app()


def main() -> None:
    uvicorn.run("orchestration.MCP.relay_server:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
