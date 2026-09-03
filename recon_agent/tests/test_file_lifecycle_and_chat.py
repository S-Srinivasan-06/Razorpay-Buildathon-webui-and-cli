"""Unit & Integration Tests for File Lifecycle Management and Chat Grounding.

Verifies:
  1. Assistant refuses to chat if no files are ingested in the active session.
  2. Deleted files/tables are immediately purged from grounded context to prevent hallucinations.
  3. REST endpoints correctly track file uploads, listings, deletions, and chat gating.
"""

import io
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.engine.chatbot import build_grounded_context, ReconChatSession
from app.pipeline import Pipeline
from app.server.main import app, CHAT_SESSIONS, SESSIONS


def test_chat_refuses_without_files() -> None:
    """Verify that ReconChatSession refuses to query LLM when no active files are loaded."""
    session = ReconChatSession("test_sid", pipe=None)
    res = session.chat("What was the total volume?")
    assert res["ok"] is False
    assert "No active files loaded" in res["error"]

    empty_pipe = Pipeline("empty_sid", auto_ack=True)
    session.set_pipe(empty_pipe)
    res2 = session.chat("Explain ORD_1")
    assert res2["ok"] is False
    assert "No active files loaded" in res2["error"]


def test_deleted_file_excluded_from_context(tmp_path: Path) -> None:
    """Verify that purged tables are immediately excluded from the grounded context string."""
    p1 = tmp_path / "payments.csv"
    p1.write_text("order_id,amount,date\nORD_1,1000.00,2026-03-01\nORD_2,2000.00,2026-03-01\n", encoding="utf-8")

    p2 = tmp_path / "bank.csv"
    p2.write_text("utr,credit,date\nORD_1,1000.00,2026-03-02\nORD_2,1952.80,2026-03-02\n", encoding="utf-8")

    pipe = Pipeline("test_del", auto_ack=True)
    pipe.run([p1, p2])

    ctx_before = build_grounded_context(pipe)
    assert "payments" in ctx_before
    assert "bank" in ctx_before
    assert "ORD_1" in ctx_before

    # Delete payments table
    del pipe.tables["payments"]
    ctx_after = build_grounded_context(pipe)
    assert "Table 'payments'" not in ctx_after
    assert "Table 'bank'" in ctx_after


def test_server_file_lifecycle_and_chat_endpoints() -> None:
    """Verify multipart upload, file listing, file deletion, and chat rejection REST endpoints."""
    client = TestClient(app)

    # 1. Create session
    resp = client.post("/api/sessions")
    assert resp.status_code == 200
    sid = resp.json()["session_id"]

    # 2. Chat before upload must fail
    chat_resp = client.post(f"/api/sessions/{sid}/chat", json={"message": "What is the status?"})
    assert chat_resp.status_code == 200
    assert chat_resp.json()["ok"] is False
    assert "No active files loaded" in chat_resp.json()["error"]

    # 3. Upload files
    f1 = ("payments.csv", io.BytesIO(b"order_id,amount,date\nORD_1,1000.00,2026-03-01\n"), "text/csv")
    f2 = ("bank.csv", io.BytesIO(b"utr,credit,date\nORD_1,1000.00,2026-03-02\n"), "text/csv")
    upload_resp = client.post(f"/api/sessions/{sid}/files", files=[("files", f1), ("files", f2)])
    assert upload_resp.status_code == 200
    assert "payments.csv" in upload_resp.json()["added"]

    # 4. List files
    list_resp = client.get(f"/api/sessions/{sid}/files")
    assert list_resp.status_code == 200
    file_names = [f["filename"] for f in list_resp.json()["files"]]
    assert "payments.csv" in file_names
    assert "bank.csv" in file_names

    # 5. Delete one file
    del_resp = client.delete(f"/api/sessions/{sid}/files/payments.csv")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] == "payments.csv"
    assert "payments.csv" not in del_resp.json()["remaining_files"]
    assert "bank.csv" in del_resp.json()["remaining_files"]


def test_chat_answers_standard_deviation_and_statistics(tmp_path: Path) -> None:
    """Verify that the assistant calculates and provides standard deviation metrics without refusal."""
    p1 = tmp_path / "merchant_sales.csv"
    p1.write_text(
        "order_id,gross_amount,date\n"
        "ORD_1,1000.00,2026-03-01\n"
        "ORD_2,2000.00,2026-03-01\n"
        "ORD_3,3000.00,2026-03-01\n"
        "ORD_4,4000.00,2026-03-01\n",
        encoding="utf-8",
    )
    p2 = tmp_path / "bank_statement.csv"
    p2.write_text(
        "utr,credit_amount,date\n"
        "ORD_1,980.00,2026-03-02\n"
        "ORD_2,1960.00,2026-03-02\n"
        "ORD_3,2940.00,2026-03-02\n"
        "ORD_4,3920.00,2026-03-02\n",
        encoding="utf-8",
    )

    pipe = Pipeline("test_stats_chat", auto_ack=True)
    pipe.ingest([p1, p2])

    ctx = build_grounded_context(pipe)
    assert "[Active Statistical Profiles & Standard Deviations across Datasets]:" in ctx
    assert "Average Standard Deviation" in ctx
    assert "gross_amount" in ctx
    assert "credit_amount" in ctx

    session = ReconChatSession("test_stats_chat", pipe=pipe)
    resp = session.chat("What is the average standard deviation across the datasets?")
    assert resp["ok"] is True
    assert "standard deviation" in resp["response"].lower()
    assert "not available" not in resp["response"].lower()
    assert "1,290.99" in resp["response"] or "1290" in resp["response"] or "Average Standard Deviation" in resp["response"]


