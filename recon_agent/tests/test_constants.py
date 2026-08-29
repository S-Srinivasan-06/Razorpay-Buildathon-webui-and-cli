from app.core.constants import REG


def test_registry_loads_and_fee_schedule_parsed():
    assert REG.version == "v0"
    assert REG["match_auto_threshold"] == 0.85
    assert "razorpay_test_mode" in REG.fee_schedules
    fs = REG.fee_schedules["razorpay_test_mode"]
    assert fs.params["rate"] == 0.02 and fs.gst_rate == 0.18
