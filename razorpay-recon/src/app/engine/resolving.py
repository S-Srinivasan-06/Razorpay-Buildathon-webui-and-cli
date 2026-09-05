"""Exception Resolution Logic and Diagnostic Explanation Generation.

Calculates confidence scores for classified discrepancy hypotheses, determines
automated action policies (auto_resolve vs request_confirmation vs mark_pending),
and generates audit-ready root-cause explanations for every unmatched record.
"""

from typing import Any, Dict, Optional

from app.core.constants import REG
from app.core.contracts import HYPOTHESIS_PRIORITY, HypothesisCategory, UnmatchedRecord

_MAX_RANK = max(HYPOTHESIS_PRIORITY.values())


def category_confidence(category: HypothesisCategory) -> float:
    """Calculate base normalized confidence score from the hypothesis priority taxonomy.
    
    Args:
        category: Classified HypothesisCategory.
        
    Returns:
        Confidence score between 0.0 and 1.0 based on taxonomy ranking.
    """
    p = HYPOTHESIS_PRIORITY.get(category, _MAX_RANK)
    return round(1.0 - (p - 1) / (_MAX_RANK - 1), 3)


def exception_confidence(
    evidence_count: int,
    category: HypothesisCategory,
    sem: Optional[float] = None,
) -> float:
    """Compute overall confidence for an exception hypothesis.
    
    Applies high confidence (0.88 - 0.98) for verified operational patterns with
    corroborating evidence (Temporal Drift, Split settlements, Fee Deductions, Token matches).
    Applies baseline confidence (0.85) for confirmed anomalies (Duplicates, Refund Offsets).
    Uses weighted multi-signal scoring for unclassified items.
    
    Args:
        evidence_count: Number of verified EvidencePiece pieces attached to the record.
        category: Classified HypothesisCategory.
        sem: Optional semantic similarity score.
        
    Returns:
        Composite confidence score in [0.0, 1.0].
    """
    # High confidence for verified business patterns supported by evidence
    if category in (
        HypothesisCategory.TEMPORAL_DRIFT,
        HypothesisCategory.SPLIT,
        HypothesisCategory.FEE_DEDUCTION,
        HypothesisCategory.COUNTERPARTY_MISMATCH,
    ):
        base = 0.88 + 0.04 * min(evidence_count, 2)
        return min(round(base, 3), 0.98)

    # Well-categorized anomalies requiring confirmation
    if category in (
        HypothesisCategory.DUPLICATE,
        HypothesisCategory.REFUND_OFFSET,
        HypothesisCategory.VALUE_ERROR,
        HypothesisCategory.MISSING,
    ):
        return round(0.85, 3)

    # Weighted scoring for unclassified or partially matched discrepancies
    return (
        min(evidence_count / 4, 1.0) * REG["w_exception_evidence"]
        + category_confidence(category) * REG["w_exception_category"]
        + (sem or 0.0) * REG["w_exception_semantic"]
    )


def decide_action(
    conf: float,
    evidence_count: int,
    category: Optional[HypothesisCategory] = None,
    ctx: Optional[Dict[str, Any]] = None,
) -> str:
    """Determine the automated action policy for an exception item based on strict governance gates.
    
    Actions:
      - 'auto_resolve': Legitimate business variation (e.g. gateway fees, timing drift)
                        that meets governance confidence (>= 0.85) and evidence (>= 2 pieces).
      - 'request_confirmation': Discrepancy or anomaly requiring operator review.
      - 'mark_pending': Low-confidence unclassified discrepancy awaiting manual investigation.
    """
    min_conf = float(REG["exception_auto_resolve_confidence"])
    min_ev = int(REG["exception_auto_resolve_evidence_min"])

    # Anomaly categories that ALWAYS require operator confirmation
    if category in (
        HypothesisCategory.DUPLICATE,
        HypothesisCategory.REFUND_OFFSET,
        HypothesisCategory.VALUE_ERROR,
        HypothesisCategory.MISSING,
        HypothesisCategory.UNCLASSIFIED,
    ):
        return "request_confirmation"

    # Ambiguous splits ALWAYS require operator confirmation
    if category == HypothesisCategory.SPLIT and ctx and ctx.get("ambiguous_split"):
        return "request_confirmation"

    # Business variations qualify for auto_resolve ONLY if they satisfy governance thresholds
    if category in (
        HypothesisCategory.TEMPORAL_DRIFT,
        HypothesisCategory.SPLIT,
        HypothesisCategory.FEE_DEDUCTION,
        HypothesisCategory.TAX_WITHHOLDING,
        HypothesisCategory.COUNTERPARTY_MISMATCH,
    ):
        if conf >= min_conf and evidence_count >= min_ev:
            return "auto_resolve"
        return "request_confirmation"

    # Threshold-based fallback policy evaluation
    if conf >= min_conf and evidence_count >= min_ev:
        return "auto_resolve"
    if conf >= 0.40:
        return "request_confirmation"
    return "mark_pending"


def generate_explanation(
    rec: UnmatchedRecord,
    ctx: Dict[str, Any],
    row_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a clear, human-readable root-cause diagnostic explanation for a record.
    
    Args:
        rec: UnmatchedRecord containing side, reference, delta, and classified reason.
        ctx: Context dictionary with candidate links, batch refs, and duplicate IDs.
        row_data: Optional raw row attributes from the source file.
        
        
    Returns:
        Formatted diagnostic explanation string.
    """
    cat = rec.reason
    side = rec.side
    ref = rec.ref or "N/A"

    rule_tag = f" [Rule: '{ctx['rule_label']}']" if ctx.get("rule_label") else ""
    tol_tag = f" [Tolerance: {ctx['tolerance_str']}]" if ctx.get("tolerance_str") else ""

    if cat == HypothesisCategory.TEMPORAL_DRIFT:
        return (
            f"Approved [No Error]: Exact amount & reference '{ref}' matched; "
            f"settlement deferred by bank holiday/clearing window.{tol_tag}"
        )
    elif cat == HypothesisCategory.SPLIT:
        if ctx.get("ambiguous_split"):
            return (
                f"Requires Review [Ambiguous Match]: Multiple valid combinations of order legs sum exactly to the "
                f"batch deposit '{ctx.get('split_batch_ref', 'N/A')}'. Operator must manually confirm the correct set."
            )
        if side == "L":
            batch_ref = ctx.get("split_batch_ref", "bank batch settlement")
            return (
                f"Approved [No Error]: Constituent transaction leg resolved as part of "
                f"batch deposit '{batch_ref}' net of gateway deductions.{rule_tag}{tol_tag}"
            )
        targets = ctx.get("split_targets", [])
        return (
            f"Approved [No Error]: Batch settlement combines multiple order legs "
            f"(RIDs {targets}) net of payment gateway deductions.{rule_tag}{tol_tag}"
        )
    elif cat == HypothesisCategory.FEE_DEDUCTION:
        return f"Approved [No Error]: Net bank deposit variance matches payment gateway fee policy.{rule_tag}{tol_tag}"
    elif cat == HypothesisCategory.TAX_WITHHOLDING:
        return f"Approved [No Error]: Variance matches configured tax withholding / GST deduction policy.{rule_tag}{tol_tag}"
    elif cat == HypothesisCategory.CURRENCY_CONVERSION:
        return f"Approved [No Error]: Variance explained by expected FX/currency conversion spread corridor.{tol_tag}"
    elif cat == HypothesisCategory.DUPLICATE:
        return f"Error in Source A (Ledger): Duplicate order reference '{ref}' recorded multiple times in payments ledger."
    elif cat == HypothesisCategory.REFUND_OFFSET:
        return (
            f"Anomaly in Source B (Bank): Negative credit entry (-₹{abs(rec.delta or 0):.2f}) "
            "representing customer refund or chargeback."
        )
    elif cat == HypothesisCategory.COUNTERPARTY_MISMATCH:
        return f"Approved [No Error]: Normalized token/semantic match verified between order '{ref}' and counterpart UTR.{tol_tag}"
    elif cat in (HypothesisCategory.VALUE_ERROR, HypothesisCategory.AMOUNT_DELTA):
        return (
            f"Value Discrepancy Error: Amount delta of ₹{abs(rec.delta or 0):.2f} detected "
            f"between supply dispatch order '{ref}' and bank settlement credit.{tol_tag}"
        )
    elif cat == HypothesisCategory.MISSING:
        if side == "L":
            return f"Missing Bank Settlement: Banana supply order '{ref}' dispatched but missing corresponding credit in bank statement."
        else:
            return f"Missing Supply Order: Bank credit for UTR '{ref}' received but missing corresponding dispatch order in payments ledger."
    elif side == "L":
        return f"Error in Source B (Bank): Order '{ref}' exists in payments ledger but has no corresponding bank settlement credit."
    elif side == "R":
        return f"Error in Source A (Ledger): Unmatched bank credit for UTR '{ref}' without corresponding order in payments ledger."
    else:
        return f"Unclassified discrepancy for reference '{ref}'."

