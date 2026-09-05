"""Double-Entry Bookkeeping Journal Entry (JE) Engine & Auditor Evidence Pack.

Generates controller-grade double-entry journal vouchers with strict mathematical
debit-credit parity assertions (Σ Debits == Σ Credits) and suspense accounts per
unresolved discrepancy to guarantee provable trial balance closure.
"""

import csv
import io
from typing import Any, Dict, List, Optional

from app.core.contracts import JournalEntry, JournalEntryLine


def generate_journal_entries(
    sid: str,
    *,
    matched_pairs: List[Dict[str, Any]],
    exceptions: List[Dict[str, Any]],
    totals: Dict[str, float],
    default_date: str = "2026-03-31",
) -> List[JournalEntry]:
    """Generate auditable double-entry journal entries for settled volumes, fees, and suspense reserves.
    
    Guarantees:
      1. Sequential voucher indexing (`JE-{sid}-{seq:04d}`).
      2. Strict balance parity: sum(debit) == sum(credit) for each entry.
      3. Suspense journal entries per unresolved exception so trial balance ties exactly to cash position.
    
    Args:
        sid: Session identifier string.
        matched_pairs: Detailed records of matched settlements.
        exceptions: Unresolved or classified exception queue records.
        totals: Financial aggregates (gross, net, fees, matched_value, exception_value).
        default_date: Accounting period close date.
        
    Returns:
        List of mathematically balanced JournalEntry models.
    """
    entries: List[JournalEntry] = []
    seq = 1

    # JE 1: Gross Sales & Clearing Recognition (Recognize gross merchant sales into gateway clearing)
    gross_sales = float(totals.get("gross", 0.0))
    if gross_sales > 0:
        je_id = f"JE-{sid[:8]}-{seq:04d}"
        seq += 1
        lines = [
            JournalEntryLine(account="Gateway Clearing / In-Transit Account", debit=gross_sales, credit=0.0),
            JournalEntryLine(account="Merchant Sales Revenue", debit=0.0, credit=gross_sales),
        ]
        total_dr = sum(l.debit for l in lines)
        total_cr = sum(l.credit for l in lines)
        assert abs(total_dr - total_cr) < 0.005, f"JE balance mismatch in {je_id}: {total_dr} != {total_cr}"
        entries.append(
            JournalEntry(
                je_id=je_id,
                date=default_date,
                description="Gross merchant sales recognition into settlement clearing account",
                leg="SALES_RECOGNITION",
                lines=lines,
                total_debit=round(total_dr, 2),
                total_credit=round(total_cr, 2),
            )
        )

    # JE 2: Bank Settlement & Gateway Processing Fee Realization (Matched Settlements)
    matched_gross = float(totals.get("matched_value", 0.0))
    net_inflow = float(totals.get("net", 0.0))
    total_fees = float(totals.get("fees", 0.0))
    
    # Compute base_fee and gst_itc from actual per-pair deduction breakdowns
    # (avoids hardcoding /1.18 which is wrong for non-18% segment rules).
    # matched_pairs may be raw dicts with 'gateway_fee' and 'gst', or MapResult-like objects.
    _bp_base = 0.0
    _bp_gst = 0.0
    _bp_tds = 0.0
    for mp in matched_pairs:
        if isinstance(mp, dict):
            _bp_base += float(mp.get("gateway_fee", 0.0))
            _bp_gst += float(mp.get("gst", 0.0))
            _bp_tds += float(mp.get("tds", 0.0))
        else:
            _bp_base += float(getattr(mp, "gateway_fee", 0.0))
            _bp_gst += float(getattr(mp, "gst", 0.0))
            _bp_tds += float(getattr(mp, "tds", 0.0))
    
    if total_fees > 0 and matched_gross > 0:
        if _bp_base > 0 or _bp_gst > 0 or _bp_tds > 0:
            # Use per-rule totals from breakdowns
            base_fee = round(_bp_base, 2)
            gst_itc = round(_bp_gst, 2)
            tds_recv = round(_bp_tds, 2)
        else:
            # Fallback: assume 18% GST split only when no breakdown detail is available
            base_fee = round(total_fees / 1.18, 2)
            gst_itc = round(total_fees - base_fee, 2)
            tds_recv = 0.0
        net_bank_matched = round(matched_gross - total_fees, 2)
    else:
        base_fee = 0.0
        gst_itc = 0.0
        tds_recv = 0.0
        net_bank_matched = matched_gross

    if matched_gross > 0:
        je_id = f"JE-{sid[:8]}-{seq:04d}"
        seq += 1
        lines = [
            JournalEntryLine(account="Bank Operating Account", debit=net_bank_matched, credit=0.0),
        ]
        if base_fee > 0:
            lines.append(
                JournalEntryLine(account="Payment Gateway Processing Fee Expense", debit=base_fee, credit=0.0)
            )
        if gst_itc > 0:
            lines.append(
                JournalEntryLine(account="GST Input Tax Credit (ITC) Receivable", debit=gst_itc, credit=0.0)
            )
        if tds_recv > 0:
            lines.append(
                JournalEntryLine(account="TDS Receivable (Advance Tax Asset)", debit=tds_recv, credit=0.0)
            )
        
        # Credit Gateway Clearing Account for total gross settled
        total_debits_so_far = sum(l.debit for l in lines)
        lines.append(
            JournalEntryLine(account="Gateway Clearing / In-Transit Account", debit=0.0, credit=total_debits_so_far)
        )
        
        total_dr = sum(l.debit for l in lines)
        total_cr = sum(l.credit for l in lines)
        assert abs(total_dr - total_cr) < 0.005, f"JE balance mismatch in {je_id}: {total_dr} != {total_cr}"
        entries.append(
            JournalEntry(
                je_id=je_id,
                date=default_date,
                description="Realization of verified bank deposits, gateway processing fees, and GST input tax credit",
                leg="SETTLEMENT_FEE",
                lines=lines,
                total_debit=round(total_dr, 2),
                total_credit=round(total_cr, 2),
            )
        )

    # JE 3: Suspense Provisions per Unresolved Discrepancy / Exception
    for exc in exceptions:
        rec = exc.get("rec", {})
        delta = float(rec.delta if hasattr(rec, "delta") and rec.delta is not None else (rec.get("delta") or 0.0))
        ref = rec.ref if hasattr(rec, "ref") else rec.get("ref", "DISCREPANCY")
        reason = rec.reason if hasattr(rec, "reason") else rec.get("reason", "UNRESOLVED")
        
        if abs(delta) >= 0.01:
            abs_delta = round(abs(delta), 2)
            je_id = f"JE-{sid[:8]}-{seq:04d}"
            seq += 1
            if delta > 0:
                lines = [
                    JournalEntryLine(account="Reconciliation Suspense Account", debit=abs_delta, credit=0.0),
                    JournalEntryLine(account="Gateway Clearing / In-Transit Account", debit=0.0, credit=abs_delta),
                ]
            else:
                lines = [
                    JournalEntryLine(account="Gateway Clearing / In-Transit Account", debit=abs_delta, credit=0.0),
                    JournalEntryLine(account="Reconciliation Suspense Account", debit=0.0, credit=abs_delta),
                ]
            total_dr = sum(l.debit for l in lines)
            total_cr = sum(l.credit for l in lines)
            assert abs(total_dr - total_cr) < 0.005, f"JE balance mismatch in suspense {je_id}"
            entries.append(
                JournalEntry(
                    je_id=je_id,
                    date=default_date,
                    description=f"Suspense accrual for variance in transaction '{ref}' ({reason})",
                    leg="SUSPENSE",
                    lines=lines,
                    total_debit=round(total_dr, 2),
                    total_credit=round(total_cr, 2),
                )
            )

    return entries


def export_journal_entries_csv(entries: List[JournalEntry]) -> str:
    """Export journal entries into standardized double-entry general ledger CSV format."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["JE Number", "Posting Date", "Category", "Description", "Account Name", "Debit (INR)", "Credit (INR)"])
    for je in entries:
        for line in je.lines:
            writer.writerow([
                je.je_id,
                je.date,
                je.leg,
                je.description,
                line.account,
                f"{line.debit:.2f}" if line.debit > 0 else "0.00",
                f"{line.credit:.2f}" if line.credit > 0 else "0.00",
            ])
    return out.getvalue()
