"""Payment Gateway Fee Modeling and Decimal Precision Calculation.

Provides deterministic calculation of merchant gateway fees across multiple
pricing structures (flat rate percentage, per-transaction fixed fee, tiered volume bands)
and calculates applicable GST (Goods and Services Tax) with exact bankers rounding.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional, Union

from app.core.contracts import FeeSchedule


def compute_fee(
    gross: Union[float, int, str, Decimal],
    schedule: FeeSchedule,
    method: Optional[str] = None,
) -> float:
    """Compute the expected payment gateway processing fee (including GST) for a gross transaction.
    
    Calculation modes:
      - `flat_rate`: `gross * rate + flat` (e.g. 2.0% MDR + ₹0 flat)
      - `per_txn_flat`: Fixed charge per transaction (e.g. ₹5.00)
      - `tiered`: Slices gross amount into tiered bands `[lo, hi, rate]`
      
    Instrument-aware adjustments (when method is specified):
      - `upi` / `bhim`: 0% MDR + 0% GST (zero-charge mandate)
      - `debit_card` / `dc`: 0.9% MDR (standard RBI cap)
      - `credit_card` / `cc`: Standard schedule rate (e.g. 2.0%)
      - `netbanking` / `nb`: Flat fee if specified in params, or standard schedule
    """
    g = Decimal(str(gross))
    
    # 1. Check instrument override
    m = (method or "").strip().lower()
    if m in ("upi", "bhim", "qr"):
        return 0.0
    
    rate = Decimal(str(schedule.params.get("rate", 0.0)))
    flat = Decimal(str(schedule.params.get("flat", 0.0)))

    if m in ("debit_card", "debit", "dc"):
        rate = min(rate, Decimal("0.009"))  # 0.9% cap

    if schedule.model_type == "flat_rate":
        fee = g * rate + flat
    elif schedule.model_type == "per_txn_flat":
        fee = flat or Decimal(str(schedule.params.get("flat", 5.0)))
    elif schedule.model_type == "tiered":
        # Tiered volume rate bands: [(lo, hi, rate), ...]
        fee, rem = Decimal(0), g
        for lo, hi, r in schedule.params.get("tiers", []):
            band = min(rem, Decimal(str(hi)) - Decimal(str(lo))) if hi else rem
            fee += band * Decimal(str(r))
            rem -= band
        fee += flat
    else:
        fee = g * rate + flat

    # Apply Goods and Services Tax (GST) on gateway service fee
    if schedule.gst_rate:
        fee *= (1 + Decimal(str(schedule.gst_rate)))

    return float(fee.quantize(Decimal("0.01"), ROUND_HALF_UP))


def compute_tax_component(
    gross: Union[float, int, str, Decimal],
    schedule: FeeSchedule,
    method: Optional[str] = None,
) -> float:
    """Calculate the explicit GST component (tax on gateway fee) claimable as Input Tax Credit (ITC)."""
    if not schedule.gst_rate:
        return 0.0
    
    m = (method or "").strip().lower()
    if m in ("upi", "bhim", "qr"):
        return 0.0
    
    # Calculate base MDR fee before GST
    g = Decimal(str(gross))
    rate = Decimal(str(schedule.params.get("rate", 0.0)))
    flat = Decimal(str(schedule.params.get("flat", 0.0)))
    if m in ("debit_card", "debit", "dc"):
        rate = min(rate, Decimal("0.009"))
        
    base_fee = g * rate + flat
    gst = base_fee * Decimal(str(schedule.gst_rate))
    return float(gst.quantize(Decimal("0.01"), ROUND_HALF_UP))


def compute_net_settlement(
    gross: Union[float, int, str, Decimal],
    schedule: FeeSchedule,
    method: Optional[str] = None,
) -> float:
    """Backward-compatible alias for the canonical expected-net calculation."""
    return compute_expected_net(gross, schedule, method=method)


def compute_deduction_breakdown(
    gross: Union[float, int, str, Decimal],
    schedule: FeeSchedule,
    method: Optional[str] = None,
    include_tds: Optional[bool] = None,
) -> Dict[str, float]:
    """Return one authoritative, itemized settlement deduction calculation.

    GST is charged on the gateway service fee. TDS is only included when the
    schedule explicitly declares ``apply_tds``; its model default is retained
    for anomaly diagnosis but is not silently deducted from every settlement.
    """
    gross_d = Decimal(str(gross))
    total_fee = Decimal(str(compute_fee(gross_d, schedule, method=method)))
    gst = Decimal(str(compute_tax_component(gross_d, schedule, method=method)))
    gateway_fee = total_fee - gst
    use_tds = bool(schedule.params.get("apply_tds", False)) if include_tds is None else include_tds
    tds = (gross_d * Decimal(str(schedule.tds_rate))).quantize(Decimal("0.01"), ROUND_HALF_UP) if use_tds else Decimal("0")
    total = (gateway_fee + gst + tds).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return {"gross": float(gross_d), "gateway_fee": float(gateway_fee), "gst": float(gst),
            "tds": float(tds), "total_deductions": float(total),
            "expected_net": float((gross_d - total).quantize(Decimal("0.01"), ROUND_HALF_UP))}


def compute_expected_net(
    gross: Union[float, int, str, Decimal], schedule: FeeSchedule,
    method: Optional[str] = None, include_tds: Optional[bool] = None,
) -> float:
    """Canonical settlement math: gross minus gateway fee, GST, and applicable TDS."""
    return compute_deduction_breakdown(gross, schedule, method, include_tds)["expected_net"]
