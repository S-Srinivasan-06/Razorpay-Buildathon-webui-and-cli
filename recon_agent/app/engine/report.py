from app.core.constants import REG
from app.core.contracts import FinalReport
from app.core.cost import tracker_for


def build_final_report(sid, *, match_rate, precision_vs_truth, recall_vs_truth,
                       throughput_rows_per_sec, exceptions, elapsed_seconds,
                       totals, llm_user_disagreements, fallback_events) -> FinalReport:
    tracker = tracker_for(sid)
    return FinalReport(
        match_rate=match_rate,
        precision_vs_truth=precision_vs_truth,
        recall_vs_truth=recall_vs_truth,
        throughput_rows_per_sec=throughput_rows_per_sec,
        honest_exception_count=len(exceptions),
        auto_resolved_count=sum(1 for e in exceptions if e.get("action") in ("auto_resolve", "mark_resolved")),
        escalated_count=sum(1 for e in exceptions if e.get("action") in ("request_confirmation", "escalate")),
        unresolved_count=sum(1 for e in exceptions if e.get("action") == "mark_pending"),
        total_gross=totals["gross"], total_net=totals["net"], total_fees=totals["fees"],
        matched_value=totals["matched_value"], exception_value=totals["exception_value"],
        cost_usd=round(tracker.total, 6),
        cost_estimated=tracker.estimated_any,
        elapsed_seconds=elapsed_seconds,
        llm_user_disagreements=llm_user_disagreements,
        fallback_events=fallback_events,
        constants_version=REG.version,
        retention_note="intermediates 90d; final report + audit retained indefinitely",
    )
