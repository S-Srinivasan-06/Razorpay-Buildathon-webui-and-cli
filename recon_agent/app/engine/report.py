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
            1 for e in exceptions if e.get("action") == "mark_pending"
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

