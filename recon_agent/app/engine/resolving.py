from typing import Optional
from app.core.constants import REG
from app.core.contracts import HypothesisCategory, HYPOTHESIS_PRIORITY

_MAX_RANK = max(HYPOTHESIS_PRIORITY.values())


def category_confidence(category: HypothesisCategory) -> float:
    p = HYPOTHESIS_PRIORITY.get(category, _MAX_RANK)
    return round(1.0 - (p - 1) / (_MAX_RANK - 1), 3)


def exception_confidence(evidence_count: int, category: HypothesisCategory, sem: Optional[float] = None) -> float:
    # High confidence for verified business patterns with evidence
    if category in (HypothesisCategory.TEMPORAL_DRIFT, HypothesisCategory.SPLIT, HypothesisCategory.FEE_DEDUCTION):
        base = 0.88 + 0.04 * min(evidence_count, 2)
        return min(round(base, 3), 0.98)
    
    # Well-categorized anomalies
    if category in (HypothesisCategory.DUPLICATE, HypothesisCategory.REFUND_OFFSET):
        return round(0.85, 3)
    
    # Missing / unclassified items require human escalation
    return (min(evidence_count / 4, 1.0) * REG["w_exception_evidence"]
            + category_confidence(category) * REG["w_exception_category"]
            + (sem or 0.0) * REG["w_exception_semantic"])


def decide_action(conf: float, evidence_count: int, category: Optional[HypothesisCategory] = None) -> str:
    # Non-error business variations that should be automatically approved
    if category in (HypothesisCategory.TEMPORAL_DRIFT, HypothesisCategory.SPLIT, HypothesisCategory.FEE_DEDUCTION):
        return "auto_resolve"

    # Strict errors / anomalies that require human escalation
    if category in (HypothesisCategory.DUPLICATE, HypothesisCategory.REFUND_OFFSET, HypothesisCategory.UNCLASSIFIED, HypothesisCategory.COUNTERPARTY_MISMATCH):
        return "request_confirmation"

    if (conf >= REG["exception_auto_resolve_confidence"]
            and evidence_count >= REG["exception_auto_resolve_evidence_min"]):
        return "auto_resolve"
    if 0.40 <= conf < 0.85:
        return "request_confirmation"
    return "mark_pending"


def generate_explanation(rec, ctx: dict, row_data: Optional[dict] = None) -> str:
    cat = rec.reason
    side = rec.side
    ref = rec.ref or "N/A"

    if cat == HypothesisCategory.TEMPORAL_DRIFT:
        return f"Approved [No Error]: Exact amount & reference '{ref}' matched; settlement deferred by bank holiday/clearing window."
    elif cat == HypothesisCategory.SPLIT:
        targets = ctx.get("split_targets", [])
        return f"Approved [No Error]: Batch settlement combines multiple order legs (RIDs {targets}) net of payment gateway fees."
    elif cat == HypothesisCategory.FEE_DEDUCTION:
        return f"Approved [No Error]: Net bank deposit variance matches standard payment gateway fee schedule."
    elif cat == HypothesisCategory.DUPLICATE:
        return f"Error in Source A (Ledger): Duplicate order reference '{ref}' recorded multiple times in payments ledger."
    elif cat == HypothesisCategory.REFUND_OFFSET:
        return f"Anomaly in Source B (Bank): Negative credit entry (-₹{abs(rec.delta or 0):.2f}) representing customer refund or chargeback."
    elif cat == HypothesisCategory.COUNTERPARTY_MISMATCH:
        return f"Error: Counterparty identifier mismatch between payment order reference '{ref}' and bank settlement UTR."
    elif side == "L":
        return f"Error in Source B (Bank): Order '{ref}' exists in payments ledger but has no corresponding bank settlement credit."
    elif side == "R":
        return f"Error in Source A (Ledger): Unmatched bank credit for UTR '{ref}' without corresponding order in payments ledger."
    else:
        return f"Unclassified discrepancy for reference '{ref}'."
