def test_halt_then_resume_completes_run(tmp_path, monkeypatch):
    from app.core import llm_client
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    from app.data.generator import generate
    generate(tmp_path)
    from app.pipeline import Pipeline
    p = Pipeline("resume-test", auto_ack=False)     # interactive mode, no auto-ack
    result = p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"], tmp_path / "ground_truth.jsonl")
    while result is None and p.sm.state.name == "HALT":
        p.sm.resume()
        result = p.continue_run()
    assert result is not None and result.match_rate > 0
