"""FastAPI Reconciliation Server and Web Console Backend API v2.

Provides dedicated, high-performance REST and WebSocket endpoints for the
single-page reconciliation console:
  - Paginated ingestion data grids and column statistics with PII redaction.
  - Interactive schema mapping review and confidence band inspection.
  - Policy configuration and baseline dry-run calibration telemetry.
  - Real-time matched results and balance variance summaries.
  - Paginated exception queue with auto-approval explanations and manual override actions.
  - Priority-tiered event ring buffers (Priority 1: UI narration, Priority 2: Traces, Priority 3: Silent logs).
  - Export utilities for canonical reconciled CSVs, JSON reports, and JSONL audit hash chains.
"""

import asyncio
import csv
from collections import deque
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import threading
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from fastapi import APIRouter, FastAPI, File, HTTPException, Query, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import BASE_DIR, UPLOAD_DIR
from app.core.audit import audit_for
from app.core.channels import subscribe
from app.core.constants import REG
from app.core.contracts import MessageKind
from app.core.cost import tracker_for
from app.core.dispatcher import _breakers
from app.core.masking import pii_score
from app.engine.chatbot import ReconChatSession
from app.pipeline import Pipeline

STATIC_DIR = BASE_DIR / "app" / "static"

# -----------------------------------------------------------------------------
# Per-Session Registries and Priority-Tagged Event Ring Buffers
# -----------------------------------------------------------------------------
V2_SESSIONS: Dict[str, Dict[str, Any]] = {}
CHAT_SESSIONS: Dict[str, ReconChatSession] = {}
BUFFERS: Dict[str, Dict[str, deque]] = {}  # sid -> {"trace": deque(maxlen=2000), "logs": deque(maxlen=5000)}
_WS: Dict[str, Dict[str, Any]] = {}       # sid -> {"queues": set(), "loop": loop|None}

# Regex for low-priority telemetry events routed to silent logs (Priority 3)
_P3_PATTERN = re.compile(r"^(tool_ok|cost_overrun|args_rejected|AUDIT_COMMIT)")

# High-priority control signals routed to user notification stream (Priority 1)
_P1_CONTROL = {
    "STATE_ENTERED",
    "STATE_EXITED",
    "HALT",
    "RESUMED",
    "ABORT_CONFIRMED",
    "FILE_REQUESTED",
    "CONFIRMATION_REQUESTED",
}


def _buffers(sid: str) -> Dict[str, deque]:
    """Retrieve or initialize bounded ring buffers for trace and background log streams."""
    if sid not in BUFFERS:
        BUFFERS[sid] = {"trace": deque(maxlen=2000), "logs": deque(maxlen=5000)}
    return BUFFERS[sid]


def _classify(kind: MessageKind, payload: Dict[str, Any]) -> int:
    """Classify message into priority tiers: 1=user narration/cards, 2=trace, 3=silent background logs."""
    if kind in (MessageKind.CHAT, MessageKind.ARTIFACT):
        return 1
    if kind == MessageKind.CONTROL:
        return 1 if payload.get("event") in _P1_CONTROL else 2
    return 3 if _P3_PATTERN.match(payload.get("event", "")) else 2


def _push_ws(sid: str, frame: str) -> None:
    """Safely push a JSON message frame to all active WebSocket listeners for a session."""
    s = _WS.get(sid)
    if not s or not s.get("loop"):
        return
    for q in list(s["queues"]):
        try:
            s["loop"].call_soon_threadsafe(q.put_nowait, frame)
        except Exception:
            pass


def _bus_bridge(kind: MessageKind):
    """Factory creating an event listener bridging the internal bus to ring buffers and WebSockets."""
    def handler(sid: str, model: Any, source: str) -> None:
        payload = model.model_dump()
        prio = _classify(kind, payload)
        frame = {
            "kind": kind.value,
            "priority": prio,
            "source": source,
            "payload": payload,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        buf = _buffers(sid)
        (buf["logs"] if prio == 3 else buf["trace"]).append(frame)
        _push_ws(sid, json.dumps(frame, default=str))

    return handler


_bridge_installed = False


def _install_bus_bridge() -> None:
    """Idempotently register event bus bridge subscribers across all MessageKind channels."""
    global _bridge_installed
    if _bridge_installed:
        return
    for k in MessageKind:
        subscribe(k, _bus_bridge(k))
    _bridge_installed = True


# -----------------------------------------------------------------------------
# Helper Utilities
# -----------------------------------------------------------------------------
def _sess(sid: str) -> Dict[str, Any]:
    """Retrieve session dictionary or raise HTTP 404."""
    if sid not in V2_SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    return V2_SESSIONS[sid]


def _pipe(sid: str) -> Optional[Pipeline]:
    """Retrieve active Pipeline instance for a session."""
    return _sess(sid).get("pipe")


def _totals(pipe: Optional[Pipeline]) -> Optional[Dict[str, float]]:
    """Compute gross, net, fee, matched, and exception balance sums safely before AGGREGATING."""
    if not pipe or not getattr(pipe, "cfg", None) or not pipe.cfg:
        return None
    cfg = pipe.cfg
    rows_l = pipe.tables.get(cfg.get("left_table", ""), [])
    rows_r = pipe.tables.get(cfg.get("right_table", ""), [])
    la, ra = cfg.get("left_amount"), cfg.get("right_amount")
    if not la or not ra:
        return None
    g = sum(float(x.get(la, 0) or 0) for x in rows_l)
    n = sum(float(x.get(ra, 0) or 0) for x in rows_r)
    matched_rids = {m.l_rid for m in pipe.exec_res.matched} if getattr(pipe, "exec_res", None) else set()
    mv = sum(float(x.get(la, 0) or 0) for x in rows_l if x["_rid"] in matched_rids)
    return {
        "gross": round(g, 2),
        "net": round(n, 2),
        "fees": round(g - n, 2),
        "matched_value": round(mv, 2),
        "exception_value": round(g - mv, 2),
    }


def _exception_rows(pipe: Optional[Pipeline]) -> List[Dict[str, Any]]:
    """Enrich exception queue records with row attributes, verified evidence details, and status notes."""
    rows = []
    cfg = getattr(pipe, "cfg", {}) or {}
    l_table_name = cfg.get("left_table", "payments")
    r_table_name = cfg.get("right_table", "bank")
    l_rows = {row["_rid"]: row for row in (pipe.tables.get(l_table_name, []) if getattr(pipe, "tables", None) else [])}
    r_rows = {row["_rid"]: row for row in (pipe.tables.get(r_table_name, []) if getattr(pipe, "tables", None) else [])}

    for item in getattr(pipe, "queue", None) or []:
        rec = item["rec"]
        action = item.get("action", "mark_pending")
        explanation = item.get("explanation") or getattr(rec, "explanation", None) or ""

        # Source record attributes
        src_table = l_table_name if rec.side == "L" else r_table_name
        src_row = (l_rows if rec.side == "L" else r_rows).get(rec.rid, {})
        record_data = {k: v for k, v in src_row.items() if not k.startswith("_")}

        # Formulate verified evidence details
        conf = item.get("conf", 0.0)
        pieces = [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])]

        piece_details = []
        for p in pieces:
            if p == "key_match":
                piece_details.append(f"key_match=1.0 (exact reference '{rec.ref}')")
            elif p == "amount_within_tol":
                delta_str = f"diff={abs(rec.delta):.2f}" if rec.delta is not None else "exact parity"
                piece_details.append(f"amount_within_tol=1.0 ({delta_str})")
            elif p == "date_within_window":
                piece_details.append("date_within_window=1.0 (clearing timeframe)")
            elif p == "fee_model_match":
                piece_details.append(f"fee_model_match=1.0 (diff={abs(rec.delta or 0):.2f} matches fee schedule)")
            else:
                piece_details.append(f"{p}=1.0")

        evidence_str = (
            f"{len(pieces)} verified evidence factors: {', '.join(piece_details)}"
            if piece_details
            else "rule consistency"
        )

        if action in ("auto_resolve", "mark_resolved"):
            auto_reason = f"Approved by engine: confidence={conf:.2f}, {evidence_str}."
        elif action == "declined":
            auto_reason = f"Rejected / Declined by operator review: confidence={conf:.2f} did not pass manual verification."
        elif action in ("escalate", "request_confirmation"):
            auto_reason = f"Awaiting operator review: confidence={conf:.2f}, {evidence_str}; potential variance or anomaly detected."
        else:
            auto_reason = f"Pending engine evaluation: confidence={conf:.2f}."

        rows.append({
            "rid": rec.rid,
            "side": rec.side,
            "source_table": src_table,
            "ref": rec.ref,
            "reason": rec.reason.value if hasattr(rec.reason, "value") else str(rec.reason),
            "delta": rec.delta,
            "confidence": round(conf, 3),
            "action": action,
            "explanation": explanation,
            "auto_reason": auto_reason,
            "manual_match_ref": item.get("manual_match_ref", ""),
            "record_data": record_data,
            "pieces": pieces,
        })
    return rows


def _paginate(items: List[Any], page: int, page_size: int) -> Dict[str, Any]:
    """Paginate an in-memory list and return sliced items with navigation metadata."""
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


# -----------------------------------------------------------------------------
# API v2 Router — Endpoint per Web Console Panel
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.post("/sessions")
def create_session() -> Dict[str, str]:
    """Create a new reconciliation session for API v2."""
    sid = uuid.uuid4().hex[:8]
    V2_SESSIONS[sid] = {"pipe": None, "files": {}}
    CHAT_SESSIONS[sid] = ReconChatSession(sid)
    _buffers(sid)
    audit_for(sid).append({"event": "SESSION_INITIALIZED", "session_id": sid})
    return {"session_id": sid}


@router.get("/sessions/{sid}/overview")
def overview(sid: str) -> Dict[str, Any]:
    """Retrieve high-level pipeline status, circuit breaker states, and token expenditures."""
    _sess(sid)
    pipe = _pipe(sid)
    brk = {t: c for (s, t), c in _breakers.items() if s == sid}
    files_map = V2_SESSIONS[sid].get("files", {})
    return {
        "session_id": sid,
        "state": pipe.sm.state.value if pipe and pipe.sm.state else "IDLE",
        "abort_token": pipe.sm._token if pipe else None,
        "halted": bool(pipe and pipe.sm.state and pipe.sm.state.value == "HALT"),
        "circuit_breaker": {
            "threshold": REG["circuit_breaker_failure_count"],
            "tools": brk,
            "open": any(c >= REG["circuit_breaker_failure_count"] for c in brk.values()),
        },
        "cost_usd": round(tracker_for(sid).total, 6),
        "constants_version": REG.version,
        "audit_count": len(audit_for(sid).records),
        "files": list(files_map.keys()),
        "table_counts": {
            k: len(v)
            for k, v in (pipe.tables if pipe and getattr(pipe, "tables", None) else {}).items()
        },
    }


@router.get("/sessions/{sid}/ingestion")
def ingestion(
    sid: str,
    table: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
) -> Dict[str, Any]:
    """Retrieve ingested tables with pagination and column statistics with PII redaction."""
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "tables", None):
        return {"tables": {}, "profiles": {}, "table_meta": {}}

    profiles = {}
    mask_at, review_at = REG["pii_mask_threshold"], REG["pii_review_threshold"]
    for name, profs in getattr(pipe, "profiles", {}).items():
        out = []
        for p in profs:
            d = p.model_dump()
            if d["pii_likelihood"] >= mask_at:
                d["sample_values"] = ["[MASKED:pii]"]
            elif d["pii_likelihood"] >= review_at:
                d["pii_review"] = True
            out.append(d)
        profiles[name] = out

    # Build metadata counts for all ingested tables
    table_meta = {}
    for name, rows in pipe.tables.items():
        cols = [k for k in (rows[0].keys() if rows else []) if not k.startswith("_")]
        table_meta[name] = {"total_rows": len(rows), "columns": cols}

    # Paginate specific table or default first pages
    tables = {}
    if table and table in pipe.tables:
        pg = _paginate(pipe.tables[table], page, page_size)
        tables[table] = pg
    elif table:
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found")
    else:
        for name, rows in pipe.tables.items():
            pg = _paginate(rows, page, page_size)
            tables[name] = pg

    return {
        "session_id": sid,
        "tables": tables,
        "profiles": profiles,
        "table_meta": table_meta,
    }


@router.get("/sessions/{sid}/mapping")
def mapping(sid: str) -> Dict[str, Any]:
    """Retrieve candidate schema links, composite confidence scores, and committed mapping fields."""
    pipe = _pipe(sid)
    if not pipe:
        return {"candidates": [], "committed": None, "confidence": 0.0}
    cands = []
    w = (
        REG["w_mapping_structural"],
        REG["w_mapping_sample"],
        REG["w_mapping_type"],
        REG["w_mapping_semantic"],
    )
    for ov, lt, lc, rt, rc in getattr(pipe, "_map_cands", [])[:6]:
        lp = next((p for p in pipe.profiles.get(lt, []) if p.name == lc), None)
        rp = next((p for p in pipe.profiles.get(rt, []) if p.name == rc), None)
        tc = 1.0 if (lp and rp and lp.dtype == rp.dtype) else 0.4
        sem = 0.5
        composite = w[0] * ov + w[1] * ov + w[2] * tc + w[3] * sem
        cands.append({
            "left": f"{lt}.{lc}",
            "right": f"{rt}.{rc}",
            "signals": {
                "structural_overlap": round(ov, 3),
                "sample_match_rate": round(ov, 3),
                "type_compatibility": tc,
                "semantic_plausibility": sem,
            },
            "composite": round(composite, 3),
            "band": (
                "auto"
                if composite >= REG["mapping_auto_accept"]
                else ("confirm" if composite >= REG["mapping_review_floor"] else "escalate")
            ),
        })
    return {
        "candidates": cands,
        "committed": (
            {
                k: pipe.cfg.get(k)
                for k in (
                    "left_table",
                    "right_table",
                    "left_key",
                    "right_key",
                    "left_amount",
                    "right_amount",
                    "left_date",
                    "right_date",
                    "tolerance",
                    "window_days",
                )
            }
            if pipe.cfg
            else None
        ),
        "confidence": round(getattr(pipe, "_map_conf", 0.0), 3),
        "ambiguous": getattr(pipe, "_ambiguous", False),
        "ambiguity_delta": REG["mapping_ambiguity_delta"],
    }


@router.get("/sessions/{sid}/policy")
def policy(sid: str) -> Dict[str, Any]:
    """Retrieve synthesized matching policy components, baseline calibrations, and fee schedules."""
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "policy_doc", None):
        return {"components": [], "baseline_match_rate": None, "revision_history": []}
    doc = pipe.policy_doc
    return {
        "components": [c.model_dump() for c in doc.components],
        "generated_from": doc.generated_from,
        "baseline_match_rate": doc.baseline_match_rate,
        "baseline_source": doc.baseline_source,
        "baseline_constants_version": doc.baseline_constants_version,
        "revision_history": doc.revision_history,
        "current_match_rate": getattr(pipe, "match_rate", None),
        "revision_caps": {
            "iterations": REG["revision_iteration_cap"],
            "seconds": REG["revision_time_cap_s"],
            "usd": REG["revision_cost_cap_usd"],
        },
        "fee_schedules": [fs.model_dump(mode="json") for fs in REG.fee_schedules.values()],
    }


@router.get("/sessions/{sid}/results")
def results(sid: str) -> Dict[str, Any]:
    """Retrieve matched record pairs enriched with source attributes and financial totals."""
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "exec_res", None):
        return {"executed": False}
    r = pipe.exec_res

    cfg = getattr(pipe, "cfg", {}) or {}
    l_table_name = cfg.get("left_table", "payments")
    r_table_name = cfg.get("right_table", "bank")
    l_rows = {row["_rid"]: row for row in (pipe.tables.get(l_table_name, []) if getattr(pipe, "tables", None) else [])}
    r_rows = {row["_rid"]: row for row in (pipe.tables.get(r_table_name, []) if getattr(pipe, "tables", None) else [])}

    enriched_matched = []
    for m in r.matched:
        m_dict = m.model_dump()
        m_dict["l_data"] = {k: v for k, v in l_rows.get(m.l_rid, {}).items() if not k.startswith("_")}
        m_dict["r_data"] = {k: v for k, v in r_rows.get(m.r_rid, {}).items() if not k.startswith("_")}
        enriched_matched.append(m_dict)

    return {
        "executed": True,
        "match_rate": getattr(pipe, "match_rate", None),
        "precision_vs_truth": getattr(pipe, "precision", None),
        "recall_vs_truth": getattr(pipe, "recall", None),
        "throughput_rows_per_sec": getattr(pipe, "throughput", None),
        "matched": enriched_matched,
        "unmatched_count": len(r.unmatched),
        "duplicates": r.duplicates,
        "splits": r.splits,
        "variance": r.variance.model_dump(),
        "totals": _totals(pipe),
        "final_report": pipe.final.model_dump(mode="json") if getattr(pipe, "final", None) else None,
    }


@router.get("/sessions/{sid}/exceptions")
def exceptions(
    sid: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> Dict[str, Any]:
    """Retrieve paginated exception queue items with confidence breakdowns and action status."""
    pipe = _pipe(sid)
    if not pipe:
        return {"queue": [], "pagination": None}
    all_rows = _exception_rows(pipe)
    pg = _paginate(all_rows, page, page_size)
    return {
        "queue": pg["items"],
        "pagination": {k: v for k, v in pg.items() if k != "items"},
        "auto_resolve_gate": {
            "confidence": REG["exception_auto_resolve_confidence"],
            "evidence_min": REG["exception_auto_resolve_evidence_min"],
        },
        "summary": {
            "total": len(all_rows),
            "auto_resolved": sum(1 for r in all_rows if r["action"] in ("auto_resolve", "mark_resolved")),
            "needs_review": sum(1 for r in all_rows if r["action"] in ("request_confirmation", "escalate")),
            "pending": sum(1 for r in all_rows if r["action"] == "mark_pending"),
        },
    }


class ActionBody(BaseModel):
    """Payload schema for an operator exception action."""
    action: str          # "approve" | "decline" | "escalate"
    match_ref: str = ""  # Optional target reference ID to pair with
    note: str = ""


@router.post("/sessions/{sid}/exceptions/{rid}/action")
def exception_action(sid: str, rid: int, body: ActionBody) -> Dict[str, Any]:
    """Apply operator override decision to an exception and update report balance invariant."""
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "queue", None):
        raise HTTPException(status_code=404, detail="no exception queue")
    item = next((i for i in pipe.queue if i["rec"].rid == rid), None)
    if not item:
        raise HTTPException(status_code=404, detail="exception not found")

    prior_action = item.get("action", "mark_pending")
    prior = {
        "action": prior_action,
        "confidence": item.get("conf", 0.0),
        "reason": item["rec"].reason.value if hasattr(item["rec"].reason, "value") else str(item["rec"].reason),
        "pieces": [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])],
    }

    if body.action == "approve":
        item["action"] = "mark_resolved"
        if body.match_ref:
            item["manual_match_ref"] = body.match_ref
            item["rec"].ref = body.match_ref
    elif body.action == "decline":
        item["action"] = "declined"
    else:
        item["action"] = "escalate"

    audit_for(sid).append({
        "event": "USER_OVERRIDE",
        "rid": rid,
        "action": item["action"],
        "match_ref": body.match_ref if body.match_ref else None,
        "note": body.note,
        "prior": prior,
    })

    counts = None
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
        if prior_action != item["action"]:
            pipe.final.llm_user_disagreements.append({
                "rid": rid,
                "system_proposal": prior,
                "user_decision": {
                    "action": item["action"],
                    "match_ref": body.match_ref,
                    "note": body.note,
                },
                "disagreement_kind": "exception_override",
            })
        counts = {
            "auto_resolved": pipe.final.auto_resolved_count,
            "escalated": pipe.final.escalated_count,
            "unresolved": pipe.final.unresolved_count,
            "honest_total": pipe.final.honest_exception_count,
        }
    return {"ok": True, "rid": rid, "action": item["action"], "counts": counts}


@router.get("/sessions/{sid}/audit")
def audit(sid: str) -> Dict[str, Any]:
    """Retrieve full audit log records and cryptographic verification status."""
    log = audit_for(sid)
    return {"records": log.records, "verified": log.verify(), "count": len(log.records)}


@router.get("/sessions/{sid}/export.csv")
def export_reconciliation_csv(sid: str) -> StreamingResponse:
    """Generate a canonical reconciled output CSV combining matched pairs and classified exceptions."""
    pipe = _pipe(sid)
    if not pipe:
        raise HTTPException(status_code=404, detail="no pipeline")

    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow([
        "type",
        "l_rid",
        "r_rid",
        "ref",
        "side",
        "reason",
        "composite_score_or_confidence",
        "delta",
        "action",
        "explanation",
    ])

    # Write Matched Pairs
    if getattr(pipe, "exec_res", None) and getattr(pipe.exec_res, "matched", None):
        for m in pipe.exec_res.matched:
            writer.writerow([
                "matched",
                m.l_rid,
                m.r_rid,
                "",
                "",
                "",
                m.composite_score,
                "",
                "matched",
                "",
            ])

    # Write Exception Items
    if getattr(pipe, "queue", None):
        for item in pipe.queue:
            rec = item["rec"]
            writer.writerow([
                "exception",
                rec.rid if rec.side == "L" else "",
                rec.rid if rec.side == "R" else "",
                rec.ref or "",
                rec.side,
                rec.reason.value if hasattr(rec.reason, "value") else str(rec.reason),
                item.get("conf", 0.0),
                rec.delta if rec.delta is not None else "",
                item.get("action", "mark_pending"),
                (item.get("explanation") or getattr(rec, "explanation", "") or "").replace("\n", " "),
            ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reconciliation_output_{sid}.csv"},
    )


@router.get("/sessions/{sid}/export/report.json")
def export_report_json(sid: str) -> StreamingResponse:
    """Download the finalized reconciliation report as JSON."""
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "final", None):
        raise HTTPException(status_code=404, detail="no final report yet")

    return StreamingResponse(
        iter([pipe.final.model_dump_json(indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=final_report_{sid}.json"},
    )


@router.get("/sessions/{sid}/export/audit.jsonl")
def export_audit_jsonl(sid: str) -> StreamingResponse:
    """Download the complete cryptographic audit chain as a JSONL stream."""
    log = audit_for(sid)
    lines = [json.dumps(r, default=str) for r in log.records]

    return StreamingResponse(
        iter(["\n".join(lines)]),
        media_type="application/jsonl",
        headers={"Content-Disposition": f"attachment; filename=audit_chain_{sid}.jsonl"},
    )


@router.get("/sessions/{sid}/trace")
def trace(sid: str) -> Dict[str, Any]:
    """Fetch stored execution telemetry events from the session trace ring buffer."""
    _sess(sid)
    return {"events": list(_buffers(sid)["trace"])}


@router.get("/sessions/{sid}/logs")
def logs(sid: str) -> Dict[str, Any]:
    """Fetch stored background log events from the session log ring buffer."""
    _sess(sid)
    return {"events": list(_buffers(sid)["logs"])}


# -----------------------------------------------------------------------------
# Mutations
# -----------------------------------------------------------------------------
@router.post("/sessions/{sid}/run")
async def run(sid: str, files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """Upload files and execute the reconciliation pipeline asynchronously."""
    sess = _sess(sid)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for f in files:
        p = UPLOAD_DIR / f"{sid}_{f.filename}"
        p.write_bytes(await f.read())
        sess["files"][f.filename] = p
        paths.append(p)
    if len(paths) < 2:
        raise HTTPException(status_code=400, detail="need at least two tables (ledger + statement)")

    pipe = Pipeline(sid, auto_ack=True)
    sess["pipe"] = pipe
    if sid in CHAT_SESSIONS:
        CHAT_SESSIONS[sid].set_pipe(pipe)
    audit_for(sid).append({
        "event": "RUN_STARTED",
        "files": [p.name for p in paths],
        "ts": datetime.now(timezone.utc).isoformat(),
    })

    def work():
        try:
            pipe.run(paths)
        except Exception as e:
            import traceback
            traceback.print_exc()

    threading.Thread(target=work, daemon=True).start()
    return {"ok": True, "files": [p.name for p in paths]}


@router.post("/sessions/{sid}/resume")
def resume(sid: str) -> Dict[str, Any]:
    """Resume a halted pipeline run from its pre-halt state in a background thread."""
    pipe = _pipe(sid)
    if not pipe:
        raise HTTPException(status_code=400, detail="no pipeline to resume")
    pipe.sm.resume()

    def cont():
        pipe.continue_run()

    threading.Thread(target=cont, daemon=True).start()
    return {"ok": True, "state": pipe.sm.state.value}


@router.post("/sessions/{sid}/restart")
def restart(sid: str) -> Dict[str, Any]:
    """Reset session pipeline, clear ring buffers, and record restart audit event."""
    sess = _sess(sid)
    sess["pipe"] = None
    sess["files"] = {}
    if sid in CHAT_SESSIONS:
        CHAT_SESSIONS.pop(sid, None)
    if sid in BUFFERS:
        BUFFERS[sid]["trace"].clear()
        BUFFERS[sid]["logs"].clear()
    audit_for(sid).append({
        "event": "ENGINE_RESTARTED",
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "session_id": sid}


@router.delete("/sessions/{sid}/files/{filename}")
def delete_file(sid: str, filename: str) -> Dict[str, Any]:
    """Delete uploaded file from the session's upload cache."""
    sess = _sess(sid)
    if filename in sess.get("files", {}):
        p = sess["files"].pop(filename)
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    return {"ok": True, "deleted": filename}


class AbortBody(BaseModel):
    """Payload schema for requesting a pipeline abort."""
    token: str


@router.post("/sessions/{sid}/abort")
def abort(sid: str, body: AbortBody) -> Dict[str, bool]:
    """Request pipeline abort using the active state abort token."""
    pipe = _pipe(sid)
    if not pipe:
        raise HTTPException(status_code=400, detail="no pipeline to abort")
    pipe.sm.request_abort(body.token)
    return {"ok": True}


class ChatBody(BaseModel):
    """Payload schema for assistant chat queries in API v2."""
    message: str


@router.post("/sessions/{sid}/chat")
def chat(sid: str, body: ChatBody) -> Dict[str, Any]:
    """Submit a question to the grounded AI reconciliation assistant."""
    _sess(sid)
    if sid not in CHAT_SESSIONS:
        CHAT_SESSIONS[sid] = ReconChatSession(sid, _pipe(sid))
    else:
        CHAT_SESSIONS[sid].set_pipe(_pipe(sid))
    return CHAT_SESSIONS[sid].chat(body.message)


# -----------------------------------------------------------------------------
# WebSocket Handler
# -----------------------------------------------------------------------------
async def ws_v2(websocket: WebSocket, sid: str) -> None:
    """WebSocket streaming endpoint for API v2 event telemetry."""
    await websocket.accept()
    s = _WS.setdefault(sid, {"queues": set(), "loop": None})
    q: asyncio.Queue = asyncio.Queue()
    s["queues"].add(q)
    s["loop"] = asyncio.get_running_loop()
    try:
        await websocket.send_text(
            json.dumps({
                "kind": "control",
                "priority": 1,
                "source": "system",
                "payload": {"event": "WS_CONNECTED", "session": sid},
                "ts": datetime.now(timezone.utc).isoformat(),
            })
        )
        while True:
            await websocket.send_text(await q.get())
    except (asyncio.CancelledError, Exception):
        pass
    finally:
        s["queues"].discard(q)


# -----------------------------------------------------------------------------
# Mounting
# -----------------------------------------------------------------------------
def mount_v2(app: FastAPI) -> FastAPI:
    """Mount API v2 routes, CORS middleware, WebSocket handler, and static file endpoints."""
    _install_bus_bridge()
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    # Enable CORS for browser integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    # WebSocket route on root app
    app.add_api_websocket_route("/ws/v2/{sid}", ws_v2)

    @app.get("/console", include_in_schema=False)
    def console():
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        return HTMLResponse(
            "<code>app/static/index.html not found — save the console build there, "
            "then reload /console</code>",
            status_code=404,
        )

    # Mount static assets directory
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


# -----------------------------------------------------------------------------
# Standalone Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    app = FastAPI(title="Razorpay Recon Agent API v2")
    mount_v2(app)
    uvicorn.run(app, host="127.0.0.1", port=8000)

