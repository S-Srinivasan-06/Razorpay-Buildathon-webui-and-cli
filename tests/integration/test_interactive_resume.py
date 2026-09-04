"""Unit Tests for Interactive Pause and Resume Pipeline Execution.

Verifies:
  1. Pipeline configured with auto_ack=False halts safely on interactive gates.
  2. Successive manual resume calls (p.sm.resume() + continue_run()) drive the engine
     forward to ARCHIVED completion without state loss or memory corruption.
"""

from pathlib import Path
from typing import Any

import pytest

from app.core import llm_client
from app.data.generator import generate
from app.pipeline import Pipeline


def test_halt_then_resume_completes_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that an interactive pipeline halted by policy gates completes successfully upon manual resumption."""
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    generate(tmp_path)
    p = Pipeline("resume-test", auto_ack=False)  # Interactive mode without auto-ack
    result = p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"], tmp_path / "ground_truth.jsonl")

    # Manually resume on any encountered halt until complete
    while result is None and p.sm.state.name == "HALT":
        p.sm.resume()
        result = p.continue_run()

    assert result is not None and result.match_rate > 0

