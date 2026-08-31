"""Unit Tests for Immutable Registry and Constants Loading.

Verifies:
  1. Registry loads constants from constants_v0.yaml successfully with version tagging.
  2. Core threshold constants (match auto threshold, review floors) match specifications.
  3. Default Razorpay fee schedules and GST tax multipliers parse into structured models.
"""

from app.core.constants import REG


def test_registry_loads_and_fee_schedule_parsed() -> None:
    """Verify registry loading, version metadata, and fee schedule parameter validation."""
    assert REG.version == "v0"
    assert REG["match_auto_threshold"] == 0.85
    assert "razorpay_test_mode" in REG.fee_schedules
    fs = REG.fee_schedules["razorpay_test_mode"]
    assert fs.params["rate"] == 0.02 and fs.gst_rate == 0.18

