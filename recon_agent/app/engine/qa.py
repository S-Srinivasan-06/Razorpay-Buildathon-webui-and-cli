from app.core.contracts import HypothesisCategory as H
from app.core.contracts import HYPOTHESIS_PRIORITY

CTX_KEYS = ["dup_rids", "split_targets", "single_target", "partial", "fee_match",
            "tax_match", "fx_match", "fuzzy_key", "negative_credit",
            "date_only_mismatch"]

_PREDICATES = {
    H.DUPLICATE:             lambda rec, ctx: bool(ctx["dup_rids"]),
    H.SPLIT:                 lambda rec, ctx: bool(ctx["split_targets"]),
    H.PARTIAL_PAYMENT:       lambda rec, ctx: rec.delta is not None and rec.delta > 0.01
                                                and ctx["single_target"] and ctx["partial"],
    H.REFUND_OFFSET:         lambda rec, ctx: ctx["negative_credit"]
                                                or (rec.delta is not None and rec.delta < -0.01),
    H.FEE_DEDUCTION:         lambda rec, ctx: ctx["fee_match"],
    H.TAX_WITHHOLDING:       lambda rec, ctx: ctx["tax_match"],
    H.CURRENCY_CONVERSION:   lambda rec, ctx: ctx["fx_match"],
    H.TEMPORAL_DRIFT:        lambda rec, ctx: ctx["date_only_mismatch"],
    H.COUNTERPARTY_MISMATCH: lambda rec, ctx: ctx["fuzzy_key"],
    H.AMOUNT_DELTA:          lambda rec, ctx: rec.delta is not None and abs(rec.delta) > 0.01,
    H.UNCLASSIFIED:          lambda rec, ctx: True,
}

_ORDERED = sorted(HYPOTHESIS_PRIORITY, key=HYPOTHESIS_PRIORITY.get)


def classify(rec, ctx) -> H:
    for category in _ORDERED:
        if _PREDICATES[category](rec, ctx):
            return category
    return H.UNCLASSIFIED
