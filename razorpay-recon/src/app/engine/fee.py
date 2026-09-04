"""Payment Gateway Fee Modeling and Decimal Precision Calculation.

Provides deterministic calculation of merchant gateway fees across multiple
pricing structures (flat rate percentage, per-transaction fixed fee, tiered volume bands)
and calculates applicable GST (Goods and Services Tax) with exact bankers rounding.
"""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple, Union

from app.core.contracts import FeeSchedule, FeeTaxRule, SegmentMatcher


def effective_tolerance(
    gross: Union[float, int, str, Decimal],
    abs_tol: float = 0.01,
    pct_tol: float = 0.0,
    mode: str = "absolute_only",
) -> float:
    """Compute effective row-specific tolerance threshold based on user policy.
    
    Modes:
      - 'greater': max(abs_tol, pct_amount)
      - 'lesser': min(abs_tol, pct_amount)
      - 'percentage_only': pct_amount
      - 'absolute_only': abs_tol (default)
    """
    g = abs(float(gross))
    pct_amount = g * (pct_tol / 100.0)
    if mode == "greater":
        return max(abs_tol, pct_amount)
    if mode == "lesser":
        return min(abs_tol, pct_amount)
    if mode == "percentage_only":
        return pct_amount
    return abs_tol


def matches_rule(
    row: Dict[str, Any],
    rule: FeeTaxRule,
    total_rows: int = 1,
    row_idx: int = 0,
) -> bool:
    """Check if a specific dataset row matches a FeeTaxRule segment matcher."""
    matcher = rule.matcher
    k = matcher.kind

    if k == "all":
        return True

    if k == "row_range_pct":
        # Derive position from _rid (authoritative, ingestion-stable row ID) if available.
        # This makes the rule self-correcting even when callers omit row_idx.
        # Fallback to row_idx only when _rid is absent (e.g. synthetic rows in tests).
        rid = row.get("_rid") if isinstance(row, dict) else None
        pos_idx = (int(rid) - 1) if rid is not None else row_idx
        curr_pct = (pos_idx / max(total_rows, 1)) * 100.0
        start = matcher.start_pct if matcher.start_pct is not None else 0.0
        end = matcher.end_pct if matcher.end_pct is not None else 100.0
        return start <= curr_pct < end or (curr_pct == 100.0 and end == 100.0)

    if k == "row_range_abs":
        rid = row.get("_rid", row_idx + 1)
        try:
            r_num = int(rid)
        except (ValueError, TypeError):
            r_num = row_idx + 1
        start = matcher.start_row if matcher.start_row is not None else 1
        end = matcher.end_row if matcher.end_row is not None else 10**9
        return start <= r_num <= end

    if k == "date_range":
        # Extract date from row
        row_date_val = None
        for cand_col in ("date", "txn_date", "created_at", "timestamp"):
            if cand_col in row and row[cand_col]:
                row_date_val = str(row[cand_col])[:10]
                break
        if not row_date_val:
            return False
        try:
            d = datetime.strptime(row_date_val, "%Y-%m-%d").date()
            if matcher.date_from and d < matcher.date_from:
                return False
            if matcher.date_to and d > matcher.date_to:
                return False
            return True
        except Exception:
            return False

    if k == "column_equals":
        if not matcher.column or matcher.column not in row:
            return False
        actual = str(row.get(matcher.column, "")).strip().lower()
        expected = str(matcher.value).strip().lower()
        return actual == expected

    if k == "column_in":
        if not matcher.column or matcher.column not in row:
            return False
        actual = str(row.get(matcher.column, "")).strip().lower()
        expected_set = [str(v).strip().lower() for v in (matcher.values or [])]
        return actual in expected_set

    return False


def resolve_rule_for_row(
    row: Dict[str, Any],
    rules: List[FeeTaxRule],
    total_rows: int = 1,
    row_idx: int = 0,
) -> Tuple[Optional[FeeTaxRule], str]:
    """Resolve the authoritative winning rule for a row among candidate segment rules.
    
    Resolution order:
      1. Collect all matching rules.
      2. If zero, return (None, "no_rule").
      3. Filter by highest priority.
      4. If ties exist, the most recently created (last-defined) wins, logged as a warning.
    """
    matched = [r for r in rules if matches_rule(row, r, total_rows, row_idx)]
    if not matched:
        return None, "no_rule_matched"

    if len(matched) == 1:
        return matched[0], "exact_rule_match"

    max_prio = max(r.priority for r in matched)
    prio_candidates = [r for r in matched if r.priority == max_prio]

    if len(prio_candidates) == 1:
        return prio_candidates[0], f"priority_win(prio={max_prio})"

    # Ties: last-defined wins
    winner = prio_candidates[-1]
    tied_labels = [c.label for c in prio_candidates]
    note = f"tie_break_last_defined(winner={winner.label}, tied={tied_labels})"
    return winner, note


def compute_fee(
    gross: Union[float, int, str, Decimal],
    schedule: Optional[FeeSchedule] = None,
    method: Optional[str] = None,
) -> float:
    """Compute gateway fee from a FeeSchedule (backward-compatible)."""
    if not schedule:
        return 0.0
    g = Decimal(str(gross))
    m = (method or "").strip().lower()
    if m in ("upi", "bhim", "qr"):
        return 0.0
    rate = Decimal(str(schedule.params.get("rate", 0.0)))
    flat = Decimal(str(schedule.params.get("flat", 0.0)))
    if m in ("debit_card", "debit", "dc"):
        dc_cap = Decimal(str(schedule.params.get("debit_card_cap", schedule.params.get("debit_card_rate", "0.009"))))
        rate = min(rate, dc_cap)

    if schedule.model_type == "flat_rate":
        fee = g * rate + flat
    elif schedule.model_type == "per_txn_flat":
        fee = flat or Decimal(str(schedule.params.get("flat", 5.0)))
    elif schedule.model_type == "tiered":
        fee, rem = Decimal(0), g
        for lo, hi, r in schedule.params.get("tiers", []):
            band = min(rem, Decimal(str(hi)) - Decimal(str(lo))) if hi else rem
            fee += band * Decimal(str(r))
            rem -= band
        fee += flat
    else:
        fee = g * rate + flat

    if schedule.gst_rate:
        fee *= (1 + Decimal(str(schedule.gst_rate)))
    return float(fee.quantize(Decimal("0.01"), ROUND_HALF_UP))


def compute_tax_component(
    gross: Union[float, int, str, Decimal],
    schedule: Optional[FeeSchedule] = None,
    method: Optional[str] = None,
) -> float:
    """Compute GST component from a FeeSchedule (backward-compatible)."""
    if not schedule or not schedule.gst_rate:
        return 0.0
    m = (method or "").strip().lower()
    if m in ("upi", "bhim", "qr"):
        return 0.0
    g = Decimal(str(gross))
    rate = Decimal(str(schedule.params.get("rate", 0.0)))
    flat = Decimal(str(schedule.params.get("flat", 0.0)))
    if m in ("debit_card", "debit", "dc"):
        dc_cap = Decimal(str(schedule.params.get("debit_card_cap", schedule.params.get("debit_card_rate", "0.009"))))
        rate = min(rate, dc_cap)
    base_fee = g * rate + flat
    gst = base_fee * Decimal(str(schedule.gst_rate))
    return float(gst.quantize(Decimal("0.01"), ROUND_HALF_UP))


def compute_net_settlement(
    gross: Union[float, int, str, Decimal],
    schedule: Optional[FeeSchedule] = None,
    method: Optional[str] = None,
) -> float:
    """Backward-compatible alias for the canonical expected-net calculation."""
    return compute_expected_net(gross, schedule=schedule, method=method)


def compute_deduction_breakdown(
    gross: Union[float, int, str, Decimal],
    schedule: Optional[FeeSchedule] = None,
    method: Optional[str] = None,
    include_tds: Optional[bool] = None,
    rules: Optional[List[FeeTaxRule]] = None,
    row: Optional[Dict[str, Any]] = None,
    total_rows: int = 1,
    row_idx: int = 0,
) -> Dict[str, Any]:
    """Return an authoritative itemized settlement deduction calculation.
    
    Supports both new segment-based FeeTaxRule lists and legacy FeeSchedule models.
    Default state for every session without explicit rules or schedule:
    zero fee, zero tax, zero deductions.
    """
    gross_d = Decimal(str(gross))

    # Priority 1: Segment-based FeeTaxRule evaluation
    if rules is not None:
        if row is not None and len(rules) > 0:
            winning_rule, note = resolve_rule_for_row(row, rules, total_rows, row_idx)
            if winning_rule:
                fee_rate = Decimal(str(winning_rule.fee_rate))
                flat_fee = Decimal(str(winning_rule.flat_fee))
                gst_rate = Decimal(str(winning_rule.gst_rate))
                tds_rate = Decimal(str(winning_rule.tds_rate))
                
                gateway_fee = (gross_d * fee_rate + flat_fee).quantize(Decimal("0.01"), ROUND_HALF_UP)
                gst = (gateway_fee * gst_rate).quantize(Decimal("0.01"), ROUND_HALF_UP)
                tds = (gross_d * tds_rate).quantize(Decimal("0.01"), ROUND_HALF_UP)
                total = (gateway_fee + gst + tds).quantize(Decimal("0.01"), ROUND_HALF_UP)
                expected_net = (gross_d - total).quantize(Decimal("0.01"), ROUND_HALF_UP)

                return {
                    "gross": float(gross_d),
                    "gateway_fee": float(gateway_fee),
                    "gst": float(gst),
                    "tds": float(tds),
                    "total_deductions": float(total),
                    "expected_net": float(expected_net),
                    "rule_id": winning_rule.rule_id,
                    "rule_label": winning_rule.label,
                    "rule_note": note,
                }
        
        # Zero rules or no rule matched in rules mode -> zero deductions
        return {
            "gross": float(gross_d),
            "gateway_fee": 0.0,
            "gst": 0.0,
            "tds": 0.0,
            "total_deductions": 0.0,
            "expected_net": float(gross_d),
            "rule_id": None,
            "rule_label": "Zero Fee / Tax (No Rule)",
            "rule_note": "No active rule matched row; zero deductions applied",
        }

    # Priority 2: Legacy FeeSchedule evaluation
    if schedule is not None:
        total_fee = Decimal(str(compute_fee(gross_d, schedule, method=method)))
        gst = Decimal(str(compute_tax_component(gross_d, schedule, method=method)))
        gateway_fee = total_fee - gst
        use_tds = bool(schedule.params.get("apply_tds", False)) if include_tds is None else include_tds
        tds = (gross_d * Decimal(str(schedule.tds_rate))).quantize(Decimal("0.01"), ROUND_HALF_UP) if use_tds else Decimal("0")
        total = (gateway_fee + gst + tds).quantize(Decimal("0.01"), ROUND_HALF_UP)
        return {
            "gross": float(gross_d),
            "gateway_fee": float(gateway_fee),
            "gst": float(gst),
            "tds": float(tds),
            "total_deductions": float(total),
            "expected_net": float((gross_d - total).quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "rule_id": schedule.schedule_id,
            "rule_label": f"Legacy Schedule ({schedule.provider})",
            "rule_note": "Evaluated via legacy FeeSchedule",
        }

    # Default: Zero fee, zero tax
    return {
        "gross": float(gross_d),
        "gateway_fee": 0.0,
        "gst": 0.0,
        "tds": 0.0,
        "total_deductions": 0.0,
        "expected_net": float(gross_d),
        "rule_id": None,
        "rule_label": "Zero Fee / Tax (Default)",
        "rule_note": "Zero deductions applied",
    }


def compute_expected_net(
    gross: Union[float, int, str, Decimal],
    schedule: Optional[FeeSchedule] = None,
    method: Optional[str] = None,
    include_tds: Optional[bool] = None,
    rules: Optional[List[FeeTaxRule]] = None,
    row: Optional[Dict[str, Any]] = None,
    total_rows: int = 1,
    row_idx: int = 0,
) -> float:
    """Canonical settlement math: gross minus gateway fee, GST, and applicable TDS."""
    return float(compute_deduction_breakdown(
        gross,
        schedule=schedule,
        method=method,
        include_tds=include_tds,
        rules=rules,
        row=row,
        total_rows=total_rows,
        row_idx=row_idx,
    )["expected_net"])
