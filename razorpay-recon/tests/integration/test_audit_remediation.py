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

