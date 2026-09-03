"""Unified, Audited Agent Action Dispatcher.

Provides a single authoritative execution gateway for all state-changing actions
triggered either via conversational AI chat or REST API endpoints.
"""

from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional
import uuid

from app.core.audit import audit_for
from app.core.channels import validate_and_route
from app.core.contracts import FeeTaxRule, MessageKind
from app.core.states import State
from app.engine.fee import compute_deduction_breakdown

ACTIVE_RUN_STATES = {
    "INGESTING",
    "PROFILING",
    "MAPPING_PROPOSED",
    "MAPPING_VALIDATED",
    "POLICY_GENERATED",
    "DRY_RUN",
    "EXECUTING",
    "INSPECTING",
    "REVISION",
    "QA",
    "RESOLVING",
    "AGGREGATING",
}


_ACTION_LOCK = threading.Lock()


def execute_agent_action(
    sid: str,
    pipe: Any,
    action_kind: str,
    payload: Dict[str, Any],
    source: str = "chat",
) -> Dict[str, Any]:
    """Execute a validated pipeline action with mandatory audit logging and event dispatch.
    
    Args:
        sid: Session identifier.
        pipe: Pipeline instance.
        action_kind: Standardized action name (e.g. RUN_RECONCILIATION, SET_TOLERANCE).
        payload: Parameter dictionary.
        source: Trigger origin ('chat', 'rest', 'ui', 'confirmation').
        
    Returns:
        Action execution result dictionary.
    """
    if not pipe:
        from app.pipeline import Pipeline
        pipe = Pipeline(sid, auto_ack=True)

    try:
        from app.server.api_v2 import V2_SESSIONS
        if sid in V2_SESSIONS:
            V2_SESSIONS[sid]["pipe"] = pipe
    except Exception:
        pass

    action_kind = action_kind.upper().strip()
    ts = datetime.now(timezone.utc).isoformat()
    result_data: Dict[str, Any] = {}

    if action_kind == "RUN_RECONCILIATION":
        with _ACTION_LOCK:
            if not getattr(pipe, "tables", None) or len(pipe.tables) < 2:
                raise ValueError(
                    "I don't have two datasets to reconcile yet — please upload files or run Load Sample Data first."
                )
            state_val = pipe.sm.state.value if pipe.sm.state else "IDLE"
            if state_val in ACTIVE_RUN_STATES:
                raise ValueError("Reconciliation pipeline is already running.")

            # If previous run completed or was aborted, construct a fresh Pipeline
            # (mirrors what the REST /run endpoint does) so stale state doesn't bleed through.
            if state_val in ("ARCHIVED", "ABORT_CONFIRMED"):
                from app.pipeline import Pipeline
                old_pipe = pipe
                pipe = Pipeline(sid, auto_ack=True)
                pipe.tables = dict(old_pipe.tables)
                pipe.rules = list(getattr(old_pipe, "rules", []))
                pipe.schedule = getattr(old_pipe, "schedule", None)
                pipe.cfg.update({
                    k: v for k, v in old_pipe.cfg.items()
                    if k in ("tolerance", "tolerance_abs", "tolerance_pct",
                             "tolerance_mode", "window_days",
                             "left_table", "right_table", "left_key", "right_key",
                             "left_amount", "right_amount", "left_date", "right_date")
                })
                # Update session registries so both REST and chat use the new pipe
                try:
                    from app.server.api_v2 import V2_SESSIONS, CHAT_SESSIONS
                    if sid in V2_SESSIONS:
                        V2_SESSIONS[sid]["pipe"] = pipe
                    if sid in CHAT_SESSIONS:
                        CHAT_SESSIONS[sid].set_pipe(pipe)
                except Exception:
                    pass

            # Synchronously transition to INGESTING to guard against race condition
            pipe.sm.enter(State.INGESTING)

            def _work():
                try:
                    pipe.run([])
                except Exception as e:
                    import traceback
                    traceback.print_exc()

            threading.Thread(target=_work, daemon=True).start()
            result_data = {"status": "started", "state": pipe.sm.state.value}

    elif action_kind == "SET_POLICY":
        fee_rate = float(payload.get("fee_rate", payload.get("fee", 0.0)))
        gst_rate = float(payload.get("gst_rate", payload.get("gst", 0.0)))
        tolerance = float(payload.get("tolerance", payload.get("tol", 0.01)))
        window_days = int(payload.get("window_days", 3))
        flat_fee = float(payload.get("flat_fee", 0.0))
        pipe.set_policy(
            fee_rate=fee_rate,
            gst_rate=gst_rate,
            tolerance=tolerance,
            window_days=window_days,
            flat_fee=flat_fee,
        )
        result_data = {
            "fee_rate": fee_rate,
            "gst_rate": gst_rate,
            "tolerance": tolerance,
            "window_days": window_days,
            "flat_fee": flat_fee,
        }

    elif action_kind == "SET_TOLERANCE":
        abs_tol = float(payload.get("abs_tol", payload.get("abs", 0.01)))
        pct_tol = float(payload.get("pct_tol", payload.get("pct", 0.0)))
        mode = str(payload.get("mode", "absolute_only"))
        pipe.set_tolerance(abs_tol=abs_tol, pct_tol=pct_tol, mode=mode)
        result_data = {"abs_tol": abs_tol, "pct_tol": pct_tol, "mode": mode}

    elif action_kind == "ADD_RULES":
        raw_rules = payload.get("rules", [])
        added_rules = []
        for rd in raw_rules:
            rule = rd if isinstance(rd, FeeTaxRule) else FeeTaxRule.model_validate(rd)
            pipe.add_rule(rule)
            added_rules.append(rule.model_dump(mode="json"))
        result_data = {"added_count": len(added_rules), "rules": added_rules}

    elif action_kind == "SET_RULES":
        raw_rules = payload.get("rules", [])
        new_rules = [
            rd if isinstance(rd, FeeTaxRule) else FeeTaxRule.model_validate(rd)
            for rd in raw_rules
        ]
        pipe.set_rules(new_rules)
        result_data = {"total_rules": len(new_rules), "rules": [r.model_dump(mode="json") for r in new_rules]}

    elif action_kind == "CLEAR_RULES":
        pipe.set_rules([])
        result_data = {"cleared": True, "total_rules": 0}

    elif action_kind in ("VERIFY_TAX", "VERIFY_CHARGES"):
        kind = "tax" if action_kind == "VERIFY_TAX" else "charge"
        tables = list(pipe.tables.items()) if getattr(pipe, "tables", None) else []
        if len(tables) < 2:
            result_data = {"error": "Need at least 2 tables to verify."}
        else:
            left_rows = tables[0][1]
            right_rows = tables[1][1]
            total_eval = min(len(left_rows), 50)
            verified_count = 0
            for idx in range(total_eval):
                l_row = left_rows[idx]
                amt = float(l_row.get(pipe.cfg.get("left_amount", "amount"), 0) or 0)
                brk = compute_deduction_breakdown(
                    amt,
                    rules=pipe.rules,
                    row=l_row,
                    total_rows=len(left_rows),
                    row_idx=idx,
                )
                if kind == "tax" and (brk["gst"] > 0 or brk["tds"] > 0):
                    verified_count += 1
                elif kind == "charge" and brk["gateway_fee"] > 0:
                    verified_count += 1
            result_data = {"kind": kind, "evaluated": total_eval, "applicable_count": verified_count}

    else:
        raise ValueError(f"Unsupported action kind: '{action_kind}'")

    # 1. Cryptographic audit trail entry logged unconditionally before returning
    audit_for(sid).append({
        "event": f"{action_kind}_APPLIED",
        "source": source,
        "payload": payload,
        "result": result_data,
        "ts": ts,
    })

    # 2. Synchronize frontend subscribers via WebSocket bus
    validate_and_route(
        sid,
        MessageKind.CONTROL,
        {
            "event": f"{action_kind}_APPLIED",
            "source": source,
            "detail": result_data,
        },
        "system",
    )

    return {
        "ok": True,
        "action": action_kind,
        "source": source,
        "result": result_data,
        "ts": ts,
    }
