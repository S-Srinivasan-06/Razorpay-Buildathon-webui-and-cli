"""Unit & Integration Tests for End-to-End Pipeline Evidence Flow and Benchmark Precision/Recall.

Verifies:
  1. Pipeline achieves 100% benchmark precision and recall against synthetic ground truth.
  2. All core discrepancy categories (refund_offset, split, temporal_drift, duplicate) are recognized.
  3. Evidence factors AMOUNT_WITHIN_TOL and FEE_MODEL_MATCH maintain strict mutual exclusivity.
"""

from pathlib import Path
from typing import Any

import pytest

from app.core import llm_client
from app.core.contracts import EvidencePiece
from app.data.generator import generate
from app.pipeline import Pipeline


@pytest.fixture(autouse=True)
def no_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable external LLM calls to verify deterministic heuristic accuracy."""
    def boom(*a: Any, **k: Any) -> None:
        raise ConnectionError("llm down")

    monkeypatch.setattr(llm_client, "json_chat", boom)


def test_end_to_end_classifications_and_evidence(tmp_path: Path) -> None:
    """Verify end-to-end classification taxonomy, evidence exclusivity, and 100% benchmark precision/recall."""
    generate(tmp_path)
    p = Pipeline("test-session", auto_ack=True)
    p.set_policy(fee_rate=0.02, gst_rate=0.18, tolerance=0.01)
    final = p.run(
        [tmp_path / "payments.csv", tmp_path / "bank.csv"],
        tmp_path / "ground_truth.jsonl",
    )
    assert final is not None
    reasons = {i["rec"].reason.value for i in p.queue}
    assert {"refund_offset", "split", "temporal_drift", "duplicate"} <= reasons

    # Ensure amount within tolerance and fee model match are mutually exclusive
    for item in p.queue:
        pieces = set(item["pieces"])
        assert not ({EvidencePiece.AMOUNT_WITHIN_TOL, EvidencePiece.FEE_MODEL_MATCH} <= pieces)

    assert final.precision_vs_truth == 1.0 and final.recall_vs_truth == 1.0

