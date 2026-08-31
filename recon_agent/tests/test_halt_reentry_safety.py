"""Unit Tests for State Machine Halt and Re-entry Safety Invariants.

Verifies:
  1. Resuming a low-confidence mapping halt re-evaluates the validation gate rather than
     silently bypassing the check and advancing to POLICY_GENERATED with invalid schema links.
  2. Resuming an unresolvable schema halt (zero linkable columns) re-halts cleanly without
     infinite loops or hanging threads.
"""

from pathlib import Path
from typing import Any

import pytest

from app.core import llm_client
from app.core.contracts import ColumnProfile
from app.core.states import State
from app.pipeline import Pipeline


def test_low_confidence_mapping_rehalts_on_resume_not_bypassed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify resuming a below-floor mapping halt re-evaluates the confidence floor instead of bypassing."""
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    p = Pipeline("v1-test", auto_ack=False)
    # Two tables with marginal key overlap resulting in low mapping confidence
    p.tables = {
        "left": [{"_rid": 1, "id": "X1", "amt": 10.0}, {"_rid": 2, "id": "X2", "amt": 20.0}],
        "right": [{"_rid": 1, "ref": "Z9", "val": 999.0}],
    }
    p.profiles = {
        "left": [
            ColumnProfile(
                name="id",
                dtype="text",
                numeric_ratio=0,
                date_ratio=0,
                cardinality=1.0,
                null_rate=0,
                min_len=2,
                max_len=2,
                sample_values=["X1"],
                pii_likelihood=0,
            )
        ],
        "right": [
            ColumnProfile(
                name="ref",
                dtype="text",
                numeric_ratio=0,
                date_ratio=0,
                cardinality=1.0,
                null_rate=0,
                min_len=2,
                max_len=2,
                sample_values=["Z9"],
                pii_likelihood=0,
            )
        ],
    }
    ok = p.propose_mapping()
    if ok:
        ok = p.validate_mapping()
    assert p.sm.state == State.HALT, "expected halt on low-confidence mapping"
    p.sm.resume()
    result = p.continue_run()
    # Must NOT have silently advanced to POLICY_GENERATED or DRY_RUN with bad schema mapping;
    # must re-halt on the unresolved condition
    assert p.sm.state == State.HALT, "resume must re-check, not bypass, the confidence gate"


def test_no_linkable_columns_rehalts_not_infinite_loops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify resuming a no-linkable-columns halt re-halts promptly without infinite loops or hanging."""
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    p = Pipeline("v2-test", auto_ack=False)
    p.tables = {"left": [{"_rid": 1, "a": "foo"}], "right": [{"_rid": 1, "b": "bar"}]}
    p.profiles = {
        "left": [
            ColumnProfile(
                name="a",
                dtype="text",
                numeric_ratio=0,
                date_ratio=0,
                cardinality=1.0,
                null_rate=0,
                min_len=3,
                max_len=3,
                sample_values=["foo"],
                pii_likelihood=0,
            )
        ],
        "right": [
            ColumnProfile(
                name="b",
                dtype="text",
                numeric_ratio=0,
                date_ratio=0,
                cardinality=1.0,
                null_rate=0,
                min_len=3,
                max_len=3,
                sample_values=["bar"],
                pii_likelihood=0,
            )
        ],
    }
    ok = p.propose_mapping()
    assert not ok and p.sm.state == State.HALT
    p.sm.resume()
    result = p.continue_run()  # Must return promptly without hanging
    assert p.sm.state == State.HALT, "resume with no new data must re-halt, not silently proceed or loop forever"

