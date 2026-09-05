"""Comprehensive Test Suite for Bug Audit Remediation.

Tests all fixes identified in the full codebase audit:
1. row_idx threading across fee.py, pipeline.py, and api_v2.py (authoritative _rid positioning).
2. Multi-way chaining endpoint POST /sessions/{sid}/multiway-run with independent cash position invariant and journal export.
3. Fresh pipeline instantiation on chat-triggered re-run from ARCHIVED state.
4. Multi-action confirmation gate queue (confirming all queued actions on YES).
5. Low-priority catch-all policy injection (preserving specific segment rules).
6. Rule compiler range anchoring for out-of-order keywords ("last 20%... first 80%").
7. Variable GST calculation in double-entry journal entries (no hardcoded 18% split).
8. Extended load_sample endpoint supporting all 4 bundled dataset suites.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import pandas as pd

from app.core.contracts import FeeTaxRule, SegmentMatcher, CashPosition, MultiWayReport
from app.engine.fee import compute_deduction_breakdown, matches_rule
from app.engine.journal import generate_journal_entries, export_journal_entries_csv
from app.engine.multiway import detect_table_roles, run_multiway_chaining
from app.engine.rule_compiler import compile_rules_from_text
from app.pipeline import Pipeline
from app.server.main import app
from app.server.api_v2 import V2_SESSIONS, CHAT_SESSIONS
from app.core.states import State


client = TestClient(app)


# -----------------------------------------------------------------------------
# 1. row_idx Threading and Authoritative _rid Position
# -----------------------------------------------------------------------------
def test_row_idx_authoritative_rid_segment_matching() -> None:
    """Ensure row_range_pct derives position from _rid across pipeline stages."""
    rule_first_40 = FeeTaxRule(
        rule_id="r_tier1",
        label="Tier 1 (First 40%)",
        matcher=SegmentMatcher(kind="row_range_pct", start_pct=0.0, end_pct=40.0),
        fee_rate=0.02,
        gst_rate=0.18,
        priority=1,
    )
    rule_rest_60 = FeeTaxRule(
        rule_id="r_tier2",
        label="Tier 2 (Rest 60%)",
        matcher=SegmentMatcher(kind="row_range_pct", start_pct=40.0, end_pct=100.0),
        fee_rate=0.015,
        gst_rate=0.12,
        priority=2,
    )
    rules = [rule_first_40, rule_rest_60]

    # Row 39 (_rid=40 out of 100) -> 39% position -> Tier 1
    row_39 = {"_rid": 40, "amount": 1000.0, "order_id": "ORD_39"}
    # Row 41 (_rid=42 out of 100) -> 41% position -> Tier 2
    row_41 = {"_rid": 42, "amount": 1000.0, "order_id": "ORD_41"}

    # Even when caller passes row_idx=0 (simulating previous bug), _rid must win!
    b39 = compute_deduction_breakdown(1000.0, rules=rules, row=row_39, total_rows=100, row_idx=0)
    b41 = compute_deduction_breakdown(1000.0, rules=rules, row=row_41, total_rows=100, row_idx=0)

    assert b39["rule_label"] == "Tier 1 (First 40%)"
    assert b41["rule_label"] == "Tier 2 (Rest 60%)"
    assert b39["gateway_fee"] == 20.0
    assert b41["gateway_fee"] == 15.0
    assert b39["gst"] == 3.6
    assert b41["gst"] == 1.8


# -----------------------------------------------------------------------------
# 2. Multi-Way Chaining and Independent Cash Position Invariant
# -----------------------------------------------------------------------------
def test_multiway_chaining_and_controller_invariant() -> None:
    """Test full multiway reconciliation across 3-file benchmark datasets."""
    r = client.post("/api/v2/sessions")
    sid = r.json()["session_id"]

    # Load 3-file benchmark
    r_load = client.post(f"/api/v2/sessions/{sid}/load_sample?dataset=benchmark_3file")
    assert r_load.status_code == 200
    assert len(r_load.json()["files"]) == 3
    assert "Run Multi-Way Chaining" in (r_load.json().get("advisory") or "")

    # Execute multiway run
    r_run = client.post(f"/api/v2/sessions/{sid}/multiway-run")
    assert r_run.status_code == 200
    rpt = r_run.json()["report"]
    assert len(rpt["legs"]) == 2
    assert rpt["consolidated_match_rate"] > 0.0
    assert rpt["total_orders_evaluated"] > 0

    # Verify Cash Position metrics
    cp = rpt["cash_position"]
    assert cp["gross_sales"] > 0.0
    assert cp["settled_in_bank"] > 0.0
    assert cp["in_transit_total"] >= 0.0
    assert cp["projected_closing"] > 0.0

    # Retrieve via GET endpoint
    r_get = client.get(f"/api/v2/sessions/{sid}/multiway")
    assert r_get.status_code == 200
    assert r_get.json()["report"]["total_orders_evaluated"] == rpt["total_orders_evaluated"]

    # Export Journal CSV
    r_csv = client.get(f"/api/v2/sessions/{sid}/export/journal.csv")
    assert r_csv.status_code == 200
    assert "JE Number,Posting Date,Category" in r_csv.text
    assert "Bank Operating Account" in r_csv.text


# -----------------------------------------------------------------------------
# 3. Chat-Triggered Re-Run on ARCHIVED State Recreates Pipeline
# -----------------------------------------------------------------------------
def test_chat_rerun_on_archived_recreates_fresh_pipeline() -> None:
    """Ensure execute_agent_action RUN_RECONCILIATION on ARCHIVED state reconstructs Pipeline."""
    r = client.post("/api/v2/sessions")
    sid = r.json()["session_id"]

    client.post(f"/api/v2/sessions/{sid}/load_sample?dataset=basic")
    pipe = V2_SESSIONS[sid]["pipe"]

    # Simulate completed first run
    pipe.sm.enter(State.ARCHIVED)
    assert pipe.sm.state == State.ARCHIVED

    # Trigger re-run via chat action dispatcher
    from app.engine.actions import execute_agent_action
    res = execute_agent_action(sid, pipe, "RUN_RECONCILIATION", {}, source="chat")
    assert res["ok"] is True
    assert res["result"]["status"] == "started"

    # Verify session now holds a fresh Pipeline instance (not the stale ARCHIVED one)
    new_pipe = V2_SESSIONS[sid]["pipe"]
    assert new_pipe is not pipe
    assert new_pipe.sm.state != State.ARCHIVED


# -----------------------------------------------------------------------------
# 4. Multi-Action Confirmation Queue
# -----------------------------------------------------------------------------
def test_multi_action_confirmation_queue() -> None:
    """Ensure multiple state-changing actions are queued and all confirmed on YES."""
    r = client.post("/api/v2/sessions")
    sid = r.json()["session_id"]
    client.post(f"/api/v2/sessions/{sid}/load_sample?dataset=basic")

    chat_sess = CHAT_SESSIONS[sid]
    # Queue two pending actions manually
    act1 = {"kind": "SET_POLICY", "payload": {"fee_rate": 0.015, "gst_rate": 0.18, "tolerance": 0.02}, "token": "tok1"}
    act2 = {"kind": "SET_TOLERANCE", "payload": {"abs_tol": 0.05, "pct_tol": 0.02, "mode": "greater"}, "token": "tok2"}
    chat_sess.pending_actions_queue = [act1, act2]
    chat_sess.pending_action = act2

    # Send YES to confirm all
    r_confirm = client.post(f"/api/v2/sessions/{sid}/chat", json={"message": "YES"})
    assert r_confirm.status_code == 200
    reply = r_confirm.json()["response"]
    assert "SET_POLICY" in reply
    assert "SET_TOLERANCE" in reply
    assert "confirmed and executed successfully" in reply

    # Verify policy and tolerance both updated
    pipe = V2_SESSIONS[sid]["pipe"]
    assert pipe.cfg.get("tolerance_mode") == "greater"
    assert pipe.cfg.get("tolerance_abs") == 0.05


# -----------------------------------------------------------------------------
# 5. Policy Preserves Segment Rules
# -----------------------------------------------------------------------------
def test_set_policy_preserves_specific_segment_rules() -> None:
    """Ensure set_policy injects a priority-999 catch-all and preserves custom segment rules."""
    pipe = Pipeline("test_policy_preserve", auto_ack=True)
    custom_rule = FeeTaxRule(
        rule_id="r_custom",
        label="Custom Electronics",
        matcher=SegmentMatcher(kind="column_equals", column="category", value="electronics"),
        fee_rate=0.018,
        gst_rate=0.12,
        priority=1,
    )
    pipe.set_rules([custom_rule])
    assert len(pipe.rules) == 1

    # Apply flat policy
    pipe.set_policy(fee_rate=0.02, gst_rate=0.18, tolerance=0.01)

    # Custom rule must still be present with priority 1; policy rule appended at priority 999
    assert len(pipe.rules) == 2
    assert pipe.rules[0].rule_id == "r_custom"
    assert pipe.rules[0].priority == 1
    assert pipe.rules[1].matcher.kind == "all"
    assert pipe.rules[1].priority == 999


# -----------------------------------------------------------------------------
# 6. Rule Compiler Range Anchoring for Out-of-Order Keywords
# -----------------------------------------------------------------------------
def test_rule_compiler_range_anchoring_out_of_order() -> None:
    """Ensure 'last 20%' is anchored to 80%-100% and 'first 80%' to 0%-80%."""
    # Natural language with tail segment mentioned
    text = "first 80% rows have 1.5% fee and 18% gst, last 20% rows have 2.0% fee and 18% gst"
    res = compile_rules_from_text(text)
    assert not res.has_ambiguity
    assert len(res.rules) == 2
    r1, r2 = res.rules[0], res.rules[1]

    assert r1.matcher.start_pct == 0.0
    assert r1.matcher.end_pct == 80.0
    assert r2.matcher.start_pct == 80.0
    assert r2.matcher.end_pct == 100.0


# -----------------------------------------------------------------------------
# 7. Variable GST Split in Journal Entries
# -----------------------------------------------------------------------------
def test_journal_variable_gst_split_not_hardcoded_18() -> None:
    """Ensure generate_journal_entries uses actual breakdown totals without assuming /1.18."""
    # Matched pair with 12% GST instead of 18%
    matched_pairs = [
        {"gateway_fee": 100.0, "gst": 12.0, "order_id": "ORD_1"},
        {"gateway_fee": 50.0, "gst": 6.0, "order_id": "ORD_2"},
    ]
    totals = {
        "matched_value": 10000.0,
        "net": 9832.0,
        "fees": 168.0,  # 150 base fee + 18 GST (12% effective)
    }
    entries = generate_journal_entries("sess_test", matched_pairs=matched_pairs, exceptions=[], totals=totals)
    fee_entry = next((e for e in entries if e.leg == "SETTLEMENT_FEE"), None)
    assert fee_entry is not None

    fee_line = next(l for l in fee_entry.lines if "Processing Fee" in l.account)
    gst_line = next(l for l in fee_entry.lines if "GST Input Tax Credit" in l.account)

    assert fee_line.debit == 150.0  # Exactly sum of gateway_fee
    assert gst_line.debit == 18.0   # Exactly sum of gst (not 168 - (168/1.18))
    assert abs(fee_entry.total_debit - fee_entry.total_credit) < 0.01


# -----------------------------------------------------------------------------
# 8. Extended load_sample Dataset Options
# -----------------------------------------------------------------------------
def test_load_sample_enterprise_ecosystem_loads_5_tables() -> None:
    """Ensure load_sample with enterprise_ecosystem ingests all 5 enterprise tables."""
    r = client.post("/api/v2/sessions")
    sid = r.json()["session_id"]

    r_load = client.post(f"/api/v2/sessions/{sid}/load_sample?dataset=enterprise_ecosystem")
    assert r_load.status_code == 200
    files = r_load.json()["files"]
    assert len(files) == 5

    table_names = {f["table"] for f in files}
    assert "zomato_orders" in table_names
    assert "flipkart_orders" in table_names
    assert "razorpay_ledger" in table_names
    assert "icici_bank" in table_names
    assert "hdfc_bank" in table_names


# -----------------------------------------------------------------------------
# 9. Multi-Way Endpoint Resilience (No False 404s, Clean 400 Bad Requests)
# -----------------------------------------------------------------------------
def test_multiway_endpoints_resilience_and_no_404_session_wiping() -> None:
    """Verify multiway endpoints return 200/400 (never 404 for valid sessions), preventing frontend session wiping."""
    r = client.post("/api/v2/sessions")
    sid = r.json()["session_id"]

    # 1. GET multiway before any run should return 200 with report: None (NOT 404)
    r_empty_get = client.get(f"/api/v2/sessions/{sid}/multiway")
    assert r_empty_get.status_code == 200
    assert r_empty_get.json()["ok"] is False
    assert r_empty_get.json()["report"] is None

    # 2. Export journal before run should return 400 Bad Request (NOT 404)
    r_empty_csv = client.get(f"/api/v2/sessions/{sid}/export/journal.csv")
    assert r_empty_csv.status_code == 400
    assert "no multiway journal" in r_empty_csv.json()["detail"].lower()

    # 3. POST multiway-run with 0 tables should return 400 Bad Request (NOT 404)
    r_empty_run = client.post(f"/api/v2/sessions/{sid}/multiway-run")
    assert r_empty_run.status_code == 400
    assert "requires 3+ tables" in r_empty_run.json()["detail"]

    # 4. POST multiway-run with only 2 tables should return 400 Bad Request (NOT 404)
    client.post(f"/api/v2/sessions/{sid}/load_sample?dataset=basic")
    r_2table_run = client.post(f"/api/v2/sessions/{sid}/multiway-run")
    assert r_2table_run.status_code == 400
    assert "requires 3+ tables" in r_2table_run.json()["detail"]

    # 5. POST multiway-run with 3 tables succeeds with 200 OK
    client.post(f"/api/v2/sessions/{sid}/load_sample?dataset=benchmark_3file")
    r_valid_run = client.post(f"/api/v2/sessions/{sid}/multiway-run")
    assert r_valid_run.status_code == 200
    assert r_valid_run.json()["ok"] is True
    assert "report" in r_valid_run.json()

    # 6. GET multiway after run returns 200 OK with report
    r_after_get = client.get(f"/api/v2/sessions/{sid}/multiway")
    assert r_after_get.status_code == 200
    assert r_after_get.json()["ok"] is True
    assert r_after_get.json()["report"] is not None

    # 7. Genuinely missing session ID still returns 404 "session not found"
    r_missing_sess = client.get("/api/v2/sessions/nonexistent/multiway")
    assert r_missing_sess.status_code == 404
    assert r_missing_sess.json()["detail"] == "session not found"


# -----------------------------------------------------------------------------
# 9. AI Direct Tax Rule Editing on Vague Remarks & No LLM Parsing
# -----------------------------------------------------------------------------
def test_ai_direct_tax_rule_editing_on_vague_remark(monkeypatch) -> None:
    """Ensure AI directly edits tax rules on vague remarks without confirmation gates."""
    from app.core import llm_client
    from app.engine.chatbot import ReconChatSession, extract_tax_remark
    from app.core.audit import audit_for

    # Verify extract_tax_remark catches various vague and explicit tax remarks
    assert extract_tax_remark("the tax is 5%") == 0.05
    assert extract_tax_remark("taxes are 5%") == 0.05
    assert extract_tax_remark("tax of 12%") == 0.12
    assert extract_tax_remark("what if the gst is 18%?") == 0.18
    assert extract_tax_remark("tax: 5%") == 0.05
    assert extract_tax_remark("assume 5% tax deduction") == 0.05

    sid = f"test_tax_edit_{uuid.uuid4().hex[:6]}" if "uuid" in dir() else "test_tax_edit_ai_1"
    import uuid
    sid = f"test_tax_edit_{uuid.uuid4().hex[:6]}"

    pipe = Pipeline(sid, auto_ack=True)
    pipe.tables = {
        "payments": [{"order_id": "ORD_1", "amount": 1000.0}],
        "bank": [{"utr": "ORD_1", "credit": 950.0}],
    }
    pipe.cfg = {"tolerance_abs": 0.01, "left_table": "payments", "right_table": "bank"}
    V2_SESSIONS[sid] = {"pipe": pipe, "policy": {}, "files": {}}

    # Mock conversational_chat so test runs deterministically offline
    monkeypatch.setattr(
        llm_client,
        "conversational_chat",
        lambda messages, system_instruction, timeout=25.0: (
            "I have updated the tax rate to 5.0% for your reconciliation session.",
            0.0001,
        ),
    )

    chat_session = ReconChatSession(sid, pipe)

    # 1. Vague remark: "the tax is 5%"
    res = chat_session.chat("the tax is 5%")
    assert res["ok"] is True
    # Tax rule should be immediately updated in schedule and rules without asking for YES confirmation
    assert pipe.schedule.gst_rate == 0.05
    assert pipe.cfg["gst_rate"] == 0.05
    assert pipe.cfg["tax_rate"] == 0.05
    assert len(pipe.rules) >= 1
    assert pipe.rules[0].gst_rate == 0.05

    # Confirmation gate was NOT triggered
    assert chat_session.pending_action is None
    assert "Reply YES" not in res["response"]

    # Audit trail contains TAX_RULE_UPDATED_BY_AI event
    audit_events = [e["payload"] for e in audit_for(sid) if e.get("payload", {}).get("event") == "TAX_RULE_UPDATED_BY_AI"]
    assert len(audit_events) >= 1
    assert audit_events[-1]["gst_rate"] == 0.05

    # 2. Subsequent vague remark: "what if tax is 12%?"
    monkeypatch.setattr(
        llm_client,
        "conversational_chat",
        lambda messages, system_instruction, timeout=25.0: (
            "Tax rule has been modified to 12.0%.",
            0.0001,
        ),
    )
    res2 = chat_session.chat("what if tax is 12%?")
    assert res2["ok"] is True
    assert pipe.schedule.gst_rate == 0.12
    assert pipe.rules[0].gst_rate == 0.12
    assert pipe.cfg["gst_rate"] == 0.12


def test_no_llm_output_parsing_verbatim(monkeypatch) -> None:
    """Ensure LLM response is returned completely verbatim without regex or tag parsing."""
    from app.core import llm_client
    from app.engine.chatbot import ReconChatSession
    import uuid

    sid = f"test_raw_{uuid.uuid4().hex[:6]}"
    pipe = Pipeline(sid, auto_ack=True)
    pipe.tables = {"tbl": [{"id": 1, "amount": 500}]}
    pipe.cfg = {"tolerance_abs": 0.01}

    raw_complex_response = (
        "Here is the detailed reconciliation breakdown:\n\n"
        "```json\n"
        '{"status": "matched", "tax_impact": 0.05}\n'
        "```\n\n"
        "Special chars & formatting: <note>Check variance</note> | $1,234.56 | 99.8% match rate."
    )

    monkeypatch.setattr(
        llm_client,
        "conversational_chat",
        lambda messages, system_instruction, timeout=25.0: (raw_complex_response, 0.0002),
    )

    session = ReconChatSession(sid, pipe)
    res = session.chat("Show me the report details")
    assert res["ok"] is True
    # Response matches raw LLM response completely without any stripping or parsing
    assert res["response"] == raw_complex_response


def test_csv_export_and_results_endpoint_include_all_attributes() -> None:
    """Verify that downloadable CSV export and results endpoint include every attribute from both datasets."""
    import csv
    import io
    import uuid
    from app.core.contracts import MatchedRecord, UnmatchedRecord, HypothesisCategory, ExecutionResult, VarianceMetrics
    from app.engine.report import export_reconciliation_csv_string
    from app.server.api_v2 import V2_SESSIONS

    sid = f"test_attr_{uuid.uuid4().hex[:6]}"
    pipe = Pipeline(sid, auto_ack=True)
    pipe.cfg = {
        "left_table": "payments",
        "right_table": "bank",
        "left_key": "order_id",
        "right_key": "utr",
        "left_amount": "amount",
        "right_amount": "credit",
        "tolerance_abs": 0.01,
    }

    # Populate multiple attributes across left and right tables
    pipe.tables = {
        "payments": [
            {
                "_rid": 1,
                "order_id": "ORD_101",
                "amount": 1500.0,
                "date": "2026-03-01",
                "customer_id": "CUST_99",
                "customer_email": "user@example.com",
                "payment_method": "upi",
                "custom_tag": "vip_sale",
            },
            {
                "_rid": 2,
                "order_id": "ORD_102",
                "amount": 2500.0,
                "date": "2026-03-02",
                "customer_id": "CUST_42",
                "customer_email": "corp@corp.in",
                "payment_method": "netbanking",
                "custom_tag": "b2b",
            },
        ],
        "bank": [
            {
                "_rid": 1,
                "utr": "ORD_101",
                "credit": 1500.0,
                "date": "2026-03-01",
                "description": "UPI INWARD / ORD_101",
                "bank_account": "HDFC_001",
                "channel": "IMPS",
            }
        ],
    }

    # Setup matched result
    matched_rec = MatchedRecord(
        l_rid=1,
        r_rid=1,
        composite_score=0.99,
        components={"exact_key": 1.0},
        policy_version="v0",
    )
    pipe.exec_res = ExecutionResult(
        matched=[matched_rec],
        unmatched=[],
        duplicates=[],
        splits=[],
        variance=VarianceMetrics(abs_sum=0.0, signed_sum=0.0, per_record=[]),
    )

    # Setup exception queue item
    exc_rec = UnmatchedRecord(
        rid=2,
        side="L",
        ref="ORD_102",
        delta=2500.0,
        reason=HypothesisCategory.UNCLASSIFIED,
        explanation="Unmatched order ORD_102",
    )
    pipe.queue = [
        {
            "rec": exc_rec,
            "action": "mark_pending",
            "conf": 0.35,
            "pieces": [],
            "record_data": pipe.tables["payments"][1],
        }
    ]

    # Register in active session storage
    V2_SESSIONS[sid] = {"pipe": pipe, "files": []}

    # 1. Test CSV export string contains all attribute columns
    csv_str = export_reconciliation_csv_string(pipe)
    reader = csv.reader(io.StringIO(csv_str))
    rows = list(reader)
    header = rows[0]

    # Verify all left attributes prefixed with payments_ are present
    expected_left = [
        "payments_order_id",
        "payments_amount",
        "payments_date",
        "payments_customer_id",
        "payments_customer_email",
        "payments_payment_method",
        "payments_custom_tag",
    ]
    for col in expected_left:
        assert col in header, f"Missing expected left column in CSV: {col}"

    # Verify all right attributes prefixed with bank_ are present
    expected_right = [
        "bank_utr",
        "bank_credit",
        "bank_date",
        "bank_description",
        "bank_bank_account",
        "bank_channel",
    ]
    for col in expected_right:
        assert col in header, f"Missing expected right column in CSV: {col}"

    # Verify matched data row has all attribute values
    matched_row = rows[1]
    header_idx = {name: i for i, name in enumerate(header)}
    assert matched_row[header_idx["payments_customer_id"]] == "CUST_99"
    assert matched_row[header_idx["payments_customer_email"]] == "user@example.com"
    assert matched_row[header_idx["payments_custom_tag"]] == "vip_sale"
    assert matched_row[header_idx["bank_bank_account"]] == "HDFC_001"
    assert matched_row[header_idx["bank_channel"]] == "IMPS"

    # Verify exception data row has source attributes
    exc_row = rows[2]
    assert exc_row[header_idx["payments_customer_id"]] == "CUST_42"
    assert exc_row[header_idx["payments_customer_email"]] == "corp@corp.in"
    assert exc_row[header_idx["payments_custom_tag"]] == "b2b"

    # 2. Test /api/v2/sessions/{sid}/results endpoint payload
    resp = client.get(f"/api/v2/sessions/{sid}/results")
    assert resp.status_code == 200
    data = resp.json()

    assert data["left_table"] == "payments"
    assert data["right_table"] == "bank"
    for col in ["order_id", "amount", "date", "customer_id", "customer_email", "payment_method", "custom_tag"]:
        assert col in data["left_columns"]
    for col in ["utr", "credit", "date", "description", "bank_account", "channel"]:
        assert col in data["right_columns"]

    # Verify enriched matched pair carries full l_data and r_data dictionaries
    match_payload = data["matched"][0]
    assert match_payload["l_data"]["customer_email"] == "user@example.com"
    assert match_payload["l_data"]["custom_tag"] == "vip_sale"
    assert match_payload["r_data"]["bank_account"] == "HDFC_001"
    assert match_payload["r_data"]["channel"] == "IMPS"



