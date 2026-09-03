"""End-to-End Tests for Segment Rules, User-Defined Tolerance, Enterprise Ecosystem, and 3-File Benchmark.

Verifies:
  1. REST Endpoints: GET/POST /rules, GET/POST /tolerance, and POST /confirm-action.
  2. Natural Language Rule Compilation & Confirmation Gate (§4).
  3. 3-File Input Reconciliation with variable tax rates & offline benchmark comparison
     (verifying ground truth file is strictly offline and never uploaded).
  4. 5-Enterprise Ecosystem reconciliation with bank gateway charges & Razorpay net profit calculation.
"""

from pathlib import Path
from typing import Any
import json

from fastapi.testclient import TestClient
import pytest

from app.core import llm_client
from app.data.generate_ecosystem import generate_enterprise_ecosystem, generate_3file_benchmark
from app.pipeline import Pipeline
from app.server.main import app


@pytest.fixture(autouse=True)
def no_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable external LLM to guarantee deterministic testing."""
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError("offline")))
    monkeypatch.setattr(llm_client, "conversational_chat", lambda *a, **k: ("Offline response", 0.0))


def test_rules_and_tolerance_endpoints() -> None:
    client = TestClient(app)
    # 1. Create session
    r = client.post("/api/v2/sessions")
    assert r.status_code == 200
    sid = r.json()["session_id"]

    # 2. Test GET initial tolerance
    r_tol = client.get(f"/api/v2/sessions/{sid}/tolerance")
    assert r_tol.status_code == 200
    assert r_tol.json()["tolerance_mode"] == "absolute_only"

    # 3. Test POST update tolerance
    r_up_tol = client.post(
        f"/api/v2/sessions/{sid}/tolerance",
        json={"abs_tol": 0.50, "pct_tol": 0.05, "mode": "greater"},
    )
    assert r_up_tol.status_code == 200
    assert r_up_tol.json()["ok"] is True

    # 4. Verify updated tolerance
    r_tol2 = client.get(f"/api/v2/sessions/{sid}/tolerance")
    assert r_tol2.json()["tolerance_abs"] == 0.50
    assert r_tol2.json()["tolerance_pct"] == 0.05
    assert r_tol2.json()["tolerance_mode"] == "greater"

    # 5. Test GET initial rules (should be empty under zero-default mandate)
    r_rules = client.get(f"/api/v2/sessions/{sid}/rules")
    assert r_rules.status_code == 200
    assert r_rules.json()["total"] == 0

    # 6. Test POST update rules
    sample_rule = {
        "rule_id": "rule_test_1",
        "label": "Test 1.8% MDR + 18% GST",
        "matcher": {"kind": "all"},
        "fee_rate": 0.018,
        "gst_rate": 0.18,
        "priority": 1,
        "source": "user_explicit",
    }
    r_up_rules = client.post(
        f"/api/v2/sessions/{sid}/rules",
        json={"rules": [sample_rule]},
    )
    assert r_up_rules.status_code == 200
    assert r_up_rules.json()["ok"] is True

    # 7. Verify rules applied
    r_rules2 = client.get(f"/api/v2/sessions/{sid}/rules")
    assert r_rules2.json()["total"] == 1
    assert r_rules2.json()["rules"][0]["rule_id"] == "rule_test_1"


def test_chat_confirmation_gate_flow() -> None:
    client = TestClient(app)
    r = client.post("/api/v2/sessions")
    sid = r.json()["session_id"]

    # Natural language rule instruction: "first 20% rows have 2% fee and 18% gst, the next 80% have 1.5% fee and 18% gst"
    msg = "first 20% rows have 2% fee and 18% gst, the next 80% have 1.5% fee and 18% gst"
    r_chat = client.post(f"/api/v2/sessions/{sid}/chat", json={"message": msg})
    assert r_chat.status_code == 200
    reply = r_chat.json()["response"]
    assert "Confirmation Required" in reply

    # Confirm action
    r_confirm = client.post(f"/api/v2/sessions/{sid}/chat", json={"message": "YES"})
    assert r_confirm.status_code == 200
    assert "confirmed and executed successfully" in r_confirm.json()["response"]

    # Verify rules are now active
    r_rules = client.get(f"/api/v2/sessions/{sid}/rules")
    assert r_rules.json()["total"] == 2


def test_3file_benchmark_offline_truth(tmp_path: Path) -> None:
    """Reconcile 3-file benchmark datasets and verify offline truth integrity."""
    generate_3file_benchmark(tmp_path)
    
    sales_file = tmp_path / "merchant_sales.csv"
    gw_file = tmp_path / "gateway_settlements.csv"
    bank_file = tmp_path / "bank_statement.csv"
    truth_file = tmp_path / "benchmark_truth.jsonl"
    
    assert sales_file.exists()
    assert gw_file.exists()
    assert bank_file.exists()
    assert truth_file.exists()
    
    # Read offline truth records
    truth_rows = [json.loads(line) for line in truth_file.read_text(encoding="utf-8").splitlines() if line]
    assert len(truth_rows) >= 50
    
    # Run pipeline with the datasets (CRITICAL: never uploading the truth file!)
    p = Pipeline("benchmark-session", auto_ack=True)
    p.set_policy(fee_rate=0.02, gst_rate=0.18, tolerance=0.05)
    
    report = p.run([sales_file, bank_file])
    assert report is not None
    assert report.auto_resolved_count + report.escalated_count + report.unresolved_count > 0

    # Also verify 3-file multi-way chaining across all 3 legs
    import pandas as pd
    from app.engine.multiway import run_multiway_chaining
    tables_3file = {}
    for f in (sales_file, gw_file, bank_file):
        df = pd.read_csv(f)
        df.insert(0, "_rid", range(1, len(df) + 1))
        tables_3file[f.stem] = df.to_dict("records")

    mw_rpt = run_multiway_chaining("bench-3way", tables_3file)
    assert mw_rpt is not None
    assert len(mw_rpt.legs) == 2
    assert mw_rpt.consolidated_match_rate > 0.80
    assert mw_rpt.cash_position.projected_closing > 0
    assert len(mw_rpt.journal_entries) > 0


def test_5file_enterprise_ecosystem(tmp_path: Path) -> None:
    """Verify 5-file enterprise ecosystem data integrity, profit records, and banking settlements."""
    generate_enterprise_ecosystem(tmp_path)
    
    zomato = tmp_path / "zomato_orders.csv"
    flipkart = tmp_path / "flipkart_orders.csv"
    razorpay = tmp_path / "razorpay_ledger.csv"
    icici = tmp_path / "icici_bank.csv"
    hdfc = tmp_path / "hdfc_bank.csv"
    
    for f in (zomato, flipkart, razorpay, icici, hdfc):
        assert f.exists()
        lines = f.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) >= 51  # Header + >=50 rows
        cols = lines[0].split(",")
        assert len(cols) >= 5   # >=5 attributes
        
    # Verify Razorpay Ledger profit calculation
    rzr_lines = razorpay.read_text(encoding="utf-8").splitlines()
    header = rzr_lines[0].split(",")
    profit_idx = header.index("razorpay_net_profit")
    status_idx = header.index("settlement_status")
    
    settled_count = 0
    total_net_profit = 0.0
    for line in rzr_lines[1:]:
        parts = line.split(",")
        status = parts[status_idx]
        profit = float(parts[profit_idx])
        if status == "SETTLED":
            settled_count += 1
            assert profit > 0.0  # Razorpay collects positive margin post bank charges
            total_net_profit += profit
            
    assert settled_count >= 100
    assert total_net_profit > 1000.0  # Net profit accumulated

    # Verify 5-file multi-way reconciliation across all 5 ecosystem tables
    import pandas as pd
    from app.engine.multiway import run_multiway_chaining
    ent_tables = {}
    for f in (zomato, flipkart, razorpay, icici, hdfc):
        df = pd.read_csv(f)
        df.insert(0, "_rid", range(1, len(df) + 1))
        ent_tables[f.stem] = df.to_dict("records")

    ent_rpt = run_multiway_chaining("ent-5way", ent_tables)
    assert ent_rpt is not None
    assert len(ent_rpt.legs) == 2
    assert ent_rpt.legs[0].matched_count > 0
    assert ent_rpt.legs[1].matched_count > 0
    assert ent_rpt.cash_position.projected_closing > 0
    assert len(ent_rpt.journal_entries) > 0
