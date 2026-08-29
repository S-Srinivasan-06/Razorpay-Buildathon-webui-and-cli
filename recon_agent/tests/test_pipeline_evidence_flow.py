import pytest

from app.core import llm_client


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("llm down")
    monkeypatch.setattr(llm_client, "json_chat", boom)


def test_end_to_end_classifications_and_evidence(tmp_path):
    from app.data.generator import generate
    generate(tmp_path)
    from app.pipeline import Pipeline
    p = Pipeline("test-session", auto_ack=True)
    final = p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"],
                  tmp_path / "ground_truth.jsonl")
    assert final is not None
    reasons = {i["rec"].reason.value for i in p.queue}
    assert {"refund_offset", "split", "temporal_drift", "duplicate"} <= reasons
    from app.core.contracts import EvidencePiece
    for item in p.queue:
        pieces = set(item["pieces"])
        assert not ({EvidencePiece.AMOUNT_WITHIN_TOL, EvidencePiece.FEE_MODEL_MATCH} <= pieces)
    assert final.precision_vs_truth == 1.0 and final.recall_vs_truth == 1.0
