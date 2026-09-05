"""FastAPI Reconciliation Server and REST/WebSocket API v1.

Provides backend API endpoints for session lifecycle management, multipart file
upload/deletion, asynchronous pipeline execution, interactive grounded AI chat,
real-time WebSocket event broadcasting, and operator override actions.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sys
import threading
from typing import Any, Dict, List, Optional, Set
import uuid

# Ensure src/ is in sys.path for direct module execution
_SRC_DIR = Path(__file__).resolve().parent.parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket
from pydantic import BaseModel

from app import config
from app.config import LOGS_DIR, UPLOAD_DIR
from app.core.audit import audit_for
from app.core.channels import subscribe, validate_and_route
from app.core.constants import REG
from app.core.contracts import MessageKind
from app.engine.chatbot import ReconChatSession
from app.pipeline import Pipeline
from app.server.api_v2 import mount_v2

# Configure server file logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SERVER_LOG_PATH = LOGS_DIR / "server.log"
LATEST_SESSION_LOG = LOGS_DIR / "session.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(SERVER_LOG_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("recon_agent")

app = FastAPI(title="Razorpay Reconciliation Agent API")

# Mount API v2 routes and static web console
mount_v2(app)

# In-memory session and chatbot registries
SESSIONS: Dict[str, Dict[str, Any]] = {}
CHAT_SESSIONS: Dict[str, ReconChatSession] = {}


def _write_session_log(sid: str, log_line: str) -> None:
    """Write an event line to both the per-session log file and the latest session.log pointer.
    
    Args:
        sid: Unique session identifier string.
        log_line: Serialized JSON log line string.
    """
    try:
        logs_dir = getattr(config, "LOGS_DIR", LOGS_DIR)
        logs_dir.mkdir(parents=True, exist_ok=True)
        session_file = logs_dir / f"{sid}.log"
        with open(session_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
        latest_session_log = logs_dir / "session.log"
        with open(latest_session_log, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception as e:
        logger.error(f"Failed to write session log: {e}")


def _bridge(kind: MessageKind):
    """Factory creating an event subscriber that logs events and pushes to active WebSockets."""
    def fn(sid: str, model: Any, source: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        log_entry = json.dumps(
            {
                "ts": ts,
                "sid": sid,
                "kind": kind.value,
                "source": source,
                "payload": model.model_dump(),
            },
            default=str,
        )
        _write_session_log(sid, log_entry)
        logger.info(f"[{sid}] [{source}] {kind.value}: {json.dumps(model.model_dump(), default=str)[:140]}")

        s = SESSIONS.get(sid)
        if not s or not s.get("loop"):
            return
        item = json.dumps(
            {"kind": kind.value, "source": source, "payload": model.model_dump()},
            default=str,
        )
        for aq in list(s["queues"]):
            s["loop"].call_soon_threadsafe(aq.put_nowait, item)

    return fn


# Subscribe bridge handlers for all MessageKind event streams
for _k in MessageKind:
    subscribe(_k, _bridge(_k))


@app.post("/api/sessions")
def new_session() -> Dict[str, str]:
    """Initialize a new reconciliation session with fresh log buffers and audit trails."""
    sid = uuid.uuid4().hex[:8]
    SESSIONS[sid] = {"pipe": None, "queues": set(), "loop": None, "files": {}}
    CHAT_SESSIONS[sid] = ReconChatSession(sid)

    # Clear and initialize fresh session log file
    logs_dir = getattr(config, "LOGS_DIR", LOGS_DIR)
    logs_dir.mkdir(parents=True, exist_ok=True)
    session_file = logs_dir / f"{sid}.log"
    latest_session_log = logs_dir / "session.log"
    session_file.write_text("", encoding="utf-8")
    latest_session_log.write_text("", encoding="utf-8")

    init_msg = json.dumps({
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "SESSION_INITIALIZED",
        "session_id": sid,
    })
    _write_session_log(sid, init_msg)
    logger.info(f"Initialized new session {sid} (cleared active session.log)")

    return {"session_id": sid}


@app.get("/api/sessions/{sid}/files")
def list_files(sid: str) -> Dict[str, Any]:
    """List all uploaded statement files and currently active ingested tables for a session."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    pipe = SESSIONS[sid].get("pipe")
    files_map = SESSIONS[sid].get("files", {})
    tables = list(pipe.tables.keys()) if pipe and getattr(pipe, "tables", None) else []
    return {
        "session_id": sid,
        "files": [
            {
                "filename": fname,
                "path": str(fpath),
                "size": fpath.stat().st_size if fpath.exists() else 0,
            }
            for fname, fpath in files_map.items()
        ],
        "active_tables": tables,
    }


@app.post("/api/sessions/{sid}/files")
async def add_files(sid: str, files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """Upload new CSV/Excel statement files to the session upload directory."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    files_map = SESSIONS[sid].setdefault("files", {})
    added = []
    for f in files:
        p = UPLOAD_DIR / f"{sid}_{f.filename}"
        p.write_bytes(await f.read())
        files_map[f.filename] = p
        added.append(f.filename)

    audit_for(sid).append({
        "event": "FILES_ADDED",
        "filenames": added,
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    logger.info(f"[{sid}] Added files: {added}")
    return {"ok": True, "added": added, "total_files": list(files_map.keys())}


@app.delete("/api/sessions/{sid}/files/{filename}")
def delete_file(sid: str, filename: str) -> Dict[str, Any]:
    """Delete a file from disk, purge its table from active memory, and reset chat history."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    files_map = SESSIONS[sid].get("files", {})
    target_path = files_map.pop(filename, None)
    if target_path and target_path.exists():
        try:
            os.remove(target_path)
        except Exception as e:
            logger.warning(f"Could not remove file on disk {target_path}: {e}")

    pipe = SESSIONS[sid].get("pipe")
    # Clean up corresponding table from pipeline tables if exists
    stem = Path(filename).stem
    if pipe and getattr(pipe, "tables", None) and stem in pipe.tables:
        del pipe.tables[stem]

    # Reset chat session context so no old deleted data leaks into chat
    if sid in CHAT_SESSIONS:
        CHAT_SESSIONS[sid].history = []
        CHAT_SESSIONS[sid].set_pipe(pipe)

    audit_for(sid).append({
        "event": "FILE_DELETED",
        "deleted_filename": filename,
        "remaining_files": list(files_map.keys()),
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    logger.info(f"[{sid}] Deleted file {filename}. Remaining: {list(files_map.keys())}")
    return {"ok": True, "deleted": filename, "remaining_files": list(files_map.keys())}


@app.post("/api/sessions/{sid}/run")
async def run(sid: str, files: List[UploadFile] = File(...)) -> Dict[str, bool]:
    """Upload files and initiate pipeline execution in a background worker thread."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    files_map = SESSIONS[sid].setdefault("files", {})
    for f in files:
        p = UPLOAD_DIR / f"{sid}_{f.filename}"
        p.write_bytes(await f.read())
        paths.append(p)
        files_map[f.filename] = p

    pipe = Pipeline(sid, auto_ack=False)
    SESSIONS[sid]["pipe"] = pipe
    if sid in CHAT_SESSIONS:
        CHAT_SESSIONS[sid].set_pipe(pipe)

    def work():
        pipe.run(paths)
        if getattr(pipe, "queue", None) is not None:
            validate_and_route(
                sid,
                MessageKind.ARTIFACT,
                {
                    "kind": "exceptions",
                    "rows": [
                        {
                            "rid": i["rec"].rid,
                            "side": i["rec"].side,
                            "ref": i["rec"].ref,
                            "reason": i["rec"].reason.value,
                            "delta": i["rec"].delta,
                            "confidence": round(i["conf"], 3),
                            "action": i["action"],
                            "pieces": [p.value if hasattr(p, "value") else p for p in i["pieces"]],
                        }
                        for i in pipe.queue
                    ],
                    "summary": {"count": len(pipe.queue)},
                    "confidence_threshold": REG["exception_auto_resolve_confidence"],
                    "fallback_events": pipe.fb,
                },
                "server",
            )

    threading.Thread(target=work, daemon=True).start()
    return {"ok": True}


class ChatRequest(BaseModel):
    """Payload schema for grounded AI assistant chat queries."""
    message: str


@app.post("/api/sessions/{sid}/chat")
def chat_endpoint(sid: str, body: ChatRequest) -> Dict[str, Any]:
    """Submit a question to the grounded AI assistant for the specified session."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    pipe = SESSIONS[sid].get("pipe")
    if sid not in CHAT_SESSIONS:
        CHAT_SESSIONS[sid] = ReconChatSession(sid, pipe)
    else:
        CHAT_SESSIONS[sid].set_pipe(pipe)

    return CHAT_SESSIONS[sid].chat(body.message)


@app.websocket("/ws/{sid}")
async def ws(websocket: WebSocket, sid: str) -> None:
    """WebSocket connection endpoint streaming real-time event bus messages to clients."""
    await websocket.accept()
    s = SESSIONS.setdefault(sid, {"pipe": None, "queues": set(), "loop": None, "files": {}})
    aq: asyncio.Queue = asyncio.Queue()
    s["queues"].add(aq)
    s["loop"] = asyncio.get_running_loop()
    try:
        while True:
            await websocket.send_text(await aq.get())
    except Exception:
        s["queues"].discard(aq)


@app.get("/api/sessions/{sid}/audit")
def audit(sid: str) -> Dict[str, Any]:
    """Retrieve full audit log history and cryptographic SHA-256 verification status."""
    log = audit_for(sid)
    return {"records": log.records, "verified": log.verify()}


@app.get("/api/sessions/{sid}/report")
def report(sid: str) -> Dict[str, Any]:
    """Retrieve the FinalReport model for the session, if completed."""
    pipe = SESSIONS.get(sid, {}).get("pipe")
    return {"report": pipe.final.model_dump() if pipe and getattr(pipe, "final", None) else None}


@app.get("/api/sessions/{sid}/input_data")
@app.get("/api/sessions/{sid}/data")
def get_input_data(sid: str) -> Dict[str, Any]:
    """Retrieve raw ingested table dictionaries and statistical column profiles."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    pipe = SESSIONS[sid].get("pipe")
    if not pipe or not getattr(pipe, "tables", None):
        return {"session_id": sid, "tables": {}, "profiles": {}}
    profiles = {k: [p.model_dump() for p in v] for k, v in getattr(pipe, "profiles", {}).items()}
    return {
        "session_id": sid,
        "tables": pipe.tables,
        "profiles": profiles,
    }


@app.post("/api/sessions/{sid}/exceptions/{rid}/action")
def override(sid: str, rid: int, body: Dict[str, Any]) -> Dict[str, bool]:
    """Execute an operator override on an exception item (approve, escalate, or decline)."""
    pipe = SESSIONS[sid]["pipe"]
    item = next((i for i in pipe.queue if i["rec"].rid == rid), None)
    if not item:
        return {"ok": False}
    prior_action = item.get("action", "mark_pending")
    prior_conf = item.get("conf", 0.0)
    prior_reason = item["rec"].reason.value if hasattr(item["rec"].reason, "value") else str(item["rec"].reason)

    act = (body.get("action") or "").lower()
    if act == "approve":
        new_action = "mark_resolved"
    elif act in ("decline", "reject"):
        new_action = "declined"
    else:
        new_action = "escalate"
    item["action"] = new_action

    prior_decision = {
        "action": prior_action,
        "confidence": prior_conf,
        "reason": prior_reason,
        "pieces": [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])],
    }
    audit_for(sid).append({
        "event": "USER_OVERRIDE",
        "rid": rid,
        "action": item["action"],
        "note": body.get("note", ""),
        "prior": prior_decision,
    })

    if getattr(pipe, "final", None) is not None:
        pipe.final.auto_resolved_count = sum(
            1 for e in pipe.queue if e.get("action") in ("auto_resolve", "mark_resolved")
        )
        pipe.final.escalated_count = sum(
            1 for e in pipe.queue if e.get("action") in ("request_confirmation", "escalate")
        )
        pipe.final.unresolved_count = sum(
            1 for e in pipe.queue if e.get("action") in ("mark_pending", "declined")
        )
        if prior_action != new_action:
            pipe.final.llm_user_disagreements.append({
                "rid": rid,
                "system_proposal": prior_decision,
                "user_decision": {"action": new_action, "note": body.get("note", "")},
                "disagreement_kind": "exception_override",
            })
        validate_and_route(
            sid,
            MessageKind.ARTIFACT,
            {
                "kind": "report",
                "summary": pipe.final.model_dump(),
                "confidence_threshold": REG["match_auto_threshold"],
                "fallback_events": pipe.fb,
            },
            "engine",
        )

    return {"ok": True}


@app.post("/api/sessions/{sid}/resume")
def resume(sid: str) -> Dict[str, bool]:
    """Resume a halted pipeline run from its pre-halt state."""
    pipe = SESSIONS[sid]["pipe"]
    pipe.sm.resume()

    def cont():
        pipe.continue_run()
        if getattr(pipe, "queue", None) is not None:
            validate_and_route(
                sid,
                MessageKind.ARTIFACT,
                {
                    "kind": "exceptions",
                    "rows": [
                        {
                            "rid": i["rec"].rid,
                            "side": i["rec"].side,
                            "ref": i["rec"].ref,
                            "reason": i["rec"].reason.value,
                            "delta": i["rec"].delta,
                            "confidence": round(i["conf"], 3),
                            "action": i["action"],
                            "pieces": [p.value if hasattr(p, "value") else p for p in i["pieces"]],
                        }
                        for i in pipe.queue
                    ],
                    "summary": {"count": len(pipe.queue)},
                    "confidence_threshold": REG["exception_auto_resolve_confidence"],
                    "fallback_events": pipe.fb,
                },
                "server",
            )

    threading.Thread(target=cont, daemon=True).start()
    return {"ok": True}


@app.post("/api/sessions/{sid}/abort")
def abort(sid: str, body: Dict[str, Any]) -> Dict[str, bool]:
    """Request pipeline abort using the active state abort token."""
    SESSIONS[sid]["pipe"].sm.request_abort(body["token"])
    return {"ok": True}


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Razorpay Reconciliation Web Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn auto-reload")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


