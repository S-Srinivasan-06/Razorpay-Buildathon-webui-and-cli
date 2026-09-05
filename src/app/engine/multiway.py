"""Multi-Way Three-Legged Reconciliation & Chaining Engine.
Orchestrates multi-dataset settlement chaining across merchant sales, payment gateway
intermediary ledgers, and downstream bank statement credit deposits:
  Leg 1: Merchant Sales (Order Sources) <-> Payment Gateway Ledger (Hub)
  Leg 2: Payment Gateway Ledger (Hub) <-> Bank Operating Statements
  Consolidated: Full Transitive Settlement State & Aging Cash Position
"""
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.contracts import (
    CashPosition,
    FeeTaxRule,
    MultiWayLeg,
    MultiWayReport,
)
from app.core.channels import MessageKind, validate_and_route
from app.engine.fee import compute_deduction_breakdown
from app.engine.journal import generate_journal_entries
from app.engine import match


def detect_table_roles(tables: Dict[str, List[Dict[str, Any]]]) -> Tuple[List[str], str, List[str]]:
    """Classify ingested table names into sales sources, gateway hub, and banking statements."""
    sales_tables: List[str] = []
    hub_table: Optional[str] = None
    bank_tables: List[str] = []

    for name, rows in tables.items():
        if not rows:
            continue
        first_row = rows[0]
        cols = {c.lower() for c in first_row.keys()}
        name_lower = name.lower()

        if any(stem in name_lower for stem in ("gateway", "ledger", "settlements", "razorpay")) or (
            any("fee" in c for c in cols) and any("net" in c for c in cols)
        ):
            hub_table = name
        elif any(stem in name_lower for stem in ("bank", "statement", "icici", "hdfc", "stmt")) or (
            any("credit" in c or "deposit" in c or "utr" in c for c in cols) and not any("fee" in c for c in cols)
        ):
            bank_tables.append(name)
        else:
            sales_tables.append(name)

    if not hub_table:
        all_names = list(tables.keys())
        if len(all_names) >= 3:
            hub_table = all_names[1]
            sales_tables = [all_names[0]]
            bank_tables = all_names[2:]
        elif len(all_names) == 2:
            hub_table = all_names[0]
            bank_tables = [all_names[1]]

    return sales_tables, hub_table or "", bank_tables


def _find_col(row: Dict[str, Any], candidates: List[str], exclude: Optional[List[str]] = None) -> Optional[str]:
    """Find the first matching column name from a list of candidate stems.

    Args:
        row: Sample row whose keys are searched.
        candidates: Lowercase stems to match against.
        exclude: Optional list of substrings that must NOT appear in the column name
                 (e.g. ["profit"] prevents matching 'razorpay_net_profit' as a net column).
    """
    exclude = exclude or []
    # 1. First pass: exact matches by candidate priority order
    for cand in candidates:
        for c in row.keys():
            if c.startswith("_"):
                continue
            cl = c.lower()
            if any(x in cl for x in exclude):
                continue
            if cand == cl:
                return c
    # 2. Second pass: substring matches by candidate priority order
    for cand in candidates:
        for c in row.keys():
            if c.startswith("_"):
                continue
            cl = c.lower()
            if any(x in cl for x in exclude):
                continue
            if cand in cl:
                return c
    return None


def _resolve_hub_net(
    h: Dict[str, Any],
    hub_net_col: Optional[str],
    hub_gross_col: str,
    hub_fee_col: Optional[str],
    hub_gst_col: Optional[str],
    hub_bank_charge_col: Optional[str],
    rules: Optional[List[FeeTaxRule]],
    schedule: Optional[Any],
    total_hub_rows: int,
    row_idx: int,
) -> float:
    """Compute the expected net settlement amount for a hub record.

    Resolution order:
      1. Explicit net column (e.g. net_settled_inr in benchmark_3file).
      2. gross - bank_gateway_charge (enterprise ecosystem: bank receives gross minus interchange).
      3. gross - merchant_fee_collected (fallback when bank charge column is absent).
      4. Rules/schedule-based computation from gross.
    """
    # 1. Explicit net column
    if hub_net_col and h.get(hub_net_col) is not None:
        return float(h.get(hub_net_col, 0.0) or 0.0)

    gross = float(h.get(hub_gross_col, 0.0) or 0.0)

    # 2. gross - bank_gateway_charge (what the bank actually receives)
    if hub_bank_charge_col and h.get(hub_bank_charge_col) is not None:
        bank_charge = float(h.get(hub_bank_charge_col, 0.0) or 0.0)
        if bank_charge > 0:
            return round(gross - bank_charge, 2)

    # 3. gross - merchant_fee_collected
    if hub_fee_col and h.get(hub_fee_col) is not None:
        fee = float(h.get(hub_fee_col, 0.0) or 0.0)
        gst = float(h.get(hub_gst_col, 0.0) or 0.0) if hub_gst_col else 0.0
        if fee > 0:
            return round(gross - fee - gst, 2)

    # 4. Rules/schedule-based computation
    if rules is not None and len(rules) > 0:
        brk = compute_deduction_breakdown(gross, rules=rules, row=h, total_rows=total_hub_rows, row_idx=row_idx)
        return brk["expected_net"]
    if schedule is not None:
        brk = compute_deduction_breakdown(gross, schedule=schedule)
        return brk["expected_net"]

    return gross


def run_multiway_chaining(
    sid: str,
    tables: Dict[str, List[Dict[str, Any]]],
    *,
    rules: Optional[List[FeeTaxRule]] = None,
    schedule: Optional[Any] = None,
    opening_balance: float = 0.0,
    tolerance: float = 0.02,
) -> MultiWayReport:
    """Execute end-to-end 3-way reconciliation chaining across all ingested tables."""
    sales_tables, hub_name, bank_tables = detect_table_roles(tables)
    hub_rows = tables.get(hub_name, []) if hub_name else []

    validate_and_route(
        sid, MessageKind.TRACE,
        {
            "event": "MULTIWAY_INITIATED",
            "detail": {
                "sales_sources": sales_tables,
                "hub": hub_name,
                "banks": bank_tables,
                "total_tables": len(tables),
            }
        },
        "system"
    )

    # Build cross-reference dictionary across sales tables if PO/Invoice chaining is present
    sales_alias_map: Dict[str, str] = {}
    for s_name in sales_tables:
        for row in tables.get(s_name, []):
            p_val = str(row.get("ref_po_id") or row.get("po_id") or "").strip().upper()
            i_val = str(row.get("invoice_no") or row.get("invoice_id") or row.get("linked_invoice") or "").strip().upper()
            if p_val and i_val:
                sales_alias_map[p_val] = i_val
                sales_alias_map[i_val] = p_val

    # ---- Hub column resolution ----
    sample_hub = hub_rows[0] if hub_rows else {}
    hub_order_col = _find_col(sample_hub, ["linked_invoice", "invoice_no", "order_id", "order_ref", "reference_id", "id", "ref"]) or "order_id"
    hub_utr_col = _find_col(sample_hub, ["settlement_utr", "utr_number", "ref_utr", "utr", "payout_utr", "bank_ref"])
    hub_gross_col = _find_col(sample_hub, ["principal_amt", "gross_inr", "gross_amount", "gross", "order_amount", "amount", "total"]) or "gross_amount"
    # Exclude "profit" to avoid matching 'razorpay_net_profit' as a net settlement column
    hub_net_col = _find_col(
        sample_hub,
        ["net_payout_supplier", "net_settled_inr", "net_settlement_amount", "settlement_amount", "net_settled", "net_credit", "net_amount"],
        exclude=["profit"],
    )
    hub_fee_col = _find_col(sample_hub, ["platform_fee_amt", "gateway_fee_inr", "gateway_fee", "merchant_fee_collected", "fee", "charges", "mdr"])
    hub_gst_col = _find_col(sample_hub, ["tds_deducted", "gst_on_fee_inr", "tax_gst", "gst_on_fee", "gst", "tax"], exclude=["goods_tax_rate", "food_tax_rate"])
    hub_bank_charge_col = _find_col(sample_hub, ["bank_gateway_charge", "bank_charge", "interchange"])
    hub_date_col = _find_col(sample_hub, ["created_at", "payout_date", "settlement_date", "clearing_date", "transaction_date", "date"]) or "date"

    # Index hub rows by order reference and alternative identifiers
    hub_by_order: Dict[str, Dict[str, Any]] = {}
    for r in hub_rows:
        for k in (hub_order_col, "linked_invoice", "rzp_txn_id", "order_id", "order_ref", "id"):
            order_val = str(r.get(k, "")).strip().upper()
            if order_val:
                hub_by_order[order_val] = r
                if order_val in sales_alias_map:
                    hub_by_order[sales_alias_map[order_val]] = r

    # Track matched pairs and exceptions for journal entry generation
    multiway_matched: List[Dict[str, Any]] = []
    multiway_exceptions: List[Dict[str, Any]] = []

    # -------------------------------------------------------------
    # LEG 1: Sales Sources <-> Gateway Hub
    # -------------------------------------------------------------
    total_sales_gross = 0.0
    sales_matched_count = 0
    sales_unmatched_count = 0
    sales_matched_value = 0.0
    sales_unmatched_value = 0.0
    matched_hub_rids_from_sales: Set[int] = set()
    dropped_by_gateway_count = 0

    for s_name in sales_tables:
        s_rows = tables.get(s_name, [])
        for s_idx, s in enumerate(s_rows):
            s_order_col = _find_col(s, ["invoice_no", "po_id", "ref_po_id", "order_ref", "order_id", "id", "ref"]) or "order_id"
            s_amt_col = _find_col(s, ["invoice_total", "total_payable", "gross_inr", "gross_amount", "gross", "order_total", "amount", "total"]) or "amount"
            order_id = str(s.get(s_order_col, "")).strip().upper()
            amt = float(s.get(s_amt_col, 0.0) or 0.0)
            total_sales_gross += amt

            hub_rec = hub_by_order.get(order_id)
            if not hub_rec and order_id in sales_alias_map:
                hub_rec = hub_by_order.get(sales_alias_map[order_id])

            if hub_rec:
                hub_gross = float(hub_rec.get(hub_gross_col, 0.0) or 0.0)

                # Reconstruct gross from net + fee if gross column is missing/zero
                if hub_gross <= 0.0:
                    h_net_val = float(hub_rec.get(hub_net_col, 0.0) or 0.0) if hub_net_col else 0.0
                    h_fee_val = float(hub_rec.get(hub_fee_col, 0.0) or 0.0) if hub_fee_col else 0.0
                    h_gst_val = float(hub_rec.get(hub_gst_col, 0.0) or 0.0) if hub_gst_col else 0.0
                    hub_gross = round(h_net_val + h_fee_val + h_gst_val, 2)

                if abs(amt - hub_gross) <= tolerance:
                    sales_matched_count += 1
                    sales_matched_value += amt
                    matched_hub_rids_from_sales.add(hub_rec.get("_rid", 0))

                    # Compute fee/gst breakdown for journal entries
                    h_fee = float(hub_rec.get(hub_fee_col, 0.0) or 0.0) if hub_fee_col else 0.0
                    h_gst = float(hub_rec.get(hub_gst_col, 0.0) or 0.0) if hub_gst_col else 0.0
                    h_tds = 0.0
                    if h_fee == 0.0 and (rules or schedule):
                        brk = compute_deduction_breakdown(
                            amt, rules=rules, schedule=schedule,
                            row=s, total_rows=len(s_rows), row_idx=s_idx,
                        )
                        h_fee = brk["gateway_fee"]
                        h_gst = brk["gst"]
                        h_tds = brk["tds"]
                    multiway_matched.append({
                        "order_ref": order_id,
                        "gross": amt,
                        "net": round(amt - h_fee - h_gst - h_tds, 2),
                        "gateway_fee": h_fee,
                        "gst": h_gst,
                        "tds": h_tds,
                    })
                else:
                    sales_unmatched_count += 1
                    sales_unmatched_value += amt
                    multiway_exceptions.append({
                        "rec": {"ref": order_id, "delta": round(amt - hub_gross, 2), "reason": "gateway_variance"}
                    })
            else:
                sales_unmatched_count += 1
                sales_unmatched_value += amt
                dropped_by_gateway_count += 1
                multiway_exceptions.append({
                    "rec": {"ref": order_id, "delta": amt, "reason": "dropped_by_gateway"}
                })

    leg1_match_rate = sales_matched_count / max(sales_matched_count + sales_unmatched_count, 1)
    leg1_report = MultiWayLeg(
        leg_name="Leg 1: Merchant Sales -> Gateway Hub",
        source_table=",".join(sales_tables) if sales_tables else "sales",
        target_table=hub_name,
        matched_count=sales_matched_count,
        unmatched_count=sales_unmatched_count,
        matched_value=round(sales_matched_value, 2),
        unmatched_value=round(sales_unmatched_value, 2),
        match_rate=round(leg1_match_rate, 4),
    )

    validate_and_route(
        sid, MessageKind.TRACE,
        {
            "event": "MULTIWAY_LEG1_COMPLETED",
            "detail": {
                "leg": "Merchant Sales <-> Gateway Hub",
                "matched": sales_matched_count,
                "unmatched": sales_unmatched_count,
                "match_rate": f"{leg1_match_rate*100:.1f}%",
                "volume": f"INR {sales_matched_value:,.2f}",
            }
        },
        "system"
    )

    # -------------------------------------------------------------
    # LEG 2: Gateway Hub <-> Bank Statements
    # -------------------------------------------------------------
    bank_credits_by_ref: Dict[str, Dict[str, Any]] = {}
    unmatched_bank_rows: List[Dict[str, Any]] = []
    total_refund_debits = 0.0
    total_bank_credits = 0.0

    for b_name in bank_tables:
        b_rows = tables.get(b_name, [])
        for b in b_rows:
            b_credit_col = _find_col(b, ["credit_amt", "deposit_amt", "credit_inr", "credit", "deposit_amount", "deposit", "net_amount", "amount"]) or "credit"
            b_debit_col = _find_col(b, ["debit_amt", "withdrawal_amt", "debit_inr", "debit", "withdrawal", "refund"])
            credit_val = float(b.get(b_credit_col, 0.0) or 0.0)

            ref_vals: Set[str] = set()
            for cand_col in ("ref_utr", "utr_number", "settlement_utr", "order_reference", "order_ref", "order_id", "utr", "transaction_ref", "bank_ref", "ref"):
                c = _find_col(b, [cand_col])
                if c and str(b.get(c, "")).strip():
                    ref_vals.add(str(b.get(c)).strip().upper())

            desc = str(b.get("description") or b.get("narration") or "").strip().upper()
            if desc:
                for token in re.findall(r"[A-Z0-9_\-]+", desc):
                    if len(token) >= 5:
                        ref_vals.add(token)

            if b_debit_col and float(b.get(b_debit_col, 0.0) or 0.0) > 0:
                total_refund_debits += float(b.get(b_debit_col, 0.0))
            elif credit_val < 0:
                total_refund_debits += abs(credit_val)
            else:
                total_bank_credits += credit_val
                for r_val in ref_vals:
                    bank_credits_by_ref[r_val] = b
                if not ref_vals:
                    unmatched_bank_rows.append(b)

    # Match Hub records to Bank deposits
    fully_reconciled_count = 0
    settled_in_bank_value = 0.0
    in_transit_t1 = 0.0
    in_transit_t2 = 0.0
    in_transit_t7_plus = 0.0
    total_fees_withheld = 0.0
    total_gst_withheld = 0.0
    total_tds_withheld = 0.0
    total_bank_charges = 0.0
    gateway_variance_count = 0
    gateway_variance_value = 0.0
    pending_bank_clearing_count = 0
    matched_bank_refs: Set[str] = set()

    for h_idx, h in enumerate(hub_rows):
        order_ref = str(h.get(hub_order_col, "")).strip().upper()
        h_utr = str(h.get(hub_utr_col, "")).strip().upper() if hub_utr_col else ""
        h_txn = str(h.get("rzp_txn_id", "")).strip().upper()
        h_gross = float(h.get(hub_gross_col, 0.0) or 0.0)
        h_fee = float(h.get(hub_fee_col, 0.0) or 0.0) if hub_fee_col else 0.0
        h_gst = float(h.get(hub_gst_col, 0.0) or 0.0) if hub_gst_col else 0.0
        h_bank_charge = float(h.get(hub_bank_charge_col, 0.0) or 0.0) if hub_bank_charge_col else 0.0
        h_date_str = str(h.get(hub_date_col, "2026-03-01"))[:10]
        h_tds = 0.0

        # Reconstruct gross from net + fee if gross column is missing/zero
        if h_gross <= 0.0:
            h_net_val = float(h.get(hub_net_col, 0.0) or 0.0) if hub_net_col else 0.0
            h_fee_val = float(h.get(hub_fee_col, 0.0) or 0.0) if hub_fee_col else 0.0
            h_gst_val = float(h.get(hub_gst_col, 0.0) or 0.0) if hub_gst_col else 0.0
            h_gross = round(h_net_val + h_fee_val + h_gst_val, 2)

        # Skip zero-gross records (failed/cancelled transactions)
        if h_gross <= 0.0:
            continue

        # File didn't provide a fee and there's no bank-charge override column —
        # let the rules/schedule engine derive fee, GST, and TDS from gross,
        # mirroring the Leg 1 fallback so both legs stay consistent.
        if h_fee == 0.0 and h_bank_charge == 0.0 and (rules or schedule):
            brk = compute_deduction_breakdown(
                h_gross, rules=rules, schedule=schedule,
                row=h, total_rows=len(hub_rows), row_idx=h_idx,
            )
            h_fee = brk["gateway_fee"]
            h_gst = brk["gst"]
            h_tds = brk["tds"]

        total_fees_withheld += h_fee
        total_gst_withheld += h_gst
        total_tds_withheld += h_tds
        total_bank_charges += h_bank_charge

        # Compute expected net using the resolution chain
        h_net = _resolve_hub_net(
            h, hub_net_col, hub_gross_col, hub_fee_col, hub_gst_col,
            hub_bank_charge_col, rules, schedule, len(hub_rows), h_idx,
        )

        # Check if matched in bank across UTR, order reference, or transaction id
        bank_match = None
        matched_bank_key = None
        for k in (h_utr, order_ref, h_txn):
            if k and k in bank_credits_by_ref:
                bank_match = bank_credits_by_ref[k]
                matched_bank_key = k
                break

        if bank_match:
            b_credit_col = _find_col(bank_match, ["credit_amt", "deposit_amt", "credit_inr", "credit", "deposit_amount", "deposit", "net_amount", "amount"]) or "credit"
            b_credit = float(bank_match.get(b_credit_col, 0.0) or 0.0)

            if abs(h_net - b_credit) <= tolerance:
                fully_reconciled_count += 1
                settled_in_bank_value += b_credit
                matched_bank_refs.add(matched_bank_key or order_ref)
                multiway_matched.append({
                    "order_ref": order_ref,
                    "gross": h_gross,
                    "net": b_credit,
                    "gateway_fee": h_fee,
                    "gst": h_gst,
                    "tds": h_tds,
                })
            else:
                gateway_variance_count += 1
                gateway_variance_value += h_net
                multiway_exceptions.append({
                    "rec": {"ref": order_ref, "delta": round(h_net - b_credit, 2), "reason": "gateway_variance"}
                })
        else:
            pending_bank_clearing_count += 1
            multiway_exceptions.append({
                "rec": {"ref": order_ref, "delta": h_net, "reason": "in_transit"}
            })
            try:
                dt = datetime.strptime(h_date_str, "%Y-%m-%d").date()
                diff_days = (datetime.now(timezone.utc).date() - dt).days
            except Exception:
                diff_days = 1
            if diff_days <= 1:
                in_transit_t1 += h_net
            elif diff_days == 2:
                in_transit_t2 += h_net
            else:
                in_transit_t7_plus += h_net

    in_transit_total = in_transit_t1 + in_transit_t2 + in_transit_t7_plus
    direct_bank_charge_count = len(bank_credits_by_ref) - len(matched_bank_refs) + len(unmatched_bank_rows)

    leg2_match_rate = fully_reconciled_count / max(len(hub_rows), 1)
    leg2_report = MultiWayLeg(
        leg_name="Leg 2: Gateway Hub -> Bank Statements",
        source_table=hub_name,
        target_table=",".join(bank_tables) if bank_tables else "bank",
        matched_count=fully_reconciled_count,
        unmatched_count=len(hub_rows) - fully_reconciled_count,
        matched_value=round(settled_in_bank_value, 2),
        unmatched_value=round(in_transit_total, 2),
        match_rate=round(leg2_match_rate, 4),
    )

    validate_and_route(
        sid, MessageKind.TRACE,
        {
            "event": "MULTIWAY_LEG2_COMPLETED",
            "detail": {
                "leg": "Gateway Hub <-> Bank Operating Statements",
                "settled_in_bank": fully_reconciled_count,
                "in_transit": pending_bank_clearing_count,
                "match_rate": f"{leg2_match_rate*100:.1f}%",
                "settled_volume": f"INR {settled_in_bank_value:,.2f}",
            }
        },
        "system"
    )

    # -------------------------------------------------------------
    # CASH POSITION & CONTROLLER INVARIANT
    # -------------------------------------------------------------
    expected_settlements = round(settled_in_bank_value + in_transit_total, 2)
    exception_at_risk = round(sales_unmatched_value + gateway_variance_value, 2)

    projected_closing = round(
        opening_balance + settled_in_bank_value + in_transit_total - total_refund_debits, 2
    )

    # Independent cross-check: gross sales minus all deductions minus refunds minus exceptions
    effective_deductions = total_bank_charges if (hub_bank_charge_col and total_bank_charges > 0) else (total_fees_withheld + total_gst_withheld + total_tds_withheld)
    expected_closing_independent = round(
        opening_balance
        + total_sales_gross
        - effective_deductions
        - total_refund_debits
        - exception_at_risk,
        2
    )
    invariant_diff = abs(projected_closing - expected_closing_independent)
    # Allow tolerance proportional to transaction volume (rounding accumulation)
    invariant_tolerance = max(1.0, 0.02 * len(hub_rows))
    if invariant_diff > invariant_tolerance:
        import warnings
        warnings.warn(
            f"Cash position invariant deviation: projected={projected_closing}, "
            f"independent={expected_closing_independent}, diff={invariant_diff:.2f} "
            f"(tolerance={invariant_tolerance:.2f})"
        )

    cash_pos = CashPosition(
        opening_balance=round(opening_balance, 2),
        gross_sales=round(total_sales_gross, 2),
        expected_settlements=round(expected_settlements, 2),
        settled_in_bank=round(settled_in_bank_value, 2),
        in_transit_total=round(in_transit_total, 2),
        in_transit_t1=round(in_transit_t1, 2),
        in_transit_t2=round(in_transit_t2, 2),
        in_transit_t7_plus=round(in_transit_t7_plus, 2),
        fees_withheld=round(total_fees_withheld, 2),
        gst_withheld=round(total_gst_withheld, 2),
        tds_withheld=round(total_tds_withheld, 2),
        refund_chargeback_reserve=round(total_refund_debits, 2),
        exception_value_at_risk=round(exception_at_risk, 2),
        projected_closing=round(projected_closing, 2),
        variance_unexplained=round(invariant_diff, 2),
    )

    validate_and_route(
        sid, MessageKind.TRACE,
        {
            "event": "MULTIWAY_CASH_BALANCED",
            "detail": {
                "gross_sales": f"INR {total_sales_gross:,.2f}",
                "projected_closing": f"INR {projected_closing:,.2f}",
                "unexplained_variance": f"INR {invariant_diff:.2f}",
                "status": "BALANCED [OK]" if invariant_diff <= invariant_tolerance else "VARIANCE_AT_RISK",
            }
        },
        "system"
    )

    # -------------------------------------------------------------
    # DOUBLE-ENTRY JOURNAL ENTRIES (now with populated matched_pairs & exceptions)
    # -------------------------------------------------------------
    totals = {
        "gross": round(total_sales_gross, 2),
        "net": round(settled_in_bank_value, 2),
        "fees": round(total_fees_withheld + total_gst_withheld + total_tds_withheld, 2),
        "matched_value": round(sales_matched_value, 2),
        "exception_value": round(exception_at_risk, 2),
    }
    journal_entries = generate_journal_entries(
        sid,
        matched_pairs=multiway_matched,
        exceptions=multiway_exceptions,
        totals=totals,
    )

    total_orders = sales_matched_count + sales_unmatched_count
    consolidated_match_rate = fully_reconciled_count / max(total_orders, 1)

    return MultiWayReport(
        legs=[leg1_report, leg2_report],
        consolidated_match_rate=round(consolidated_match_rate, 4),
        total_orders_evaluated=total_orders,
        fully_reconciled_count=fully_reconciled_count,
        pending_bank_clearing_count=pending_bank_clearing_count,
        gateway_variance_count=gateway_variance_count,
        dropped_by_gateway_count=dropped_by_gateway_count,
        direct_bank_charge_count=direct_bank_charge_count,
        cash_position=cash_pos,
        journal_entries=journal_entries,
    )
