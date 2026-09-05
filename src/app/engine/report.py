"""Final Reconciliation Report Synthesis.

Aggregates execution metrics, precision/recall benchmark evaluations, financial
volume totals (gross, net, fees, matched, exception), metered LLM costs, and
classified exception counts into a canonical FinalReport contract model.
"""

from typing import Any, Dict, List, Optional

from app.core.constants import REG
from app.core.contracts import FinalReport
from app.core.cost import tracker_for


def build_final_report(
    sid: str,
    *,
    match_rate: float,
    precision_vs_truth: Optional[float],
    recall_vs_truth: Optional[float],
    throughput_rows_per_sec: float,
    exceptions: List[Dict[str, Any]],
    elapsed_seconds: float,
    totals: Dict[str, float],
    llm_user_disagreements: List[Dict[str, Any]],
    fallback_events: List[str],
) -> FinalReport:
    """Construct the immutable FinalReport model for a completed reconciliation session.
    
    Args:
        sid: Unique session identifier string.
        match_rate: Fraction of left ledger records matched (0.0 to 1.0).
        precision_vs_truth: Precision score evaluated against ground truth, if provided.
        recall_vs_truth: Recall score evaluated against ground truth, if provided.
        throughput_rows_per_sec: Processing throughput in total records per second.
        exceptions: Complete list of classified exception item dictionaries from the queue.
        elapsed_seconds: Total pipeline wall-clock execution duration in seconds.
        totals: Dictionary containing financial sums ('gross', 'net', 'fees', 'matched_value', 'exception_value').
        llm_user_disagreements: History of operator overrides deviating from system proposals.
        fallback_events: List of triggered deterministic fallback event names.
        
    Returns:
        Structured FinalReport instance.
    """
    tracker = tracker_for(sid)

    return FinalReport(
        match_rate=match_rate,
        precision_vs_truth=precision_vs_truth,
        recall_vs_truth=recall_vs_truth,
        throughput_rows_per_sec=throughput_rows_per_sec,
        honest_exception_count=len(exceptions),
        auto_resolved_count=sum(
            1 for e in exceptions if e.get("action") in ("auto_resolve", "mark_resolved")
        ),
        escalated_count=sum(
            1 for e in exceptions if e.get("action") in ("request_confirmation", "escalate")
        ),
        unresolved_count=sum(
            1 for e in exceptions if e.get("action") in ("mark_pending", "declined")
        ),
        total_gross=totals["gross"],
        total_net=totals["net"],
        total_fees=totals["fees"],
        matched_value=totals["matched_value"],
        exception_value=totals["exception_value"],
        cost_usd=round(tracker.total, 6),
        cost_estimated=tracker.estimated_any,
        elapsed_seconds=elapsed_seconds,
        llm_user_disagreements=llm_user_disagreements,
        fallback_events=fallback_events,
        constants_version=REG.version,
        retention_note="intermediates 90d; final report + audit retained indefinitely",
    )


def export_reconciliation_csv_string(pipe: Any) -> str:
    """Generate canonical CSV string containing matched pairs and classified exceptions with every attribute."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    cfg = getattr(pipe, "cfg", {}) or {}
    l_table_name = cfg.get("left_table", "payments")
    r_table_name = cfg.get("right_table", "bank")
    l_rows_list = pipe.tables.get(l_table_name, []) if getattr(pipe, "tables", None) else []
    r_rows_list = pipe.tables.get(r_table_name, []) if getattr(pipe, "tables", None) else []

    l_by_rid = {row["_rid"]: row for row in l_rows_list if isinstance(row, dict) and "_rid" in row}
    r_by_rid = {row["_rid"]: row for row in r_rows_list if isinstance(row, dict) and "_rid" in row}

    # Extract all non-private attribute columns from left and right tables
    l_cols = []
    for r in l_rows_list:
        if isinstance(r, dict):
            for k in r.keys():
                if not k.startswith("_") and k not in l_cols:
                    l_cols.append(k)

    r_cols = []
    for r in r_rows_list:
        if isinstance(r, dict):
            for k in r.keys():
                if not k.startswith("_") and k not in r_cols:
                    r_cols.append(k)

    # Prefix columns to avoid collisions between identical column names in both tables
    l_prefix = f"{l_table_name}_" if l_table_name else "left_"
    r_prefix = f"{r_table_name}_" if r_table_name and r_table_name != l_table_name else "right_"

    header = [
        "record_type",
        "status",
        "reference",
        "side",
        "variance",
        "composite_score_or_confidence",
        "match_type_or_reason",
        "action",
        "ai_diagnostic",
        "l_rid",
        "r_rid",
    ] + [f"{l_prefix}{c}" for c in l_cols] + [f"{r_prefix}{c}" for c in r_cols]

    writer.writerow(header)

    la_col = cfg.get("left_amount", "amount")
    ra_col = cfg.get("right_amount", "credit")
    lk_col = cfg.get("left_key", "order_id")
    rk_col = cfg.get("right_key", "utr")

    if getattr(pipe, "exec_res", None) and getattr(pipe.exec_res, "matched", None):
        for m in pipe.exec_res.matched:
            l_row = getattr(m, "l_data", None) or l_by_rid.get(m.l_rid, {})
            r_row = getattr(m, "r_data", None) or r_by_rid.get(m.r_rid, {})
            if not l_row and 0 < m.l_rid <= len(l_rows_list):
                l_row = l_rows_list[m.l_rid - 1]
            if not r_row and 0 < m.r_rid <= len(r_rows_list):
                r_row = r_rows_list[m.r_rid - 1]

            ref = getattr(m, "ref", None) or l_row.get(lk_col) or r_row.get(rk_col) or f"RID-{m.l_rid}"
            l_amt = l_row.get(la_col)
            r_amt = r_row.get(ra_col)
            try:
                variance = round(float(l_amt) - float(r_amt), 2) if l_amt is not None and r_amt is not None else ""
            except (ValueError, TypeError):
                variance = ""

            score = round(m.composite_score, 4) if getattr(m, "composite_score", None) is not None else 1.0
            match_type = getattr(m, "match_type", "EXACT MATCH")
            ai_diag = getattr(m, "ai_reason", f"Matched record pair: {ref}")

            row = [
                "matched",
                "MATCHED",
                ref,
                "BOTH",
                variance,
                score,
                match_type,
                "reconciled",
                ai_diag,
                m.l_rid,
                m.r_rid,
            ]
            for c in l_cols:
                row.append(l_row.get(c, ""))
            for c in r_cols:
                row.append(r_row.get(c, ""))
            writer.writerow(row)

    if getattr(pipe, "queue", None):
        for item in pipe.queue:
            rec = item["rec"]
            side = rec.side
            action = item.get("action", "mark_pending")
            status = "RESOLVED" if action in ("auto_resolve", "mark_resolved") else ("DECLINED" if action == "declined" else "DISCREPANCY")
            ref = rec.ref or (f"RID-{rec.rid}" if rec.rid else "")
            variance = rec.delta if rec.delta is not None else ""
            conf = round(item.get("conf", 0.0), 3)
            reason = rec.reason.value if hasattr(rec.reason, "value") else str(rec.reason)
            diag = (item.get("explanation") or getattr(rec, "explanation", "") or "").replace("\n", " ")

            l_rid_val = rec.rid if side == "L" else ""
            r_rid_val = rec.rid if side == "R" else ""

            # Extract source row attributes
            src_row = item.get("record_data") or (l_by_rid.get(rec.rid, {}) if side == "L" else r_by_rid.get(rec.rid, {}))
            if not src_row:
                if side == "L" and 0 < rec.rid <= len(l_rows_list):
                    src_row = l_rows_list[rec.rid - 1]
                elif side == "R" and 0 < rec.rid <= len(r_rows_list):
                    src_row = r_rows_list[rec.rid - 1]
                else:
                    src_row = {}

            row = [
                "exception",
                status,
                ref,
                side,
                variance,
                conf,
                reason,
                action,
                diag,
                l_rid_val,
                r_rid_val,
            ]
            for c in l_cols:
                row.append(src_row.get(c, "") if side == "L" else "")
            for c in r_cols:
                row.append(src_row.get(c, "") if side == "R" else "")
            writer.writerow(row)

    return output.getvalue()

