import pytest

from app.core import llm_client
from app.core.constants import REG
from app.core.contracts import EvidencePiece
from app.engine import match


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("llm down")
    monkeypatch.setattr(llm_client, "json_chat", boom)


CFG = {"left_key": "order_id", "right_key": "utr", "left_amount": "amount",
       "right_amount": "credit", "left_date": "date", "right_date": "date",
       "tolerance": 0.01, "window_days": 3}
SCHED = REG.fee_schedules["razorpay_test_mode"]


def test_exact_raw_match_scores_full_amount():
    l = {"order_id": "A", "amount": 1000.0, "date": "2026-03-01"}
    r = {"utr": "A", "credit": 1000.0, "date": "2026-03-02"}
    v, comps, ev, sd = match.score_pair("t", l, r, CFG, SCHED, [])
    assert comps["amount"] == 1.0
    assert EvidencePiece.AMOUNT_WITHIN_TOL in ev and EvidencePiece.FEE_MODEL_MATCH not in ev
    assert v >= REG["match_auto_threshold"]


def test_fee_case_exclusive_and_detected():
    l = {"order_id": "B", "amount": 2000.0, "date": "2026-03-01"}
    r = {"utr": "B", "credit": 1952.80, "date": "2026-03-02"}
    v, comps, ev, sd = match.score_pair("t", l, r, CFG, SCHED, [])
    assert EvidencePiece.FEE_MODEL_MATCH in ev and EvidencePiece.AMOUNT_WITHIN_TOL not in ev
    assert comps["amount"] == 1.0
