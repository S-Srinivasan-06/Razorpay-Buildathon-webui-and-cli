"""Unit Tests for Exception Queue Uniqueness and Deduplication.

Verifies:
  1. No transaction record (by (side, rid) tuple) appears more than once in the exception queue.
  2. Soft-paired right rows from unmatched candidate pairings do not duplicate as standalone right entries.
"""

from pathlib import Path
from typing import Any

import pytest

from app.core import llm_client
from app.data.generator import generate
from app.pipeline import Pipeline


def test_no_duplicate_exception_rids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that every entry in the pipeline exception queue has a unique (side, rid) identifier."""
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    generate(tmp_path)
    p = Pipeline("dedupe-test", auto_ack=True)
    p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"], tmp_path / "ground_truth.jsonl")
    seen = [(i["rec"].side, i["rec"].rid) for i in p.queue]
    assert len(seen) == len(set(seen)), f"duplicate exception entries: {seen}"

