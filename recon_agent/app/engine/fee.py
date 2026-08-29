from decimal import Decimal, ROUND_HALF_UP


def compute_fee(gross, schedule):
    g = Decimal(str(gross))
    if schedule.model_type == "flat_rate":
        fee = g * Decimal(str(schedule.params["rate"]))
    elif schedule.model_type == "per_txn_flat":
        fee = Decimal(str(schedule.params["flat"]))
    else:
        fee, rem = Decimal(0), g
        for lo, hi, rate in schedule.params["tiers"]:
            band = min(rem, Decimal(str(hi)) - Decimal(str(lo))) if hi else rem
            fee += band * Decimal(str(rate))
            rem -= band
    if schedule.gst_rate:
        fee *= (1 + Decimal(str(schedule.gst_rate)))
    return float(fee.quantize(Decimal("0.01"), ROUND_HALF_UP))
