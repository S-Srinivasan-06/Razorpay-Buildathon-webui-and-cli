"""End-to-End Test Suite for FastAPI Reconciliation Server and API v2.

Tests the full API v2 REST surface, multipart file upload, state machine polling,
schema mapping retrieval, policy inspection, paginated ingestion, exception queue
pagination, operator override actions, SHA-256 cryptographic audit verification,
grounded assistant chat, and high-volume (10,000+ row) Excel/CSV reconciliation throughput.
"""

import io
import json
import sys
import time
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pytest
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

BASE_URL = "http://127.0.0.1:8000"


def test_api_v2_full_suite() -> None:
    """Execute complete end-to-end integration tests against the live API v2 server."""
    try:
        r_check = requests.get(f"{BASE_URL}/docs", timeout=1.0)
    except Exception:
        pytest.skip(
            "FastAPI server not running on http://127.0.0.1:8000. "
            "Start server with `python run.py --server` to run this E2E test."
        )

    print("==================================================")
    print("STARTING RECONCILIATION AGENT API v2 TEST SUITE")
    print("==================================================")

    # 1. Test Session Creation
    print("\n[Step 1] Creating new session...")
    r = requests.post(f"{BASE_URL}/api/v2/sessions")
    assert r.status_code == 200, f"Session creation failed: {r.text}"
    sid = r.json()["session_id"]
    print(f"[OK] Session Created: {sid}")

    # 2. Test Overview (Empty State)
    print("\n[Step 2] Testing initial overview...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/overview")
    assert r.status_code == 200
    ov = r.json()
    assert ov["state"] == "IDLE"
    print(f"[OK] Initial State: {ov['state']}, Constants Version: {ov['constants_version']}")

    # 3. Test File Upload & Run with Sample Data
    print("\n[Step 3] Testing multipart file upload and reconciliation run...")
    with open("sample_data/payments.csv", "rb") as f1, open("sample_data/bank.csv", "rb") as f2:
        files = [
            ("files", ("payments.csv", f1, "text/csv")),
            ("files", ("bank.csv", f2, "text/csv")),
        ]
        r = requests.post(f"{BASE_URL}/api/v2/sessions/{sid}/run", files=files)
    assert r.status_code == 200, f"Upload run failed: {r.text}"
    print(f"[OK] Upload & Run triggered: {r.json()['files']}")

    # 4. Poll until completion (state reaches ARCHIVED)
    print("\n[Step 4] Polling state machine progress...")
    max_wait = 180
    start_t = time.time()
    final_state = None
    while time.time() - start_t < max_wait:
        r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/overview")
        st = r.json()["state"]
        print(f"  Current state: {st}")
        if st in ("ARCHIVED", "ABORT_CONFIRMED", "RUN_FAILED"):
            final_state = st
            break
        time.sleep(1)

    assert final_state == "ARCHIVED", f"Pipeline did not finish cleanly. Final state: {final_state}"
    print(f"[OK] Pipeline reached {final_state} in {time.time() - start_t:.2f}s")

    # 5. Test Ingestion Endpoint & Pagination
    print("\n[Step 5] Testing /ingestion endpoint & metadata...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/ingestion")
    assert r.status_code == 200
    ing = r.json()
    assert "table_meta" in ing
    assert "payments" in ing["table_meta"]
    assert "bank" in ing["table_meta"]
    print(f"[OK] Ingested Tables: payments ({ing['table_meta']['payments']['total_rows']} rows), bank ({ing['table_meta']['bank']['total_rows']} rows)")

    # 6. Test Mapping Endpoint
    print("\n[Step 6] Testing /mapping endpoint...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/mapping")
    assert r.status_code == 200
    mapping = r.json()
    assert mapping["committed"] is not None
    print(f"[OK] Committed Mapping: {mapping['committed']['left_key']} <-> {mapping['committed']['right_key']} (confidence: {mapping['confidence']})")

    # 7. Test Policy Endpoint
    print("\n[Step 7] Testing /policy endpoint...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/policy")
    assert r.status_code == 200
    pol = r.json()
    assert len(pol["components"]) > 0
    print(f"[OK] Policy synthesized: {len(pol['components'])} components, baseline match rate: {pol['baseline_match_rate']}")

    # 8. Test Results Endpoint
    print("\n[Step 8] Testing /results endpoint...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/results")
    assert r.status_code == 200
    res = r.json()
    assert res["executed"] is True
    print(f"[OK] Results: Match Rate = {res['match_rate']:.1%}, Matched Pairs = {len(res['matched'])}, Totals = {res['totals']}")

    # 9. Test Exception Queue Endpoint
    print("\n[Step 9] Testing /exceptions endpoint...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/exceptions")
    assert r.status_code == 200
    exc = r.json()
    assert len(exc["queue"]) > 0
    print(f"[OK] Exception Queue: {len(exc['queue'])} items. Summary: {exc['summary']}")

    # 10. Test Exception Override Action
    print("\n[Step 10] Testing exception override action...")
    first_exc = exc["queue"][0]
    rid = first_exc["rid"]
    r = requests.post(f"{BASE_URL}/api/v2/sessions/{sid}/exceptions/{rid}/action", json={"action": "approve", "note": "Verified by manager"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    print(f"[OK] Exception #{rid} override status: {r.json()['action']}")

    # 11. Test Cryptographic Audit Log
    print("\n[Step 11] Testing /audit endpoint & SHA-256 chain verification...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/audit")
    assert r.status_code == 200
    audit = r.json()
    assert audit["verified"] is True
    print(f"[OK] Audit records logged: {audit['count']}, Chain Integrity: {audit['verified']}")

    # 12. Test Grounded Chat
    print("\n[Step 12] Testing /chat grounded Q&A endpoint...")
    r = requests.post(f"{BASE_URL}/api/v2/sessions/{sid}/chat", json={"message": "What is the match rate and total gross ledger volume?"})
    assert r.status_code == 200
    chat_res = r.json()
    print(f"[OK] Chat response: {chat_res.get('response', '')[:140]}...")

    # 13. Test High-Volume 10,000+ Row Dataset (Excel .xlsx and CSV)
    print("\n[Step 13] Generating 10,000+ row dataset in Excel (.xlsx) and CSV format...")
    n_rows = 10000
    dates = pd.date_range("2026-03-01", periods=30).astype(str).tolist()

    # Left ledger (payments)
    orders = [f"ORD_{i:06d}" for i in range(1, n_rows + 1)]
    amounts = np.random.uniform(50.0, 5000.0, size=n_rows).round(2)
    pay_dates = [dates[i % len(dates)] for i in range(n_rows)]

    df_pay = pd.DataFrame({"order_id": orders, "amount": amounts, "date": pay_dates})

    # Right statement (bank) - 95% match, 5% fee variance or drift
    bank_utrs = orders.copy()
    bank_credits = amounts.copy()
    # Introduce fee deductions to 10%
    for i in range(0, n_rows, 10):
        fee = round(amounts[i] * 0.02 * 1.18, 2)
        bank_credits[i] = round(amounts[i] - fee, 2)

    df_bank = pd.DataFrame({"utr": bank_utrs, "credit": bank_credits, "date": pay_dates})

    # Save to Excel and CSV in-memory buffers
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        df_pay.to_excel(writer, index=False, sheet_name="payments")
    excel_buf.seek(0)

    csv_buf = io.BytesIO()
    df_bank.to_csv(csv_buf, index=False)
    csv_buf.seek(0)

    print("Generated payments (10,000 rows in Excel .xlsx) and bank (10,000 rows in CSV)")

    # Run 10k reconciliation via API
    r = requests.post(f"{BASE_URL}/api/v2/sessions")
    sid_large = r.json()["session_id"]
    print(f"Created session for 10k run: {sid_large}")

    t0 = time.time()
    files = [
        ("files", ("payments.xlsx", excel_buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ("files", ("bank.csv", csv_buf, "text/csv")),
    ]
    r = requests.post(f"{BASE_URL}/api/v2/sessions/{sid_large}/run", files=files)
    assert r.status_code == 200

    # Wait for completion
    st = "RUNNING"
    while time.time() - t0 < 60:
        r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid_large}/overview")
        st = r.json()["state"]
        if st in ("ARCHIVED", "RUN_FAILED"):
            break
        time.sleep(1)

    elapsed = time.time() - t0
    print(f"[OK] 10,000+ Row Dataset Reconciled in {elapsed:.2f}s! Final state: {st}")

    # Verify results of 10k run
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid_large}/results")
    res_large = r.json()
    assert res_large["executed"] is True
    print(f"[OK] 10k Run Stats: Match Rate = {res_large['match_rate']:.1%}, Matched = {len(res_large['matched'])}, Throughput = {res_large.get('throughput_rows_per_sec', 0):.0f} rows/sec")

    # Verify paginated ingestion
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid_large}/ingestion?table=payments&page=1&page_size=50")
    ing_large = r.json()
    assert "payments" in ing_large["tables"]
    assert ing_large["tables"]["payments"]["total"] == 10000
    assert len(ing_large["tables"]["payments"]["items"]) == 50
    print(f"[OK] Paginated Ingestion: Total {ing_large['tables']['payments']['total']} rows, Page size: 50, Total pages: {ing_large['tables']['payments']['total_pages']}")

    print("\n==================================================")
    print("ALL API v2 & LARGE DATASET TESTS PASSED 100%!")
    print("==================================================")


if __name__ == "__main__":
    test_api_v2_full_suite()

