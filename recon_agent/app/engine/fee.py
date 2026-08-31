"""Payment Gateway Fee Modeling and Decimal Precision Calculation.

Provides deterministic calculation of merchant gateway fees across multiple
pricing structures (flat rate percentage, per-transaction fixed fee, tiered volume bands)
and calculates applicable GST (Goods and Services Tax) with exact bankers rounding.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union

from app.core.contracts import FeeSchedule


def compute_fee(gross: Union[float, int, str, Decimal], schedule: FeeSchedule) -> float:
    """Compute the expected payment gateway processing fee and GST for a gross transaction amount.
    
    Calculation modes:
      - `flat_rate`: `gross * rate` (e.g. 2.0% MDR)
      - `per_txn_flat`: Fixed charge per transaction (e.g. ₹5.00)
      - `tiered`: Slices gross amount into tiered bands `[lo, hi, rate]`
      
    If `schedule.gst_rate` is non-zero (e.g., 0.18 for 18% GST), multiplies the fee
    by `(1 + gst_rate)` and quantizes the result to 2 decimal places using `ROUND_HALF_UP`.
    
    Args:
        gross: Gross transaction amount in source currency (e.g. INR).
        schedule: FeeSchedule configuration containing pricing model and GST rate.
        
    Returns:
        Calculated total fee as a float rounded to 2 decimal places.
    """
    g = Decimal(str(gross))

    if schedule.model_type == "flat_rate":
        fee = g * Decimal(str(schedule.params["rate"]))
    elif schedule.model_type == "per_txn_flat":
        fee = Decimal(str(schedule.params["flat"]))
    else:
        # Tiered volume rate bands: [(lo, hi, rate), ...]
        fee, rem = Decimal(0), g
        for lo, hi, rate in schedule.params["tiers"]:
            band = min(rem, Decimal(str(hi)) - Decimal(str(lo))) if hi else rem
            fee += band * Decimal(str(rate))
            rem -= band

    # Apply Goods and Services Tax (GST) if configured on the fee schedule
    if schedule.gst_rate:
        fee *= (1 + Decimal(str(schedule.gst_rate)))

    return float(fee.quantize(Decimal("0.01"), ROUND_HALF_UP))

