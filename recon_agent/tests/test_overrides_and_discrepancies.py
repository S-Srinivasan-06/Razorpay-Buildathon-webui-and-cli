import pytest
from app.core import llm_client
from app.core.contracts import HypothesisCategory


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))


def test_t6_no_false_counterparty_mismatch(tmp_path):
    from app.data.generator import generate
    generate(tmp_path)
    from app.pipeline import Pipeline
    p = Pipeline("t6-test", auto_ack=True)
    p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"], tmp_path / "ground_truth.jsonl")
    
    # Check that ORD_6 (rid 6) and ORD_7 (rid 7) are not classified as COUNTERPARTY_MISMATCH
    split_items = [i for i in p.queue if i["rec"].side == "L" and i["rec"].rid in (6, 7)]
    for item in split_items:
        assert item["rec"].reason != HypothesisCategory.COUNTERPARTY_MISMATCH, \
            f"Split leg rid {item['rec'].rid} was falsely classified as COUNTERPARTY_MISMATCH"


def test_t4_t5_override_updates_report_and_preserves_disagreement(tmp_path):
    from fastapi.testclient import TestClient
    from app.server.main import app, SESSIONS
    from app.data.generator import generate
    
    generate(tmp_path)
    client = TestClient(app)
    
    # Create session
    resp = client.post("/api/sessions")
    assert resp.status_code == 200
    sid = resp.json()["session_id"]
    
    from app.pipeline import Pipeline
    p = Pipeline(sid, auto_ack=True)
    p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"], tmp_path / "ground_truth.jsonl")
    SESSIONS[sid]["pipe"] = p
    
    # U2 Check initial sum invariant
    assert p.final.auto_resolved_count + p.final.escalated_count + p.final.unresolved_count == p.final.honest_exception_count
    
    initial_auto_resolved = p.final.auto_resolved_count
    initial_escalated = p.final.escalated_count
    initial_unresolved = p.final.unresolved_count
    
    # Pick first pending exception
    target_item = next(i for i in p.queue if i["action"] != "auto_resolve")
    target_rid = target_item["rec"].rid
    prior_action = target_item["action"]
    
    # 1. Perform user override to approve (mark_resolved)
    override_resp = client.post(f"/api/sessions/{sid}/exceptions/{target_rid}/action",
                                json={"action": "approve", "note": "verified by human auditor"})
    assert override_resp.status_code == 200
    assert override_resp.json()["ok"] is True
    
    # T4 Check: report counts updated and U2 sum invariant holds
    assert p.final.auto_resolved_count == initial_auto_resolved + 1
    assert p.final.auto_resolved_count + p.final.escalated_count + p.final.unresolved_count == p.final.honest_exception_count
    
    # T5 Check: disagreement preserved with prior proposal details
    assert len(p.final.llm_user_disagreements) > 0
    disagreement = p.final.llm_user_disagreements[-1]
    assert disagreement["rid"] == target_rid
    assert disagreement["system_proposal"]["action"] == prior_action
    assert disagreement["user_decision"]["action"] == "mark_resolved"
    assert disagreement["user_decision"]["note"] == "verified by human auditor"
    
    # 2. Perform user override to escalate another item
    target_item2 = next(i for i in p.queue if i["rec"].rid != target_rid and i["action"] != "auto_resolve")
    target_rid2 = target_item2["rec"].rid
    override_resp2 = client.post(f"/api/sessions/{sid}/exceptions/{target_rid2}/action",
                                 json={"action": "escalate", "note": "escalated to finance ops"})
    assert override_resp2.status_code == 200
    
    # U2 Check: sum invariant strictly holds after escalation as well
    assert p.final.escalated_count >= 1
    assert p.final.auto_resolved_count + p.final.escalated_count + p.final.unresolved_count == p.final.honest_exception_count
