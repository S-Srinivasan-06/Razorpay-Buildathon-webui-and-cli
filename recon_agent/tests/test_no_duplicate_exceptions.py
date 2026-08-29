def test_no_duplicate_exception_rids(tmp_path, monkeypatch):
    from app.core import llm_client
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    from app.data.generator import generate
    generate(tmp_path)
    from app.pipeline import Pipeline
    p = Pipeline("dedupe-test", auto_ack=True)
    p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"], tmp_path / "ground_truth.jsonl")
    seen = [(i["rec"].side, i["rec"].rid) for i in p.queue]
    assert len(seen) == len(set(seen)), f"duplicate exception entries: {seen}"
