from app.core.states import State


def test_low_confidence_mapping_rehalts_on_resume_not_bypassed(tmp_path, monkeypatch):
    """V1: resuming a below-floor-confidence halt must re-check, not silently
    advance to POLICY_GENERATED with the same bad mapping."""
    from app.core import llm_client
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    from app.pipeline import Pipeline
    p = Pipeline("v1-test", auto_ack=False)
    # two tables with only marginal key overlap -> low mapping confidence
    p.tables = {
        "left": [{"_rid": 1, "id": "X1", "amt": 10.0}, {"_rid": 2, "id": "X2", "amt": 20.0}],
        "right": [{"_rid": 1, "ref": "Z9", "val": 999.0}],
    }
    from app.core.contracts import ColumnProfile
    p.profiles = {
        "left": [ColumnProfile(name="id", dtype="text", numeric_ratio=0, date_ratio=0,
                               cardinality=1.0, null_rate=0, min_len=2, max_len=2,
                               sample_values=["X1"], pii_likelihood=0)],
        "right": [ColumnProfile(name="ref", dtype="text", numeric_ratio=0, date_ratio=0,
                                cardinality=1.0, null_rate=0, min_len=2, max_len=2,
                                sample_values=["Z9"], pii_likelihood=0)],
    }
    ok = p.propose_mapping()
    if ok:
        ok = p.validate_mapping()
    assert p.sm.state == State.HALT, "expected halt on low-confidence mapping"
    p.sm.resume()
    result = p.continue_run()
    # must NOT have silently advanced to POLICY_GENERATED/DRY_RUN/etc with bad data;
    # must re-halt on the same unresolved condition
    assert p.sm.state == State.HALT, "resume must re-check, not bypass, the confidence gate"


def test_no_linkable_columns_rehalts_not_infinite_loops(tmp_path, monkeypatch):
    """V2: same guarantee for the no-linkable-columns halt."""
    from app.core import llm_client
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    from app.pipeline import Pipeline
    p = Pipeline("v2-test", auto_ack=False)
    p.tables = {"left": [{"_rid": 1, "a": "foo"}], "right": [{"_rid": 1, "b": "bar"}]}
    from app.core.contracts import ColumnProfile
    p.profiles = {
        "left": [ColumnProfile(name="a", dtype="text", numeric_ratio=0, date_ratio=0,
                               cardinality=1.0, null_rate=0, min_len=3, max_len=3,
                               sample_values=["foo"], pii_likelihood=0)],
        "right": [ColumnProfile(name="b", dtype="text", numeric_ratio=0, date_ratio=0,
                                cardinality=1.0, null_rate=0, min_len=3, max_len=3,
                                sample_values=["bar"], pii_likelihood=0)],
    }
    ok = p.propose_mapping()
    assert not ok and p.sm.state == State.HALT
    p.sm.resume()
    result = p.continue_run()   # must return promptly, not hang/loop
    assert p.sm.state == State.HALT, "resume with no new data must re-halt, not silently proceed or loop forever"
