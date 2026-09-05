"""Discrepancy Quality Assurance and Predicate Classification Engine.

Applies prioritized deterministic predicates over record attributes and candidate
contexts to classify discrepancies into precise root-cause categories (Duplicate, Split,
Temporal Drift, Fee Deduction, Refund Offset, Counterparty Mismatch, Amount Delta).
"""

from typing import Any, Callable, Dict, List

from app.core.contracts import HYPOTHESIS_PRIORITY, HypothesisCategory as H, UnmatchedRecord

# Standard context keys populated during candidate extraction
CTX_KEYS: List[str] = [
    "dup_rids",
    "split_targets",
    "single_target",
    "partial",
    "fee_match",
    "tax_match",
    "fx_match",
    "fuzzy_key",
    "negative_credit",
    "date_only_mismatch",
]

# Predicate functions mapped to each discrepancy category
_PREDICATES: Dict[H, Callable[[UnmatchedRecord, Dict[str, Any]], bool]] = {
    H.DUPLICATE: lambda rec, ctx: bool(ctx.get("dup_rids")),
    H.SPLIT: lambda rec, ctx: bool(ctx.get("split_targets")),
    H.PARTIAL_PAYMENT: lambda rec, ctx: (
        rec.delta is not None
        and rec.delta > 0.01
        and ctx.get("single_target")
        and ctx.get("partial")
    ),
    H.REFUND_OFFSET: lambda rec, ctx: (
        bool(ctx.get("negative_credit"))
        or (rec.delta is not None and rec.delta < -0.01)
    ),
    H.FEE_DEDUCTION: lambda rec, ctx: bool(ctx.get("fee_match")),
    H.TAX_WITHHOLDING: lambda rec, ctx: bool(ctx.get("tax_match")),
    H.CURRENCY_CONVERSION: lambda rec, ctx: bool(ctx.get("fx_match")),
    H.TEMPORAL_DRIFT: lambda rec, ctx: bool(ctx.get("date_only_mismatch")),
    H.COUNTERPARTY_MISMATCH: lambda rec, ctx: bool(ctx.get("fuzzy_key")),
    H.VALUE_ERROR: lambda rec, ctx: (
        rec.delta is not None and abs(rec.delta) > 0.01
    ),
    H.AMOUNT_DELTA: lambda rec, ctx: (
        rec.delta is not None and abs(rec.delta) > 0.01
    ),
    H.MISSING: lambda rec, ctx: (
        rec.delta is None and not bool(ctx.get("dup_rids")) and not bool(ctx.get("split_targets"))
    ),
    H.UNCLASSIFIED: lambda rec, ctx: True,
}

# Ordered list of hypothesis categories sorted by business precedence
_ORDERED: List[H] = sorted(HYPOTHESIS_PRIORITY, key=HYPOTHESIS_PRIORITY.get)


def classify(rec: UnmatchedRecord, ctx: Dict[str, Any]) -> H:
    """Classify an unmatched record into the highest-priority matching hypothesis category.
    
    Iterates through hypothesis predicates in precedence order (e.g. DUPLICATE before SPLIT,
    SPLIT before TEMPORAL_DRIFT, etc.).
    
    Args:
        rec: UnmatchedRecord instance to classify.
        ctx: Context dictionary containing detected signals and match candidate properties.
        
    Returns:
        The matched HypothesisCategory enum value.
    """
    for category in _ORDERED:
        predicate = _PREDICATES.get(category)
        if predicate and predicate(rec, ctx):
            return category
    return H.UNCLASSIFIED

