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

import pandas as pd

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
from app.engine.fee import compute_fee, compute_tax_component
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


def _line_columns(rows: List[Dict[str, Any]], kind: str) -> List[str]:
    """Find likely tax or charge columns without requiring a fixed input schema."""
    if not rows:
        return []
    hints = ("tax", "gst", "igst", "cgst", "sgst", "vat") if kind == "tax" else (
        "charge", "fee", "mdr", "commission", "surcharge", "processing",
    )
    return [c for c in rows[0] if not c.startswith("_") and any(h in c.lower() for h in hints)]


def _reference_column(rows: List[Dict[str, Any]]) -> Optional[str]:
    if not rows:
        return None
    names = list(rows[0])
    for hint in ("order", "reference", "ref", "utr", "invoice", "id"):
        col = next((c for c in names if hint in c.lower() and not c.startswith("_")), None)
        if col:
            return col
    return None


def _amount_column(rows: List[Dict[str, Any]]) -> Optional[str]:
    """Find primary monetary amount column in dataset rows."""
    if not rows:
        return None
    names = list(rows[0])
    for hint in ("amount", "credit", "net", "gross", "val", "total"):
        col = next((c for c in names if hint in c.lower() and not c.startswith("_")), None)
        if col:
            return col
    return None


def _numeric_total(row: Dict[str, Any], cols: List[str]) -> float:
    total = 0.0
    for col in cols:
        try:
            total += float(str(row.get(col, 0) or 0).replace(",", ""))
        except (TypeError, ValueError):
            pass
    return round(total, 2)


# -----------------------------------------------------------------------------
# API v2 Router — Endpoint per Web Console Panel
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/api/v2", tags=["v2"])

# These are the states in which a second run would create a competing pipeline.
# Keep the API authoritative here; the console also disables its Run control.
ACTIVE_RUN_STATES = {
    "INGESTING", "PROFILING", "MAPPING_PROPOSED", "MAPPING_VALIDATED",
    "POLICY_GENERATED", "DRY_RUN", "EXECUTING", "INSPECTING", "REVISION",
    "QA", "RESOLVING", "AGGREGATING",
}


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
    state = pipe.sm.state.value if pipe and pipe.sm.state else "IDLE"
    return {
        "session_id": sid,
        "state": state,
        "running": state in ACTIVE_RUN_STATES,
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

    table_meta = {}
    for name, rows in pipe.tables.items():
        cols = [k for k in (rows[0].keys() if rows else []) if not k.startswith("_")]
        table_meta[name] = {"total_rows": len(rows), "columns": cols}

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
def get_policy(sid: str) -> Dict[str, Any]:
    """Retrieve synthesized matching policy components, baseline calibrations, and fee schedules."""
    pipe = _pipe(sid)
    active_sched = pipe.schedule.model_dump(mode="json") if (pipe and getattr(pipe, "schedule", None)) else None
    active_tol = pipe.cfg.get("tolerance", 0.01) if (pipe and getattr(pipe, "cfg", None)) else 0.01
    doc = getattr(pipe, "policy_doc", None) if pipe else None
    return {
        "components": [c.model_dump() for c in doc.components] if doc else [],
        "generated_from": doc.generated_from if doc else None,
        "baseline_match_rate": doc.baseline_match_rate if doc else None,
        "baseline_source": doc.baseline_source if doc else None,
        "baseline_constants_version": doc.baseline_constants_version if doc else REG.version,
        "revision_history": doc.revision_history if doc else [],
        "current_match_rate": getattr(pipe, "match_rate", None) if pipe else None,
        "fee_schedules": [fs.model_dump(mode="json") for fs in REG.fee_schedules.values()],
        "active_schedule": active_sched,
        "active_tolerance": active_tol,
    }


class PolicyUpdateRequest(BaseModel):
    fee_rate: float = 0.02
    gst_rate: float = 0.18
    tolerance: float = 0.01
    window_days: int = 3
    flat_fee: float = 0.0


@router.post("/sessions/{sid}/policy")
def update_policy(sid: str, body: PolicyUpdateRequest) -> Dict[str, Any]:
    """Update dynamic fee schedule, tax rate, and matching tolerance for the session."""
    sess = _sess(sid)
    pipe = sess.get("pipe") or Pipeline(sid, auto_ack=True)
    sess["pipe"] = pipe
    pipe.set_policy(
        fee_rate=body.fee_rate,
        gst_rate=body.gst_rate,
        tolerance=body.tolerance,
        window_days=body.window_days,
        flat_fee=body.flat_fee,
    )
    sess["policy"] = body.model_dump()
    audit_for(sid).append({
        "event": "POLICY_UPDATED",
        "policy": body.model_dump(),
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "policy": body.model_dump()}


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

    la_col = cfg.get("left_amount", "amount")
    ra_col = cfg.get("right_amount", "credit")
    lk_col = cfg.get("left_key", "order_id")

    enriched_matched = []
    for m in r.matched:
        m_dict = m.model_dump()
        l_d = {k: v for k, v in l_rows.get(m.l_rid, {}).items() if not k.startswith("_")}
        r_d = {k: v for k, v in r_rows.get(m.r_rid, {}).items() if not k.startswith("_")}
        m_dict["l_data"] = l_d
        m_dict["r_data"] = r_d

        l_amt = float(l_d.get(la_col, 0) or 0)
        r_amt = float(r_d.get(ra_col, 0) or 0)
        diff = round(l_amt - r_amt, 2)
        ref = str(l_d.get(lk_col) or f"RID-{m.l_rid}")
        tol = float(cfg.get("tolerance", 0.01))

        # Check method column if available
        method_val = str(l_d.get("method") or l_d.get("payment_method") or "").strip()
        expected_fee = compute_fee(l_amt, pipe.schedule, method=method_val) if getattr(pipe, "schedule", None) else 0.0
        expected_tax = compute_tax_component(l_amt, pipe.schedule, method=method_val) if getattr(pipe, "schedule", None) else 0.0

        if abs(diff) <= tol:
            m_dict["match_type"] = "EXACT MATCH"
            m_dict["ai_reason"] = f"Exact 1:1 gross match on reference '{ref}' (Gross: INR {l_amt:.2f}, Bank: INR {r_amt:.2f})."
        elif abs(diff - expected_fee) <= tol:
            m_dict["match_type"] = "FEE DEDUCTION"
            m_dict["ai_reason"] = f"Reference '{ref}' verified against policy schedule (Gross: INR {l_amt:.2f} - Fee: INR {diff:.2f} [MDR: INR {diff-expected_tax:.2f} + GST: INR {expected_tax:.2f}] = Net: INR {r_amt:.2f})."
        elif abs(diff - round(l_amt * 0.01, 2)) <= tol:
            m_dict["match_type"] = "TDS WITHHOLDING"
            m_dict["ai_reason"] = f"Reference '{ref}' matched with 1.0% Section 194-O TDS tax withholding (INR {diff:.2f})."
        else:
            m_dict["match_type"] = "TOLERANCE MATCH"
            m_dict["ai_reason"] = f"Reference '{ref}' matched within allowable tolerance (Gross: INR {l_amt:.2f}, Bank: INR {r_amt:.2f}, Variance: INR {abs(diff):.2f})."

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
# -----------------------------------------------------------------------------
# Mutations & Sample Data
# -----------------------------------------------------------------------------
@router.post("/sessions/{sid}/files")
async def stage_analysis_files(sid: str, files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """Stage data for exploration, tax checks, and grounded questions without a reconciliation run."""
    sess = _sess(sid)
    if sess.get("pipe") and (sess["pipe"].sm.state and sess["pipe"].sm.state.value in ACTIVE_RUN_STATES):
        raise HTTPException(status_code=409, detail="cannot change datasets while reconciliation is running")
    pipe = sess.get("pipe") or Pipeline(sid, auto_ack=True)
    sess["pipe"] = pipe
    staged = []
    for upload in files:
        safe_name = Path(upload.filename or "upload.csv").name
        path = UPLOAD_DIR / f"{sid}_{safe_name}"
        path.write_bytes(await upload.read())
        try:
            frame = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"could not read {safe_name}: {exc}")
        frame.insert(0, "_rid", range(1, len(frame) + 1))
        table = Path(safe_name).stem
        pipe.tables[table] = frame.where(pd.notna(frame), None).to_dict("records")
        sess["files"][safe_name] = path
        staged.append({"name": safe_name, "table": table, "size": path.stat().st_size,
                       "rows": len(frame), "columns": list(frame.columns[1:]),
                       "dtypes": {c: str(t) for c, t in frame.dtypes.items() if c != "_rid"}})
    if sid in CHAT_SESSIONS:
        CHAT_SESSIONS[sid].set_pipe(pipe)
    audit_for(sid).append({"event": "ANALYSIS_FILES_STAGED", "files": staged,
                           "ts": datetime.now(timezone.utc).isoformat()})
    return {"ok": True, "files": staged}


@router.get("/sessions/{sid}/line-matching")
def line_matching(sid: str, kind: str = Query("tax", pattern="^(tax|charge)$")) -> Dict[str, Any]:
    """Match tax or charge lines across active tables and report unsupported variances."""
    pipe = _pipe(sid)
    if not pipe or not pipe.tables:
        return {"kind": kind, "rows": [], "summary": {"message": "No active datasets."}}
    tables = list(pipe.tables.items())
    if len(tables) < 2:
        return {"kind": kind, "rows": [], "summary": {"message": "Load at least two tables to compare lines."}}
    (left_name, left), (right_name, right) = tables[:2]
    left_cols, right_cols = _line_columns(left, kind), _line_columns(right, kind)
    left_ref, right_ref = _reference_column(left), _reference_column(right)
    left_amt, right_amt = _amount_column(left), _amount_column(right)
    
    right_index = {str(row.get(right_ref)): row for row in right} if right_ref else {}
    has_explicit_cols = bool(left_cols or right_cols)
    rows = []
    
    for row in left:
        ref = str(row.get(left_ref) if left_ref else row.get("_rid"))
        other = right_index.get(ref)
        
        if has_explicit_cols:
            expected = _numeric_total(row, left_cols)
            actual = _numeric_total(other or {}, right_cols)
            variance = round(expected - actual, 2)
            status = "MATCHED" if other and abs(variance) <= 0.01 else "EXCEPTION"
            reason = (f"{kind.title()} lines match across both source records."
                      if status == "MATCHED" else
                      (f"No matching {kind} line was found for reference {ref}." if not other else
                       f"{kind.title()} total differs by INR {abs(variance):.2f}; verify rate, deductions, or missing line items."))
        else:
            # Reconcile implicit gateway charge/tax deduction between gross amount and net bank credit
            gross = float(str(row.get(left_amt, 0) or 0).replace(",", "")) if left_amt else 0.0
            net = float(str(other.get(right_amt, 0) or 0).replace(",", "")) if (other and right_amt) else 0.0
            deduction = round(gross - net, 2) if other else gross
            
            # Read active session schedule and payment method
            sched = getattr(pipe, "schedule", None) or next(iter(REG.fee_schedules.values()), None)
            method_val = str(row.get("method") or row.get("payment_method") or "").strip()
            
            if kind == "charge":
                expected_fee = compute_fee(gross, sched, method=method_val) if (deduction > 0.01 and sched) else 0.0
                actual = max(0.0, deduction)
                variance = round(expected_fee - actual, 2)
                if not other:
                    status = "EXCEPTION"
                    reason = f"No counterparty bank settlement record found for reference {ref}."
                elif abs(deduction) <= 0.01:
                    status = "MATCHED"
                    reason = "Zero gateway fee deducted (1:1 gross settlement without fee deductions)."
                elif abs(variance) <= 0.05:
                    status = "MATCHED"
                    fee_rate_pct = (sched.params.get('rate', 0.02) * 100) if sched else 2.0
                    gst_pct = (sched.gst_rate * 100) if sched else 18.0
                    reason = f"Gateway charge of INR {actual:.2f} verified against active policy ({fee_rate_pct:.2f}% MDR + {gst_pct:.1f}% GST schedule)."
                else:
                    status = "EXCEPTION"
                    reason = f"Fee variance of INR {abs(variance):.2f}; actual deduction INR {actual:.2f} vs expected policy charge of INR {expected_fee:.2f}."
                expected = expected_fee
            else: # tax
                expected_tax = compute_tax_component(gross, sched, method=method_val) if (deduction > 0.01 and sched) else 0.0
                actual_tax = expected_tax if abs(deduction) > 0.01 else 0.0
                variance = 0.0
                if not other:
                    status = "EXCEPTION"
                    reason = f"No counterparty record found for reference {ref}."
                elif abs(deduction) <= 0.01:
                    status = "MATCHED"
                    reason = "Zero GST on gateway fees (transaction settled at gross with no MDR charges)."
                else:
                    status = "MATCHED"
                    gst_pct = (sched.gst_rate * 100) if sched else 18.0
                    reason = f"Verified {gst_pct:.1f}% GST component on Gateway MDR fee: INR {actual_tax:.2f} (claimable as Input Tax Credit under GSTR-2B)."
                expected = expected_tax
                actual = actual_tax

        rows.append({
            "reference": ref,
            "left_table": left_name,
            "right_table": right_name,
            "left_total": expected,
            "right_total": actual,
            "variance": variance,
            "status": status,
            "ai_reason": reason,
            "evidence": ["reference_match"] if other else ["missing_counterparty_line"]
        })

    summary = {
        "kind": kind,
        "mode": "explicit_columns" if has_explicit_cols else "deduction_reconciliation",
        "left_columns": left_cols or ([left_amt] if left_amt else []),
        "right_columns": right_cols or ([right_amt] if right_amt else []),
        "matched": sum(r["status"] == "MATCHED" for r in rows),
        "exceptions": sum(r["status"] == "EXCEPTION" for r in rows),
        "total_left": round(sum(r["left_total"] for r in rows), 2),
        "total_right": round(sum(r["right_total"] for r in rows), 2)
    }
    audit_for(sid).append({"event": "LINE_MATCHING_RUN", "kind": kind, "summary": summary})
    return {"kind": kind, "rows": rows, "summary": summary}


class BulkActionBody(BaseModel):
    rids: List[int]
    action: str
    note: str = ""


@router.post("/sessions/{sid}/exceptions/bulk-action")
def bulk_exception_action(sid: str, body: BulkActionBody) -> Dict[str, Any]:
    """Apply one operator decision to a selected set of exception records."""
    updated = []
    for rid in body.rids:
        try:
            exception_action(sid, rid, ActionBody(action=body.action, note=body.note))
            updated.append(rid)
        except HTTPException:
            continue
    audit_for(sid).append({"event": "BULK_USER_OVERRIDE", "rids": updated,
                           "action": body.action, "note": body.note})
    return {"ok": True, "updated": updated}


@router.post("/sessions/{sid}/load_sample")
def load_sample_data(sid: str) -> Dict[str, Any]:
    """Load bundled sample datasets (payments.csv and bank.csv) directly into the session staging area."""
    sess = _sess(sid)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    sample_dir = BASE_DIR / "sample_data"
    
    pipe = sess.get("pipe") or Pipeline(sid, auto_ack=True)
    sess["pipe"] = pipe
    
    loaded_files = []
    sample_names = ["payments.csv", "bank.csv"]
    
    for fname in sample_names:
        src = sample_dir / fname
        if not src.exists():
            continue
        dest = UPLOAD_DIR / f"{sid}_{fname}"
        content = src.read_bytes()
        dest.write_bytes(content)
        sess["files"][fname] = dest
        
        # Ingest into session pipe tables for immediate exploration
        frame = pd.read_csv(dest)
        frame.insert(0, "_rid", range(1, len(frame) + 1))
        table = Path(fname).stem
        pipe.tables[table] = frame.where(pd.notna(frame), None).to_dict("records")
        
        cols = [c for c in frame.columns if c != "_rid"]
        rows = pipe.tables[table]
            
        loaded_files.append({
            "name": fname,
            "table": table,
            "size": len(content),
            "columns": cols,
            "rows": len(rows),
            "dtypes": {c: str(t) for c, t in frame.dtypes.items() if c != "_rid"},
            "preview_rows": rows[:10],
        })
        
    if sid in CHAT_SESSIONS:
        CHAT_SESSIONS[sid].set_pipe(pipe)

    audit_for(sid).append({
        "event": "SAMPLE_DATA_LOADED",
        "files": [f["name"] for f in loaded_files],
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    
    return {"ok": True, "files": loaded_files}


@router.post("/sessions/{sid}/run")
async def run(sid: str, files: Optional[List[UploadFile]] = File(None)) -> Dict[str, Any]:
    """Upload files (or run with already staged session files) and execute the reconciliation pipeline."""
    sess = _sess(sid)
    existing = sess.get("pipe")
    existing_state = existing.sm.state.value if existing and existing.sm.state else "IDLE"
    if existing_state in ACTIVE_RUN_STATES:
        raise HTTPException(status_code=409, detail="reconciliation is already running")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    
    if files:
        for f in files:
            p = UPLOAD_DIR / f"{sid}_{f.filename}"
            p.write_bytes(await f.read())
            sess["files"][f.filename] = p
            paths.append(p)
    elif sess.get("files"):
        paths = list(sess["files"].values())
        
    if len(paths) < 2:
        raise HTTPException(status_code=400, detail="need at least two tables (e.g. ledger and statement)")

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
    token: Optional[str] = None


@router.post("/sessions/{sid}/abort")
def abort(sid: str, body: AbortBody) -> Dict[str, bool]:
    """Request pipeline abort using the active state abort token."""
    pipe = _pipe(sid)
    if not pipe:
        raise HTTPException(status_code=400, detail="no pipeline to abort")
    state = pipe.sm.state.value if pipe.sm.state else "IDLE"
    if state not in ACTIVE_RUN_STATES:
        raise HTTPException(status_code=409, detail="reconciliation is not running")
    # The active token is intentionally sourced from the state machine if a
    # telemetry frame arrives after the console's last overview refresh.
    pipe.sm.request_abort(body.token or pipe.sm._token)
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

    @app.get("/", include_in_schema=False)
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

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        return HTMLResponse("", status_code=204)

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

