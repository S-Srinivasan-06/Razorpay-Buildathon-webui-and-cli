# Codebase Documentation

## File Tree Structure

```
recon_agent/
├── .env.example
├── requirements.txt
├── constants_v0.yaml
├── run.py
├── sample_data/
│   ├── payments.csv
│   ├── bank.csv
│   └── ground_truth.jsonl
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── pipeline.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── audit.py
│   │   ├── channels.py
│   │   ├── constants.py
│   │   ├── contracts.py
│   │   ├── cost.py
│   │   ├── dispatcher.py
│   │   ├── llm_client.py
│   │   ├── masking.py
│   │   └── states.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── chatbot.py
│   │   ├── fee.py
│   │   ├── match.py
│   │   ├── qa.py
│   │   ├── report.py
│   │   └── resolving.py
│   ├── server/
│   │   ├── __init__.py
│   │   ├── api_v2.py
│   │   └── main.py
│   └── static/
│       └── index.html
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_api_v2_e2e.py
    ├── test_constants.py
    ├── test_durability.py
    ├── test_file_lifecycle_and_chat.py
    ├── test_halt_reentry_safety.py
    ├── test_interactive_resume.py
    ├── test_match_evidence.py
    ├── test_no_duplicate_exceptions.py
    ├── test_overrides_and_discrepancies.py
    └── test_pipeline_evidence_flow.py
```

---

## Files

### README.md

```markdown
# ⚡ Razorpay Reconciliation Agent (`recon_agent`)

> **Autonomous, Multi-Way Financial Reconciliation Engine with Dynamic Fee Modeling, AI Diagnostic Provenance, and Cryptographic SHA-256 Audit Trails.**

---

## 📌 Overview

The **Razorpay Reconciliation Agent** is an enterprise-grade financial reconciliation system built to autonomously ingest, match, and resolve discrepancies between internal payment ledgers and external bank/gateway settlement statements.

It combines:
- **Deterministic Multi-Heuristic Engine**: Key linkage, date window tolerance, fee schedules, and split transaction detection.
- **LLM-Powered Semantic Intelligence**: Powered by **Gemma 4 31B** (`gemma-4-31b-it`) for ambiguous schema mapping, semantic similarity, exception root-cause explanations, and interactive conversational query answering.
- **Continuous Grounded Chatbot**: Ask natural-language questions about matched pairs, fees, duplicate orders, or balance variances strictly grounded in the active session's datasets.
- **Dynamic File Lifecycle Management**: Add or delete files dynamically with strict context isolation (deleted files are completely purged from LLM memory).
- **Cryptographic Audit Ledger**: Every state transition and decision is signed in a tamper-evident SHA-256 hash-chain stored on disk.
- **First-Class CLI Output**: Clean terminal interface with Markdown tables, live token metering, and zero external dependencies for terminal rendering.

---

## 🚀 Quickstart & Setup

### 1. Prerequisites & Installation

Clone the repository and install the lightweight dependencies:

```bash
cd recon_agent
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Set your Google Gemini API key as an environment variable:

#### On Linux / macOS:
```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
# Optional: override model (default: gemma-4-31b-it)
export LLM_MODEL="gemma-4-31b-it"
```

#### On Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
# Optional: override model (default: gemma-4-31b-it)
$env:LLM_MODEL="gemma-4-31b-it"
```

#### On Windows (Command Prompt):
```cmd
set GEMINI_API_KEY=YOUR_GEMINI_API_KEY
set LLM_MODEL=gemma-4-31b-it
```

---

## 💻 CLI Running Guide

### Standard Reconciliation Run

Reconcile internal payments against bank settlements:

```bash
python run.py sample_data/payments.csv sample_data/bank.csv
```

---

### Run with Ground Truth Benchmark Evaluation

Evaluate precision, recall, and classification accuracy against a benchmark ground truth file:

```bash
python run.py sample_data/payments.csv sample_data/bank.csv --truth sample_data/ground_truth.jsonl
```

---

### Interactive Conversational Chatbot Mode (`--chat` or `-i`)

Run reconciliation and immediately launch the continuous interactive REPL to query Gemma 4 31B:

```bash
python run.py sample_data/payments.csv sample_data/bank.csv --chat
```

```text
========================================================
             RECONCILIATION ASSISTANT CHAT             
========================================================
[*] Connected to Gemma 4 31B grounded strictly in active session [8c55792b].
[*] Ask questions about matched records, fees, duplicates, or diagnostics.
[*] Type 'exit' or 'quit' to end the conversation.

recon-bot> Why was ORD_4 flagged as an error?

ORD_4 was flagged as a duplicate ledger entry because it appears twice in the payments ledger (Source A) but only settled once in the bank statement (Source B). RID #4 was matched to the bank entry, leaving the second ORD_4 un-settled and escalated for manual review. [Cost: $0.000089]

recon-bot> Explain the batch deposit BATCH.

The BATCH transaction (INR 1,074.04) in Source B is an aggregated deposit combining orders ORD_6 (INR 400.00) and ORD_7 (INR 700.00) net of INR 25.96 gateway processing fees. It was automatically approved with no error. [Cost: $0.000094]
```

---

### Fast Offline / Zero-LLM Deterministic Mode (`--deterministic`)

Execute purely on deterministic rule engines without external API calls:

```bash
python run.py sample_data/payments.csv sample_data/bank.csv --deterministic
```

---

### JSON Output Mode (`--json`)

Export the complete structured reconciliation report and input datasets as JSON:

```bash
python run.py sample_data/payments.csv sample_data/bank.csv --truth sample_data/ground_truth.jsonl --json
```

---

### Launch Headless API Server (`--server`)

Start the FastAPI REST & WebSocket server:

```bash
python run.py --server --host 127.0.0.1 --port 8000
```

---

## 📂 Demo Test Files Walkthrough

The repository includes pre-built demo datasets in `sample_data/` covering core financial reconciliation edge cases:

### 1. `sample_data/payments.csv` (Source A: Internal Ledger)
```csv
order_id,amount,date
ORD_1,1000.00,2026-03-01
ORD_2,2000.00,2026-03-01
ORD_3,3000.00,2026-03-06
ORD_4,500.00,2026-03-02
ORD_4,500.00,2026-03-02
ORD_6,400.00,2026-03-02
ORD_7,700.00,2026-03-02
MIS_800,900.00,2026-03-03
```

### 2. `sample_data/bank.csv` (Source B: Bank Statement)
```csv
utr,credit,date
ORD_1,1000.00,2026-03-02
ORD_2,1952.80,2026-03-02
ORD_3,3000.00,2026-03-13
ORD_4,500.00,2026-03-03
BATCH,1074.04,2026-03-03
ORD_9,850.00,2026-03-05
REFUND,-250.00,2026-03-05
```

### 3. `sample_data/ground_truth.jsonl` (Truth Mapping)
```jsonl
{"l_rid": 1, "r_rid": 1, "class": "exact"}
{"l_rid": 2, "r_rid": 2, "class": "fee_deduction"}
{"l_rid": 4, "r_rid": 4, "class": "duplicate_first"}
```

---

## 📊 Sample CLI Output

```markdown
# ⚡ Razorpay Reconciliation Agent
**Session ID**: `86f3fa97`

## Execution Steps
- **Mode**: Deterministic Engine (Offline / Zero-LLM)
- **Ingesting**: `sample_data/payments.csv, sample_data/bank.csv`
- **Ground Truth Benchmark**: `sample_data/ground_truth.jsonl`
- **Step 1/7**: Profiling table schemas and column statistics...
- **Step 2/7**: Linking schema keys and amounts via mapping tool...
- **Step 3/7**: Synthesizing policy components & tolerance windows...
- **Step 4/7**: Performing dry-run calibration on sample rows...
- **Step 5/7**: Executing multi-attribute matching engine...
- **Step 6/7**: Classifying exceptions & verifying invariant proofs...
- **Step 7/7**: Aggregating financial balances & signing cryptographic audit ledger...

---

## Ingested Input Datasets

### Table: `payments` (8 records)

| # | order_id | amount | date       |
| - | -------- | ------ | ---------- |
| 1 | ORD_1    | 1000.0 | 2026-03-01 |
| 2 | ORD_2    | 2000.0 | 2026-03-01 |
| 3 | ORD_3    | 3000.0 | 2026-03-06 |
| 4 | ORD_4    | 500.0  | 2026-03-02 |
| 5 | ORD_4    | 500.0  | 2026-03-02 |
| 6 | ORD_6    | 400.0  | 2026-03-02 |
| 7 | ORD_7    | 700.0  | 2026-03-02 |
| 8 | MIS_800  | 900.0  | 2026-03-03 |

### Table: `bank` (7 records)

| # | utr    | credit  | date       |
| - | ------ | ------- | ---------- |
| 1 | ORD_1  | 1000.0  | 2026-03-02 |
| 2 | ORD_2  | 1952.8  | 2026-03-02 |
| 3 | ORD_3  | 3000.0  | 2026-03-13 |
| 4 | ORD_4  | 500.0   | 2026-03-03 |
| 5 | BATCH  | 1074.04 | 2026-03-03 |
| 6 | ORD_9  | 850.0   | 2026-03-05 |
| 7 | REFUND | -250.0  | 2026-03-05 |

---

## Reconciliation Report

### Performance & Metrics

| Metric             | Value        |
| ------------------ | ------------ |
| Match Rate         | 27.3%        |
| Precision vs Truth | 100.0%       |
| Recall vs Truth    | 100.0%       |
| Throughput         | 948 rows/sec |
| Execution Time     | 0.17s        |
| LLM Metered Cost   | $0.000168    |

### Financial Balances

| Financial Balance Component | Amount (INR) |
| --------------------------- | ------------ |
| Gross Ledger Volume         | ₹9,000.00    |
| Net Bank Inflow             | ₹8,126.84    |
| Gateway Fees Variance       | ₹873.16      |
| Matched Value               | ₹3,500.00    |
| Exception Value             | ₹5,500.00    |

### Exception Queue Summary (8 Total)

| Queue Metric             | Count | Status                    |
| ------------------------ | ----- | ------------------------- |
| Auto-Resolved (Approved) | 2     | APPROVED [NO ERROR]       |
| Escalated (Review Req)   | 6     | REQUIRES ACTION [ERROR]   |
| Unresolved Pending       | 0     | PENDING                   |
| Total Honest Exceptions  | 8     | Sum Invariant: VALID [OK] |

### Classified Discrepancies & Diagnostics

| # | Side | Reference | Discrepancy Class | Action Status           | Delta (INR) | Diagnostic & Root Cause                                                                                              |
| - | ---- | --------- | ----------------- | ----------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------- |
| 1 | L    | ORD_3     | temporal_drift    | APPROVED [NO ERROR]     | ₹0.00       | Approved [No Error]: Exact amount & reference 'ORD_3' matched; settlement deferred by bank holiday/clearing window.  |
| 2 | L    | ORD_4     | duplicate         | REQUIRES ACTION [ERROR] | —           | Error in Source A (Ledger): Duplicate order reference 'ORD_4' recorded multiple times in payments ledger.            |
| 3 | L    | ORD_6     | unclassified      | REQUIRES ACTION [ERROR] | —           | Error in Source B (Bank): Order 'ORD_6' exists in payments ledger but has no corresponding bank settlement credit.   |
| 4 | L    | ORD_7     | unclassified      | REQUIRES ACTION [ERROR] | —           | Error in Source B (Bank): Order 'ORD_7' exists in payments ledger but has no corresponding bank settlement credit.   |
| 5 | L    | MIS_800   | unclassified      | REQUIRES ACTION [ERROR] | —           | Error in Source B (Bank): Order 'MIS_800' exists in payments ledger but has no corresponding bank settlement credit. |
| 6 | R    | BATCH     | split             | APPROVED [NO ERROR]     | —           | Approved [No Error]: Batch settlement combines multiple order legs (RIDs [6, 7]) net of payment gateway fees.        |
| 7 | R    | ORD_9     | unclassified      | REQUIRES ACTION [ERROR] | —           | Error in Source A (Ledger): Unmatched bank credit for UTR 'ORD_9' without corresponding order in payments ledger.    |
| 8 | R    | REFUND    | refund_offset     | REQUIRES ACTION [ERROR] | —           | Anomaly in Source B (Bank): Negative credit entry (-₹250.00) representing customer refund or chargeback.             |

---

## Cryptographic Audit Ledger

| Audit Attribute         | Value                             |
| ----------------------- | --------------------------------- |
| Audit Entries Logged    | 9                                 |
| SHA-256 Chain Integrity | VERIFIED [OK]                     |
| Session Audit Path      | `data/audit/86f3fa97.audit.jsonl` |

---
```

---

## 🏛️ System Architecture & File Structure

```
recon_agent/
├── requirements.txt                   # FastAPI, Uvicorn, Pandas, Pydantic, PyYAML, Pytest
├── constants_v0.yaml                  # Governance constants, derivation methods & fee schedules
├── run.py                             # Unified CLI runner, Markdown formatter & chat REPL
├── sample_data/                       # Benchmark demo files
│   ├── payments.csv
│   ├── bank.csv
│   └── ground_truth.jsonl
├── app/
│   ├── __init__.py
│   ├── config.py                      # File system paths & environment variable loader
│   ├── pipeline.py                    # Central 7-step reconciliation pipeline driver
│   ├── core/
│   │   ├── audit.py                   # Cryptographic SHA-256 tamper-evident ledger
│   │   ├── channels.py                # Decoupled in-memory publish/subscribe event bus
│   │   ├── constants.py               # Constants registry loaded from YAML
│   │   ├── contracts.py               # Pydantic schemas, enums, evidence models & reports
│   │   ├── cost.py                    # LLM token metering & cost tracking
│   │   ├── dispatcher.py              # Circuit breaker, retries & budget-governed tool calls
│   │   ├── llm_client.py              # Gemma 4 31B client with JSON & chat completions
│   │   ├── masking.py                 # PII masking & pattern redaction utilities
│   │   └── states.py                  # 14-state Finite State Machine with abort tokens
│   ├── data/
│   │   └── generator.py               # Synthetic benchmark data & anomaly generator
│   ├── engine/
│   │   ├── chatbot.py                 # Grounded conversational session engine
│   │   ├── fee.py                     # Gateway fee calculations (MDR, fixed fee, GST)
│   │   ├── match.py                   # Multi-heuristic matching engine
│   │   ├── qa.py                      # Hypothesis-ordered exception classification
│   │   ├── resolving.py               # Intelligent approvals & precise diagnostic explanations
│   │   └── report.py                  # Balance aggregator & FinalReport builder
│   └── server/
│       └── main.py                    # FastAPI REST endpoints & WebSocket live stream
└── tests/
    ├── test_constants.py              # Registry loading & fee parsing tests
    ├── test_durability.py             # SHA-256 hash-chain verification & tamper detection
    ├── test_file_lifecycle_and_chat.py # File add/delete, context isolation & chat tests
    ├── test_halt_reentry_safety.py    # Review floor gate & resume loop safety tests
    ├── test_interactive_resume.py     # Multi-halt interactive resume tests
    ├── test_match_evidence.py         # Raw vs fee-adjusted matching tests
    ├── test_no_duplicate_exceptions.py # Exception deduplication invariant tests
    ├── test_overrides_and_discrepancies.py # User overrides & sum invariant tests
    └── test_pipeline_evidence_flow.py # End-to-end integration tests
```

---

## 🧪 Running Automated Tests

Run the complete test suite:

```bash
pytest -v
```

All 14 test suites covering state machine transitions, cryptographic ledger verification, fee calculations, file deletion context isolation, and ground-truth benchmarks execute in under 1 second in offline mode.
```

### recon_agent/.env.example

```bash
# Google Gemini / Gemma API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemma-4-31b-it

```

### recon_agent/constants_v0.yaml

```yaml
version: v0
constants:
  - {name: mapping_auto_accept, value: 0.70, scope: MAPPING, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.50, 0.90], gates: MAPPING_VALIDATED auto-accept}
  - {name: mapping_review_floor, value: 0.40, scope: MAPPING, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.20, 0.60], gates: MAPPING_VALIDATED halt}
  - {name: mapping_ambiguity_delta, value: 0.10, scope: MAPPING, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.05, 0.20], gates: escalate-to-user}
  - {name: match_auto_threshold, value: 0.85, scope: MATCH, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.70, 0.95], gates: auto-match}
  - {name: match_review_floor, value: 0.60, scope: MATCH, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.40, 0.80], gates: below=reject, band=review}
  - {name: w_mapping_structural, value: 0.35, scope: MAPPING, derivation_method: manual_default, derived_from: "v3 weights, unvalidated", valid_range: [0, 1], gates: mapping_confidence}
  - {name: w_mapping_sample, value: 0.30, scope: MAPPING, derivation_method: manual_default, derived_from: "v3 weights, unvalidated", valid_range: [0, 1], gates: mapping_confidence}
  - {name: w_mapping_type, value: 0.20, scope: MAPPING, derivation_method: manual_default, derived_from: "v3 weights, unvalidated", valid_range: [0, 1], gates: mapping_confidence}
  - {name: w_mapping_semantic, value: 0.15, scope: MAPPING, derivation_method: manual_default, derived_from: "v3 weights, unvalidated", valid_range: [0, 1], gates: mapping_confidence}
  - {name: w_match_key, value: 0.40, scope: MATCH, derivation_method: manual_default, derived_from: "v3 weights, unvalidated", valid_range: [0, 1], gates: match_confidence}
  - {name: w_match_amount, value: 0.30, scope: MATCH, derivation_method: manual_default, derived_from: "v3 weights, unvalidated", valid_range: [0, 1], gates: match_confidence}
  - {name: w_match_date, value: 0.20, scope: MATCH, derivation_method: manual_default, derived_from: "v3 weights, unvalidated", valid_range: [0, 1], gates: match_confidence}
  - {name: w_match_semantic, value: 0.10, scope: MATCH, derivation_method: manual_default, derived_from: "v3 weights, unvalidated", valid_range: [0, 1], gates: match_confidence}
  - {name: w_exception_evidence, value: 0.50, scope: EXCEPTION, derivation_method: manual_default, derived_from: "v0 renormalized", valid_range: [0, 1], gates: exception_confidence}
  - {name: w_exception_category, value: 0.30, scope: EXCEPTION, derivation_method: manual_default, derived_from: "v0 renormalized", valid_range: [0, 1], gates: exception_confidence}
  - {name: w_exception_semantic, value: 0.20, scope: EXCEPTION, derivation_method: manual_default, derived_from: "v0 renormalized", valid_range: [0, 1], gates: exception_confidence}
  - {name: exception_auto_resolve_confidence, value: 0.85, scope: EXCEPTION, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.70, 0.95], gates: auto_resolve}
  - {name: exception_auto_resolve_evidence_min, value: 2, scope: EXCEPTION, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [1, 5], gates: auto_resolve}
  - {name: pii_mask_threshold, value: 0.70, scope: pipeline, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.50, 0.90], gates: auto-mask}
  - {name: pii_review_threshold, value: 0.40, scope: pipeline, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.20, 0.60], gates: review flag}
  - {name: revision_match_rate_threshold, value: 0.60, scope: pipeline, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.40, 0.80], gates: REVISION entry}
  - {name: revision_iteration_cap, value: 3, scope: pipeline, derivation_method: manual_default, derived_from: "fixed cap", gates: REVISION loop}
  - {name: revision_time_cap_s, value: 120, scope: pipeline, derivation_method: manual_default, derived_from: "fixed cap", gates: REVISION loop, unit: s}
  - {name: revision_cost_cap_usd, value: 0.10, scope: pipeline, derivation_method: derived, derived_from: "20x single-revision cost", gates: REVISION loop, unit: usd}
  - {name: regression_reject_delta, value: 0.05, scope: pipeline, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.02, 0.10], gates: safe-revision gate}
  - {name: circuit_breaker_failure_count, value: 3, scope: pipeline, derivation_method: manual_default, derived_from: "fixed", gates: per-tool HALT}
  - {name: calibration_sanity_floor, value: 0.50, scope: pipeline, derivation_method: manual_default, derived_from: "reasoned default", valid_range: [0.30, 0.80], gates: CALIBRATION_DRIFT_WARNING}
  - {name: ingest_timeout_s_per_file, value: 60, scope: pipeline, derivation_method: manual_default, derived_from: "fixed", gates: INGESTING, unit: s}
  - {name: profiling_timeout_s_per_table, value: 30, scope: pipeline, derivation_method: manual_default, derived_from: "fixed", gates: PROFILING, unit: s}
  - {name: dry_run_timeout_s, value: 20, scope: pipeline, derivation_method: manual_default, derived_from: "fixed", gates: DRY_RUN, unit: s}
  - {name: sandbox_timeout_s, value: 30, scope: pipeline, derivation_method: manual_default, derived_from: "fixed", gates: EXECUTING, unit: s}
  - {name: sandbox_memory_mb, value: 512, scope: pipeline, derivation_method: manual_default, derived_from: "fixed", gates: sandbox, unit: mb}
  - {name: llm_tool_timeout_s, value: 25, scope: pipeline, derivation_method: manual_default, derived_from: "fixed", gates: tool calls, unit: s}
  - {name: cost_llm_in_per_1k_usd, value: 0.0005, scope: pipeline, derivation_method: manual_default, derived_from: "provider list price", gates: CostTracker, unit: usd}
  - {name: cost_llm_out_per_1k_usd, value: 0.0015, scope: pipeline, derivation_method: manual_default, derived_from: "provider list price", gates: CostTracker, unit: usd}
  - {name: cost_sandbox_cpu_s_usd, value: 0.00001, scope: pipeline, derivation_method: manual_default, derived_from: "provider list price", gates: CostTracker, unit: usd}
  - {name: cost_sandbox_mem_gb_s_usd, value: 0.000005, scope: pipeline, derivation_method: manual_default, derived_from: "provider list price", gates: CostTracker, unit: usd}
  - {name: session_cost_cap_usd, value: 0.50, scope: pipeline, derivation_method: derived, derived_from: "5x revision_cost_cap_usd", valid_range: [0.10, 5.00], gates: CostTracker pre-call, unit: usd}
  - {name: amount_score_scale_pct, value: 0.05, scope: MATCH, derivation_method: manual_default, derived_from: "5% of gross decay band", valid_range: [0.01, 0.20], gates: amount_delta_score}
fee_schedules:
  - provider: razorpay
    schedule_id: razorpay_test_mode
    version: "1.0"
    effective_from: 2026-01-01
    model_type: flat_rate
    params: {rate: 0.02}
    gst_rate: 0.18
    currency: INR

```

### recon_agent/requirements.txt

```text
fastapi>=0.110
uvicorn>=0.29
python-multipart>=0.0.9
pandas>=2.2
openpyxl>=3.1
pydantic>=2.8
pyyaml>=6.0
pytest>=8.0

```

### recon_agent/run.py

```python
#!/usr/bin/env python3
"""Razorpay Reconciliation Agent CLI & Server Runner

Usage:
  # Run CLI reconciliation:
  python run.py sample_data/payments.csv sample_data/bank.csv
  python run.py sample_data/payments.csv sample_data/bank.csv --truth sample_data/ground_truth.jsonl
  python run.py sample_data/payments.csv sample_data/bank.csv --chat
  python run.py sample_data/payments.csv sample_data/bank.csv --deterministic

  # Run API server:
  python run.py --server [--host 127.0.0.1] [--port 8000]
"""

import argparse
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from app.config import LOGS_DIR
from app.core import llm_client
from app.core.audit import audit_for
from app.engine.chatbot import ReconChatSession
from app.pipeline import Pipeline


def format_markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Format data rows into a clean, aligned Markdown table."""
    if not headers or not rows:
        return "_No records available._"
    str_rows = [[str(val) for val in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, val in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(val))

    header_line = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    separator_line = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    data_lines = [
        "| " + " | ".join(row[i].ljust(widths[i]) if i < len(row) else "".ljust(widths[i]) for i in range(len(headers))) + " |"
        for row in str_rows
    ]
    return "\n".join([header_line, separator_line] + data_lines)


def start_chat_repl(pipe: Pipeline, sid: str):
    print("\n---\n", flush=True)
    print(f"## 💬 Interactive Reconciliation Assistant (Session: `{sid}`)\n", flush=True)
    print(f"- Connected to **Gemma 4 31B** (`gemma-4-31b-it`) strictly grounded in active session datasets.", flush=True)
    print(f"- Ask questions about matched records, fee schedules, duplicates, or root causes.", flush=True)
    print(f"- Type `exit` or `quit` to end the conversation.\n", flush=True)

    chat_session = ReconChatSession(sid, pipe)

    while True:
        try:
            sys.stdout.write("recon-bot> ")
            sys.stdout.flush()
            user_input = sys.stdin.readline()
            if not user_input:
                break
            query = user_input.strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("\n- **Status**: Chat session closed.", flush=True)
                break

            result = chat_session.chat(query)
            if result.get("ok"):
                cost_str = f" *(LLM Cost: ${result['cost_usd']:.6f})*" if result.get("cost_usd") else ""
                print(f"\n{result['response']}{cost_str}\n", flush=True)
            else:
                print(f"\n> ⚠️ **Error**: {result.get('error', result.get('response'))}\n", flush=True)
        except (KeyboardInterrupt, EOFError):
            print("\n- **Status**: Exiting chat.", flush=True)
            break


def run_cli(files: list[Path], truth: Path | None = None, auto_ack: bool = True, as_json: bool = False, deterministic: bool = False, chat: bool = False):
    sid = uuid.uuid4().hex[:8]
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    session_file = LOGS_DIR / f"{sid}.log"
    latest_session_log = LOGS_DIR / "session.log"
    session_file.write_text("", encoding="utf-8")
    latest_session_log.write_text("", encoding="utf-8")

    print(f"# ⚡ Razorpay Reconciliation Agent", flush=True)
    print(f"**Session ID**: `{sid}`\n", flush=True)
    print("## Execution Steps", flush=True)
    
    if deterministic:
        print(f"- **Mode**: Deterministic Engine (Offline / Zero-LLM)", flush=True)
        def boom(*a, **k):
            raise ConnectionError("Deterministic mode enabled")
        llm_client.json_chat = boom

    for f in files:
        if not f.exists():
            print(f"> ❌ **Error**: File not found: `{f}`", file=sys.stderr, flush=True)
            sys.exit(1)
            
    if truth and not truth.exists():
        print(f"> ❌ **Error**: Truth file not found: `{truth}`", file=sys.stderr, flush=True)
        sys.exit(1)

    print(f"- **Ingesting**: `{', '.join(str(f) for f in files)}`", flush=True)
    if truth:
        print(f"- **Ground Truth Benchmark**: `{truth}`", flush=True)
    
    t0 = time.time()
    pipe = Pipeline(sid=sid, auto_ack=auto_ack)
    report = pipe.run(files, truth)
    elapsed = time.time() - t0

    if as_json:
        out = {
            "session_id": sid,
            "input_data": pipe.tables,
            "report": report.model_dump(mode="json"),
            "exceptions": [
                {
                    "rid": item["rec"].rid,
                    "side": item["rec"].side,
                    "ref": item["rec"].ref,
                    "reason": item["rec"].reason.value if hasattr(item["rec"].reason, "value") else str(item["rec"].reason),
                    "action": item.get("action", "pending"),
                    "confidence": item.get("conf", 0.0),
                    "delta": item["rec"].delta,
                    "explanation": item.get("explanation") or getattr(item["rec"], "explanation", None),
                    "evidence": [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])]
                }
                for item in pipe.queue
            ],
            "audit": {
                "records_count": len(audit_for(sid).records),
                "verified": audit_for(sid).verify()
            }
        }
        print(json.dumps(out, indent=2), flush=True)
        if chat:
            start_chat_repl(pipe, sid)
        return

    # 1. Ingested Input Data Section (Markdown Tables)
    print("\n---\n", flush=True)
    print("## Ingested Input Datasets", flush=True)
    for tbl_name, rows in pipe.tables.items():
        if not rows:
            continue
        cols = [k for k in rows[0].keys() if not k.startswith("_")]
        headers = ["#"] + cols
        data_rows = [[i] + [r.get(c, "") for c in cols] for i, r in enumerate(rows, 1)]
        print(f"\n### Table: `{tbl_name}` ({len(rows)} records)\n", flush=True)
        print(format_markdown_table(headers, data_rows), flush=True)

    # 2. Formatted Markdown Summary
    print("\n---\n", flush=True)
    print("## Reconciliation Report", flush=True)
    
    perf_headers = ["Metric", "Value"]
    perf_rows = [
        ["Match Rate", f"{report.match_rate:.1%}"],
        ["Precision vs Truth", f"{report.precision_vs_truth:.1%}" if report.precision_vs_truth is not None else "N/A"],
        ["Recall vs Truth", f"{report.recall_vs_truth:.1%}" if report.recall_vs_truth is not None else "N/A"],
        ["Throughput", f"{report.throughput_rows_per_sec:.0f} rows/sec"],
        ["Execution Time", f"{elapsed:.2f}s"],
        ["LLM Metered Cost", f"${report.cost_usd:.6f}"]
    ]
    print("\n### Performance & Metrics\n", flush=True)
    print(format_markdown_table(perf_headers, perf_rows), flush=True)

    fin_headers = ["Financial Balance Component", "Amount (INR)"]
    fin_rows = [
        ["Gross Ledger Volume", f"₹{report.total_gross:,.2f}"],
        ["Net Bank Inflow", f"₹{report.total_net:,.2f}"],
        ["Gateway Fees Variance", f"₹{report.total_fees:,.2f}"],
        ["Matched Value", f"₹{report.matched_value:,.2f}"],
        ["Exception Value", f"₹{report.exception_value:,.2f}"]
    ]
    print("\n### Financial Balances\n", flush=True)
    print(format_markdown_table(fin_headers, fin_rows), flush=True)
    
    inv_ok = (report.auto_resolved_count + report.escalated_count + report.unresolved_count == report.honest_exception_count)
    q_headers = ["Queue Metric", "Count", "Status"]
    q_rows = [
        ["Auto-Resolved (Approved)", str(report.auto_resolved_count), "APPROVED [NO ERROR]"],
        ["Escalated (Review Req)", str(report.escalated_count), "REQUIRES ACTION [ERROR]"],
        ["Unresolved Pending", str(report.unresolved_count), "PENDING"],
        ["Total Honest Exceptions", str(report.honest_exception_count), f"Sum Invariant: {'VALID [OK]' if inv_ok else 'INVALID'}"]
    ]
    print(f"\n### Exception Queue Summary ({report.honest_exception_count} Total)\n", flush=True)
    print(format_markdown_table(q_headers, q_rows), flush=True)
    
    if pipe.queue:
        print("\n### Classified Discrepancies & Diagnostics\n", flush=True)
        exc_headers = ["#", "Side", "Reference", "Discrepancy Class", "Action Status", "Delta (INR)", "Diagnostic & Root Cause"]
        exc_rows = []
        for i, item in enumerate(pipe.queue, 1):
            rec = item["rec"]
            action = item.get("action", "pending")
            action_badge = "APPROVED [NO ERROR]" if action == "auto_resolve" else "REQUIRES ACTION [ERROR]"
            delta_str = f"₹{rec.delta:,.2f}" if rec.delta is not None else "—"
            reason_str = rec.reason.value if hasattr(rec.reason, "value") else str(rec.reason)
            explanation = item.get("explanation") or getattr(rec, "explanation", "") or "No diagnostic available."
            exc_rows.append([str(i), rec.side, str(rec.ref or "N/A"), reason_str, action_badge, delta_str, explanation])
        print(format_markdown_table(exc_headers, exc_rows), flush=True)

    # 3. Cryptographic Audit Ledger Section
    audit_log = audit_for(sid)
    print("\n---\n", flush=True)
    print("## Cryptographic Audit Ledger\n", flush=True)
    audit_headers = ["Audit Attribute", "Value"]
    audit_rows = [
        ["Audit Entries Logged", str(len(audit_log.records))],
        ["SHA-256 Chain Integrity", "VERIFIED [OK]" if audit_log.verify() else "TAMPERED [FAIL]"],
        ["Session Audit Path", f"`data/audit/{sid}.audit.jsonl`"]
    ]
    print(format_markdown_table(audit_headers, audit_rows), flush=True)
    print("\n---\n", flush=True)

    if chat:
        start_chat_repl(pipe, sid)


def run_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    import webbrowser
    import threading
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"- **Server**: Starting API Server on `http://{host}:{port}` ...", flush=True)
    print(f"- **Console**: Opening `http://{host}:{port}/console` in browser ...", flush=True)
    # Open browser after a short delay
    threading.Timer(1.5, lambda: webbrowser.open(f"http://{host}:{port}/console")).start()
    uvicorn.run(
        "app.server.main:app",
        host=host,
        port=port,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                },
            },
            "handlers": {
                "file": {
                    "formatter": "default",
                    "class": "logging.FileHandler",
                    "filename": str(LOGS_DIR / "server.log"),
                    "mode": "a",
                    "encoding": "utf-8",
                },
                "console": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["file", "console"],
            },
        }
    )


def main():
    parser = argparse.ArgumentParser(
        description="Razorpay Autonomous Financial Reconciliation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="*", type=Path, help="CSV/Excel statement files to reconcile (e.g. sample_data/payments.csv sample_data/bank.csv)")
    parser.add_argument("--truth", type=Path, default=None, help="Optional ground truth jsonl file for precision/recall evaluation")
    parser.add_argument("--deterministic", "--no-llm", action="store_true", help="Run in pure deterministic mode without external LLM calls")
    parser.add_argument("--json", action="store_true", help="Output final report as formatted JSON")
    parser.add_argument("--chat", "-i", action="store_true", help="Start continuous interactive chatbot REPL after reconciliation")
    parser.add_argument("--clear-logs", action="store_true", help="Delete all session logs, audit trails, and uploads")
    parser.add_argument("--server", action="store_true", help="Launch FastAPI REST/WebSocket server with web console")
    parser.add_argument("--cli", action="store_true", help="Force CLI mode (skip auto-server)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    
    args = parser.parse_args()

    if args.clear_logs:
        for d in [LOGS_DIR, LOGS_DIR.parent / "audit", LOGS_DIR.parent / "uploads"]:
            if d.exists():
                for f in d.glob("*"):
                    try:
                        if f.is_file():
                            f.unlink()
                        elif f.is_dir():
                            shutil.rmtree(f)
                    except Exception:
                        pass
        print("- **Status**: All session logs, audit files, and uploaded datasets have been cleared.")
        if not args.server and not args.files:
            return

    if args.server:
        run_server(host=args.host, port=args.port)
    elif args.files:
        run_cli(files=args.files, truth=args.truth, auto_ack=True, as_json=args.json, deterministic=args.deterministic, chat=args.chat)
    elif args.cli:
        parser.print_help()
    else:
        # Default: launch web console when no files are provided
        print("# ⚡ Razorpay Reconciliation Agent", flush=True)
        print("No files specified — launching web console...\n", flush=True)
        run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()


```

### recon_agent/sample_data/payments.csv

```csv
order_id,amount,date
ORD_1,1000.00,2026-03-01
ORD_2,2000.00,2026-03-01
ORD_3,3000.00,2026-03-06
ORD_4,500.00,2026-03-02
ORD_4,500.00,2026-03-02
ORD_6,400.00,2026-03-02
ORD_7,700.00,2026-03-02
MIS_800,900.00,2026-03-03

```

### recon_agent/sample_data/bank.csv

```csv
utr,credit,date
ORD_1,1000.00,2026-03-02
ORD_2,1952.80,2026-03-02
ORD_3,3000.00,2026-03-13
ORD_4,500.00,2026-03-03
BATCH,1074.04,2026-03-03
ORD_9,850.00,2026-03-05
REFUND,-250.00,2026-03-05

```

### recon_agent/sample_data/ground_truth.jsonl

```json
{"l_rid": 1, "r_rid": 1, "class": "exact"}
{"l_rid": 2, "r_rid": 2, "class": "fee_deduction"}
{"l_rid": 4, "r_rid": 4, "class": "duplicate_first"}

```

### recon_agent/app/__init__.py

```python


```

### recon_agent/app/config.py

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
LOGS_DIR = DATA_DIR / "logs"
AUDIT_DIR = DATA_DIR / "audit"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
AUDIT_DIR.mkdir(exist_ok=True)


def _load_env_file():
    """Load environment variables from single recon_agent/.env file if present."""
    env_path = BASE_DIR / ".env"
    if env_path.is_file():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


_load_env_file()

DEFAULT_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY", "")

```

### recon_agent/app/pipeline.py

```python
import itertools
import json
import time
import uuid
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, model_validator

from app.core.audit import audit_for
from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import (Actor, DecisionRecord, MatchComponent, MatchedRecord,
                                MessageKind, Policy, PolicyComponent, UnmatchedRecord,
                                VarianceMetrics)
from app.core.dispatcher import breaker_open, dispatch_tool_call, ToolCall
from app.core.states import State, StateMachine
from app.engine import match, qa, report, resolving
from app.engine.match import _sim, fee_explains


class MapArgs(BaseModel):
    tables: dict

class MapResult(BaseModel):
    left_table: str = "payments"
    right_table: str = "bank"
    left_key: str = "order_id"
    right_key: str = "utr"
    left_amount: str | None = "amount"
    right_amount: str | None = "credit"
    left_date: str | None = "date"
    right_date: str | None = "date"

    @model_validator(mode="before")
    @classmethod
    def parse_llm_json(cls, data):
        if not isinstance(data, dict):
            return {}
        res = dict(data)
        if "mappings" in res and isinstance(res["mappings"], list):
            for item in res["mappings"]:
                if isinstance(item, dict):
                    p_val = str(item.get("payments") or item.get("payment") or item.get("left") or "")
                    b_val = str(item.get("bank") or item.get("right") or "")
                    if "id" in p_val or "key" in p_val or "order" in p_val:
                        res["left_key"] = p_val
                        res["right_key"] = b_val
                    elif "amt" in p_val or "amount" in p_val or "credit" in b_val:
                        res["left_amount"] = p_val
                        res["right_amount"] = b_val
                    elif "date" in p_val or "date" in b_val:
                        res["left_date"] = p_val
                        res["right_date"] = b_val
        res.setdefault("left_table", "payments")
        res.setdefault("right_table", "bank")
        res.setdefault("left_key", "order_id")
        res.setdefault("right_key", "utr")
        return res


def _overlap(xs, ys):
    a, b = set(map(str, xs)), set(map(str, ys))
    return len(a & b) / max(min(len(a), len(b)), 1)


class Pipeline:
    def __init__(self, sid: str, auto_ack: bool = False):
        self.sid = sid
        self.auto_ack = auto_ack
        self.sm = StateMachine(sid)
        self.fb: list[str] = []
        self.tables: dict[str, list[dict]] = {}
        self.cfg: dict = {}
        self.schedule = next(iter(REG.fee_schedules.values()), None)
        self.truth: list[dict] = []
        self.profiles: dict = {}
        self._map_cands: list = []
        self._map_conf = 0.0
        self._ambiguous = False

    # ---------- bus helpers ----------
    def _chat(self, text):
        validate_and_route(self.sid, MessageKind.CHAT, {"text": text[:2000]}, "system")

    def _trace(self, event, **d):
        validate_and_route(self.sid, MessageKind.TRACE, {"event": event, "detail": d}, "system")

    def _maybe_ack(self, tools):
        """Never raises. auto_ack=True resumes in-place immediately (CLI/test use).
        auto_ack=False leaves state at HALT for the caller to stop cleanly on."""
        if self.auto_ack:
            self.sm.resume()

    _STEP_FN_ATTR = {
        State.PROFILING: "profile",
        State.MAPPING_PROPOSED: "propose_mapping",
        State.MAPPING_VALIDATED: "validate_mapping",
        State.POLICY_GENERATED: "policy",
        State.DRY_RUN: "dry_run",
        State.EXECUTING: "execute",
        State.INSPECTING: "inspect",
        State.REVISION: "revise",
        State.QA: "qa_state",
        State.RESOLVING: "resolve",
    }

    # ---------- states ----------
    def ingest(self, files, truth=None):
        self.sm.enter(State.INGESTING)
        for f in files:
            try:
                df = pd.read_csv(f) if f.suffix == ".csv" else pd.read_excel(f)
                df.insert(0, "_rid", range(1, len(df) + 1))
                tbl_name = f.stem
                # Strip session ID prefix (e.g., 'd11231d8_payments' -> 'payments')
                if "_" in tbl_name:
                    prefix, rest = tbl_name.split("_", 1)
                    if len(prefix) == 8 and all(c in "0123456789abcdefABCDEF" for c in prefix):
                        tbl_name = rest
                self.tables[tbl_name] = df.to_dict("records")
            except Exception as e:
                self._trace("UNPARSED", file=str(f), err=str(e)[:120])
        if truth:
            self.truth = [json.loads(l) for l in Path(truth).read_text().splitlines() if l]
        return self.sm.transition(State.PROFILING, f"{len(self.tables)} tables")

    def profile(self):
        print(f"- **Step 1/7**: Profiling table schemas and column statistics...", flush=True)
        from app.core.contracts import ColumnProfile
        from app.core.masking import pii_score
        for name, rows in self.tables.items():
            df = pd.DataFrame(rows)
            self.profiles[name] = []
            for c in df.columns:
                if c == "_rid":
                    continue
                s = df[c].astype(str)
                num = pd.to_numeric(df[c], errors="coerce").notna().mean()
                dat = pd.to_datetime(df[c], errors="coerce", format="mixed").notna().mean()
                self.profiles[name].append(ColumnProfile(
                    name=c, dtype=str(df[c].dtype), numeric_ratio=float(num),
                    date_ratio=float(dat), cardinality=float(df[c].nunique() / max(len(df), 1)),
                    null_rate=float(df[c].isna().mean()),
                    min_len=int(s.str.len().min() or 0), max_len=int(s.str.len().max() or 0),
                    sample_values=s.head(3).tolist(),
                    pii_likelihood=max((pii_score(c, v) for v in s.head(5)), default=0.0)))
        return self.sm.transition(State.MAPPING_PROPOSED)

    def _pick(self, t, kind):
        for p in self.profiles[t]:
            if kind == "numeric" and p.numeric_ratio > .8 and p.cardinality > .3:
                return p.name
            if kind == "date" and p.date_ratio > .8 and p.numeric_ratio <= .8:
                return p.name
        return None

    def propose_mapping(self):
        print(f"- **Step 2/7**: Linking schema keys and amounts via mapping tool...", flush=True)
        names = list(self.tables)
        cands = []
        for lt in names:
            for rt in names:
                if lt == rt:
                    continue
                for lc in [p.name for p in self.profiles[lt]]:
                    for rc in [p.name for p in self.profiles[rt]]:
                        ov = _overlap([r.get(lc) for r in self.tables[lt]],
                                      [r.get(rc) for r in self.tables[rt]])
                        if ov >= 0.10:
                            cands.append((ov, lt, lc, rt, rc))
        cands.sort(reverse=True)
        self._map_cands = cands
        tool = ToolCall(name="mapping_semantic", args_schema=MapArgs, result_schema=MapResult,
                        timeout_s=REG["llm_tool_timeout_s"], retries=2,
                        fallback=lambda a: None, cost_budget_usd=0.005)
        llm_map, fb = dispatch_tool_call(
            self.sid, tool, {"tables": {n: [p.name for p in self.profiles[n]] for n in names}})
        if llm_map is None and fb:
            self.fb.append(f"mapping_heuristic:{fb}")
        if isinstance(llm_map, MapResult):
            self.cfg = llm_map.model_dump()
            self.cfg["left_amount"] = self.cfg.get("left_amount") or self._pick(self.cfg["left_table"], "numeric")
            self.cfg["right_amount"] = self.cfg.get("right_amount") or self._pick(self.cfg["right_table"], "numeric")
            self.cfg["left_date"] = self.cfg.get("left_date") or self._pick(self.cfg["left_table"], "date")
            self.cfg["right_date"] = self.cfg.get("right_date") or self._pick(self.cfg["right_table"], "date")
            self._map_conf = 0.9
        elif cands:
            ov, lt, lc, rt, rc = cands[0]
            self._ambiguous = len(cands) > 1 and (cands[0][0] - cands[1][0]) <= REG["mapping_ambiguity_delta"]
            self.cfg = {"left_table": lt, "right_table": rt, "left_key": lc, "right_key": rc,
                        "left_amount": self._pick(lt, "numeric"), "right_amount": self._pick(rt, "numeric"),
                        "left_date": self._pick(lt, "date"), "right_date": self._pick(rt, "date")}
            self._map_conf = min(0.45 + ov / 2, 0.95)
        else:
            self.sm.halt("no linkable columns")
            self._maybe_ack([])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.MAPPING_PROPOSED
                return False
        if breaker_open(self.sid, "mapping_semantic"):
            self.sm.halt("circuit open: mapping_semantic", tools=["mapping_semantic"])
            self._maybe_ack(["mapping_semantic"])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.MAPPING_VALIDATED
                return False
        return self.sm.transition(State.MAPPING_VALIDATED)

    def validate_mapping(self):
        audit_for(self.sid).append(DecisionRecord(
            decision_id=uuid.uuid4().hex, ts=pd.Timestamp.now(tz="UTC").to_pydatetime(),
            state="MAPPING_VALIDATED", actor=Actor.SYSTEM, decision_kind="mapping",
            proposal={"candidates": [list(c[1:]) for c in self._map_cands[:3]]},
            final={k: self.cfg.get(k) for k in ("left_table", "right_table", "left_key", "right_key")},
            confidence=self._map_conf, evidence=[]).model_dump(mode="json"))
        if self._map_conf < REG["mapping_review_floor"]:
            self.sm.halt("mapping below review floor")
            self._maybe_ack([])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.MAPPING_VALIDATED
                return False
        if self._ambiguous or self._map_conf < REG["mapping_auto_accept"]:
            self._chat(f"Mapping confidence {self._map_conf:.2f} — proceeding with trace visibility.")
        return self.sm.transition(State.POLICY_GENERATED)

    def policy(self):
        print(f"- **Step 3/7**: Synthesizing policy components & tolerance windows...", flush=True)
        comps = [PolicyComponent(component=c, params={}, precedence=i)
                 for i, c in enumerate(MatchComponent, 1)]
        comps[3].params = {"tolerance": 0.01, "window_days": 3}
        self.policy_doc = Policy(
            components=comps, baseline_match_rate=0.0,
            baseline_computed_at=pd.Timestamp.now(tz="UTC").to_pydatetime(),
            baseline_constants_version=REG.version)
        self.cfg.setdefault("tolerance", 0.01)
        self.cfg.setdefault("window_days", 3)
        return self.sm.transition(State.DRY_RUN)

    # ---------- scoring core ----------
    def _score_all(self, rows_l, rows_r):
        self._last_cand_scores = []
        matched, unmatched, dups, per = [], [], [], []
        unmatched_ctx = []
        lkeys = {}
        for l in rows_l:
            lkeys.setdefault(str(l[self.cfg["left_key"]]), []).append(l)
        dup_keys = {k for k, v in lkeys.items() if len(v) > 1}
        seen_dup = set()
        used_r = set()
        soft_paired_r = set()          # T1: r's already represented via an l-pairing

        # Index rows_r by key for O(1) candidate lookup on exact matches
        r_by_key = {}
        rk = self.cfg["right_key"]
        for r in rows_r:
            r_by_key.setdefault(str(r.get(rk)), []).append(r)

        def mk_unmatched(l, r, v, ev, sd):
            side = "L" if l is not None else "R"
            ref_key = self.cfg["left_key"] if l is not None else self.cfg["right_key"]
            rec = UnmatchedRecord(side=side, rid=(l or r)["_rid"],
                                  ref=str((l or r).get(ref_key)), delta=sd, match_confidence=v)
            return rec, ev

        is_large = len(rows_r) > 300
        for l in rows_l:
            key = str(l[self.cfg["left_key"]])
            if key in dup_keys and key not in seen_dup:
                dups.append({"side": "L", "key": key, "rids": [x["_rid"] for x in lkeys[key]]})
                seen_dup.add(key)

            # Check direct exact key matches first for blazing fast execution on large data
            direct_cands = [r for r in r_by_key.get(key, []) if r["_rid"] not in used_r]
            if direct_cands:
                cands = [(r, *match.score_pair(self.sid, l, r, self.cfg, self.schedule, self.fb))
                         for r in direct_cands]
                cands = [(r, v, c, e, d) for (r, v, c, e, d) in cands if v >= REG["match_review_floor"]]
            else:
                cands = []

            # If no direct match meets threshold, check other candidates
            if not cands:
                search_pool = [r for r in rows_r if r["_rid"] not in used_r]
                if is_large and len(search_pool) > 200:
                    # On large datasets, filter candidates by amount / date proximity
                    la = float(l.get(self.cfg.get("left_amount", ""), 0) or 0)
                    ra_key = self.cfg.get("right_amount", "")
                    search_pool = sorted(
                        search_pool,
                        key=lambda r: abs(la - float(r.get(ra_key, 0) or 0)) if ra_key else 0
                    )[:150]

                cands = [(r, *match.score_pair(self.sid, l, r, self.cfg, self.schedule, self.fb))
                         for r in search_pool]
                cands = [(r, v, c, e, d) for (r, v, c, e, d) in cands if v >= REG["match_review_floor"]]

            self._last_cand_scores.extend(v for _, v, _, _, _ in cands)
            if not cands:
                rec, ev = mk_unmatched(l, None, None, [], None)
                unmatched.append(rec)
                unmatched_ctx.append((rec, None, ev, None))
                continue
            r, v, comps, ev, sd = max(cands, key=lambda t: t[1])
            if v >= REG["match_auto_threshold"]:
                used_r.add(r["_rid"])
                matched.append(MatchedRecord(l_rid=l["_rid"], r_rid=r["_rid"],
                                             composite_score=v, components=comps,
                                             policy_version=REG.version))
                per.append({"l_id": l["_rid"], "r_id": r["_rid"], "abs": abs(sd or 0), "signed": sd})
            else:
                rec, ev = mk_unmatched(l, r, v, ev, sd)
                unmatched.append(rec)
                unmatched_ctx.append((rec, r, ev, sd))
                soft_paired_r.add(r["_rid"])          # T1: don't list this r again below
        for r in rows_r:
            if r["_rid"] not in used_r and r["_rid"] not in soft_paired_r:   # T1
                rec, ev = mk_unmatched(None, r, None, [], None)
                unmatched.append(rec)
                unmatched_ctx.append((rec, None, ev, None))

        var = VarianceMetrics(abs_sum=sum(p["abs"] for p in per),
                              signed_sum=sum(p["signed"] for p in per), per_record=per)
        from app.core.contracts import ExecutionResult
        self._last_unmatched_ctx = unmatched_ctx
        return ExecutionResult(matched=matched, unmatched=unmatched,
                               duplicates=dups, splits=[], variance=var)

    def dry_run(self):
        print(f"- **Step 4/7**: Performing dry-run calibration on sample rows...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]][:100]
        rows_r = self.tables[self.cfg["right_table"]]
        t0 = time.time()
        res = self._score_all(rows_l, rows_r)
        self.policy_doc.baseline_match_rate = len(res.matched) / max(len(rows_l), 1)
        mean_cand = sum(self._last_cand_scores) / len(self._last_cand_scores) if self._last_cand_scores else 0.0
        if mean_cand < REG["calibration_sanity_floor"]:
            self._trace("CALIBRATION_DRIFT_WARNING", mean_cand=round(mean_cand, 3))
        self._trace("dry_run_done", s=round(time.time() - t0, 2),
                    baseline=round(self.policy_doc.baseline_match_rate, 3),
                    mean_cand=round(mean_cand, 3))
        return self.sm.transition(State.EXECUTING)

    def execute(self):
        print(f"- **Step 5/7**: Executing multi-attribute matching engine...", flush=True)
        t0 = time.time()
        self.exec_res = self._score_all(self.tables[self.cfg["left_table"]],
                                        self.tables[self.cfg["right_table"]])
        self._exec_s = max(time.time() - t0, 1e-6)
        return self.sm.transition(State.INSPECTING)

    def _inspect_metrics(self):
        r = self.exec_res
        total = len(r.matched) + len(r.unmatched)
        self.match_rate = len(r.matched) / max(total, 1)
        nrows = sum(len(t) for t in self.tables.values())
        self.throughput = nrows / max(getattr(self, "_exec_s", 1.0), 1e-6)
        pred = {(m.l_rid, m.r_rid) for m in r.matched}
        truth = {(t["l_rid"], t["r_rid"]) for t in self.truth}
        self.precision = (len(pred & truth) / len(pred)) if pred else None
        self.recall = (len(pred & truth) / len(truth)) if truth else None

    def inspect(self):
        self._inspect_metrics()
        if self.match_rate < REG["revision_match_rate_threshold"]:
            return self.sm.transition(State.REVISION)
        return self.sm.transition(State.QA)

    def revise(self):
        it, t0 = 0, time.time()
        while (self.match_rate < REG["revision_match_rate_threshold"]
               and it < REG["revision_iteration_cap"]
               and time.time() - t0 < REG["revision_time_cap_s"]):
            old = self.cfg["tolerance"]
            self.cfg["tolerance"] = round(old * 1.2, 4)
            self._trace("revision", it=it, tol=self.cfg["tolerance"])
            self.execute()
            self._inspect_metrics()
            if self.policy_doc.baseline_match_rate - self.match_rate > REG["regression_reject_delta"]:
                self.cfg["tolerance"] = old
                self._trace("revision_regression_rejected", it=it)
                break                                   # T7: stop repeating an already-rejected tweak
            it += 1
        if self.match_rate < REG["revision_match_rate_threshold"]:
            self.sm.halt("revision caps exhausted or regression rejected")   # T2: restored
            self._maybe_ack([])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.QA
                return False
        return self.sm.transition(State.QA)

    # ---------- QA / resolving ----------
    def _ctx(self, side, l, r, rows_l, rows_r, sd):
        lk, rk = self.cfg["left_key"], self.cfg["right_key"]
        tol = self.cfg["tolerance"]
        ctx = {k: ([] if k in ("dup_rids", "split_targets") else False) for k in qa.CTX_KEYS}
        if side == "L" and l is not None:
            key = str(l[lk])
            ctx["dup_rids"] = [x["_rid"] for x in rows_l if str(x[lk]) == key and x["_rid"] != l["_rid"]]
            cands = [x for x in rows_r if str(x[rk]) == key]
            ctx["single_target"] = len(cands) == 1
            if cands and self.cfg.get("left_amount"):
                a = float(l[self.cfg["left_amount"]])
                rv = float(cands[0][self.cfg["right_amount"]])
                ctx["fee_match"] = fee_explains(a, rv, self.schedule, tol)
                ctx["partial"] = rv < a and not ctx["fee_match"]
                if self.cfg.get("left_date"):
                    dd = match._busdays(match._d(l[self.cfg["left_date"]]),
                                        match._d(cands[0][self.cfg["right_date"]]))
                    ctx["date_only_mismatch"] = dd > self.cfg["window_days"] and (
                        abs(a - rv) <= tol or ctx["fee_match"])
            if not cands:
                # T6: Corroborate fuzzy key with amount/fee consistency
                a = float(l[self.cfg["left_amount"]]) if self.cfg.get("left_amount") else None
                search_r = rows_r if len(rows_r) <= 500 else [
                    x for x in rows_r if abs(a - float(x.get(self.cfg.get("right_amount", ""), 0) or 0)) <= 1000
                ][:100]
                if a is not None and self.cfg.get("right_amount"):
                    ctx["fuzzy_key"] = any(
                        _sim(key, str(x[rk])) >= 0.8 and (
                            abs(a - float(x[self.cfg["right_amount"]])) <= tol
                            or fee_explains(a, float(x[self.cfg["right_amount"]]), self.schedule, tol)
                        )
                        for x in search_r
                    )
                else:
                    ctx["fuzzy_key"] = max((_sim(key, str(x[rk])) for x in search_r), default=0) >= 0.85
        if side == "R" and r is not None:
            rv = float(r[self.cfg["right_amount"]]) if self.cfg.get("right_amount") else 0.0
            ctx["negative_credit"] = rv < 0
            nets = []
            for x in rows_l:
                a = float(x.get(self.cfg["left_amount"], 0))
                nets.append((x["_rid"], a - (match.compute_fee(a, self.schedule) if self.schedule else 0)))
            # Bounded pool search for split combinations to prevent exponential explosion on large files
            valid_nets = [x for x in nets if 0 < x[1] <= rv + tol]
            pool = valid_nets[:40]
            for k in (2, 3):
                for combo in itertools.combinations(pool, k):
                    if abs(sum(v for _, v in combo) - rv) <= tol:
                        ctx["split_targets"] = [i for i, _ in combo]
                        break
                if ctx["split_targets"]:
                    break
        return ctx

    def qa_state(self):
        print(f"- **Step 6/7**: Classifying exceptions & verifying invariant proofs...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]]
        rows_r = self.tables[self.cfg["right_table"]]
        self.queue = []
        for rec, r_cand, ev, sd in self._last_unmatched_ctx:
            if rec.side == "L":
                l = next(x for x in rows_l if x["_rid"] == rec.rid)
                ctx = self._ctx("L", l, r_cand, rows_l, rows_r, sd)
            else:
                r = next(x for x in rows_r if x["_rid"] == rec.rid)
                ctx = self._ctx("R", None, r, rows_l, rows_r, sd)
            rec.reason = qa.classify(rec, ctx)
            self.queue.append({"rec": rec, "ctx": ctx, "pieces": ev})
        return self.sm.transition(State.RESOLVING)

    def resolve(self):
        for item in self.queue:
            rec, pieces, ctx = item["rec"], item["pieces"], item.get("ctx", {})
            conf = resolving.exception_confidence(len(pieces), rec.reason, None)
            action = resolving.decide_action(conf, len(pieces), rec.reason)
            explanation = resolving.generate_explanation(rec, ctx)
            rec.explanation = explanation
            item["action"], item["conf"], item["explanation"] = action, conf, explanation
            actor = Actor.SYSTEM if action in ("auto_resolve", "mark_pending", "request_confirmation") \
                else Actor.FALLBACK
            audit_for(self.sid).append(DecisionRecord(
                decision_id=uuid.uuid4().hex, ts=pd.Timestamp.now(tz="UTC").to_pydatetime(),
                state="RESOLVING", actor=actor, decision_kind="exception_resolve",
                proposal={"category": rec.reason.value, "explanation": explanation},
                final={"action": action},
                confidence=conf, evidence=pieces).model_dump(mode="json"))
        return self.sm.transition(State.AGGREGATING)

    def aggregate(self, elapsed: float):
        print(f"- **Step 7/7**: Aggregating financial balances & signing cryptographic audit ledger...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]]
        rows_r = self.tables[self.cfg["right_table"]]
        g = sum(float(x.get(self.cfg["left_amount"], 0)) for x in rows_l)
        n = sum(float(x.get(self.cfg["right_amount"], 0)) for x in rows_r)
        mv = sum(float(x.get(self.cfg["left_amount"], 0)) for x in rows_l
                 if x["_rid"] in {m.l_rid for m in self.exec_res.matched})
        totals = {"gross": round(g, 2), "net": round(n, 2), "fees": round(g - n, 2),
                  "matched_value": round(mv, 2), "exception_value": round(g - mv, 2)}
        self.final = report.build_final_report(
            self.sid, match_rate=self.match_rate, precision_vs_truth=self.precision,
            recall_vs_truth=self.recall, throughput_rows_per_sec=self.throughput,
            exceptions=self.queue, elapsed_seconds=elapsed, totals=totals,
            llm_user_disagreements=[], fallback_events=self.fb)
        return self.sm.transition(State.ARCHIVED)

    # ---------- driver ----------
    def run(self, files, truth=None):
        self._t0 = time.time()
        self.ingest(files, truth)
        return self.continue_run()

    def continue_run(self):
        """Re-entrant driver: dispatches on self.sm.state. A HALT stops this
        cleanly (returns None) without losing self.tables/self.cfg/etc; calling
        this again after sm.resume() picks up exactly where it left off."""
        while self.sm.state not in (State.AGGREGATING, State.ARCHIVED, State.ABORT_CONFIRMED):
            attr = self._STEP_FN_ATTR.get(self.sm.state)
            if attr is None:
                break
            ok = getattr(self, attr)()
            if self.sm.state == State.HALT:
                return None                      # T3: stop, don't crash the thread
            if ok is False:
                return None
        if self.sm.state == State.RESOLVING or getattr(self, "queue", None) is not None:
            if self.sm.state != State.ARCHIVED:
                self.aggregate(time.time() - getattr(self, "_t0", time.time()))
        if getattr(self, "final", None):
            validate_and_route(self.sid, MessageKind.ARTIFACT,
                               {"kind": "report", "summary": self.final.model_dump(),
                                "confidence_threshold": REG["match_auto_threshold"],
                                "fallback_events": self.fb}, "engine")
            self._chat(f"Reconciliation complete: {self.final.match_rate:.0%} matched, "
                       f"{self.final.honest_exception_count} exceptions, "
                       f"{self.final.auto_resolved_count} auto-resolved.")
        return self.final

```

### recon_agent/app/core/__init__.py

```python


```

### recon_agent/app/core/contracts.py

```python
from datetime import date, datetime
from enum import Enum
from typing import Callable, Optional, Type

from pydantic import BaseModel, ConfigDict, Field


class MessageKind(str, Enum):
    CHAT = "chat"
    ARTIFACT = "artifact"
    TRACE = "trace"
    CONTROL = "control"

class ConfidenceScope(str, Enum):
    MAPPING = "mapping"
    MATCH = "match"
    EXCEPTION = "exception"

class Actor(str, Enum):
    LLM = "llm"
    USER = "user"
    SYSTEM = "system"
    FALLBACK = "fallback"

class EvidencePiece(str, Enum):
    KEY_MATCH = "key_match"
    AMOUNT_WITHIN_TOL = "amount_within_tol"
    DATE_WITHIN_WINDOW = "date_within_window"
    FEE_MODEL_MATCH = "fee_model_match"

class HypothesisCategory(str, Enum):
    DUPLICATE = "duplicate"
    SPLIT = "split"
    PARTIAL_PAYMENT = "partial_payment"
    REFUND_OFFSET = "refund_offset"
    FEE_DEDUCTION = "fee_deduction"
    TAX_WITHHOLDING = "tax_withholding"
    CURRENCY_CONVERSION = "currency_conversion"
    TEMPORAL_DRIFT = "temporal_drift"
    COUNTERPARTY_MISMATCH = "counterparty_mismatch"
    AMOUNT_DELTA = "amount_delta"
    UNCLASSIFIED = "unclassified"

HYPOTHESIS_PRIORITY = {
    HypothesisCategory.DUPLICATE: 1,
    HypothesisCategory.SPLIT: 2,
    HypothesisCategory.PARTIAL_PAYMENT: 3,
    HypothesisCategory.REFUND_OFFSET: 4,
    HypothesisCategory.FEE_DEDUCTION: 5,
    HypothesisCategory.TAX_WITHHOLDING: 6,
    HypothesisCategory.CURRENCY_CONVERSION: 7,
    HypothesisCategory.TEMPORAL_DRIFT: 8,
    HypothesisCategory.COUNTERPARTY_MISMATCH: 9,
    HypothesisCategory.AMOUNT_DELTA: 10,
    HypothesisCategory.UNCLASSIFIED: 11,
}

class MatchComponent(str, Enum):
    EXACT_KEY = "exact_key"
    EXACT_AMOUNT = "exact_amount"
    DATE_WINDOW = "date_window"
    AMOUNT_TOL = "amount_tol"
    CURRENCY_NORM = "currency_norm"
    DUP_DETECT = "dup_detect"
    SPLIT_DETECT = "split_detect"
    FUZZY_KEY = "fuzzy_key"
    SEMANTIC_HINT = "semantic_hint"


class ChatPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=2000)

class ArtifactPayload(BaseModel):
    kind: str
    schema_version: str = "1.0"
    rows: Optional[list[dict]] = None
    summary: dict = {}
    confidence_threshold: float
    fallback_events: list[str] = []

class TracePayload(BaseModel):
    event: str
    detail: dict = {}

class ControlPayload(BaseModel):
    event: str
    state: Optional[str] = None
    abort_token: Optional[str] = None
    detail: dict = {}

SCHEMAS = {
    MessageKind.CHAT: ChatPayload,
    MessageKind.ARTIFACT: ArtifactPayload,
    MessageKind.TRACE: TracePayload,
    MessageKind.CONTROL: ControlPayload,
}


class ToolCall(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    args_schema: Type[BaseModel]
    result_schema: Type[BaseModel]
    timeout_s: float
    retries: int
    fallback: Callable
    cost_budget_usd: float

class FeeSchedule(BaseModel):
    provider: str
    schedule_id: str
    version: str
    effective_from: date
    effective_until: Optional[date] = None
    model_type: str
    params: dict
    gst_rate: float = 0.0
    currency: str = "INR"

class ConfidenceScore(BaseModel):
    scope: ConfidenceScope
    value: float = Field(ge=0, le=1)
    components: dict[str, float]
    constants_version: str
    constants_loaded_at: datetime

class DecisionRecord(BaseModel):
    decision_id: str
    ts: datetime
    state: str
    actor: Actor
    decision_kind: str
    proposal: dict
    final: dict
    overridden: bool = False
    override_reason: Optional[str] = None
    confidence: float
    evidence: list[EvidencePiece]
    fallback_used: Optional[str] = None

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    numeric_ratio: float
    date_ratio: float
    cardinality: float
    null_rate: float
    min_len: int
    max_len: int
    sample_values: list[str]
    pii_likelihood: float

class PolicyComponent(BaseModel):
    component: MatchComponent
    params: dict
    enabled: bool = True
    precedence: int

class Policy(BaseModel):
    components: list[PolicyComponent]
    generated_from: str = "deterministic_library_v0"
    revision_history: list[dict] = []
    baseline_match_rate: float
    baseline_source: str = "dry_run_subset"
    baseline_computed_at: datetime
    baseline_constants_version: str

class MatchedRecord(BaseModel):
    l_rid: int
    r_rid: int
    composite_score: float
    components: dict[str, float]
    policy_version: str

class UnmatchedRecord(BaseModel):
    side: str
    rid: int
    ref: Optional[str] = None
    reason: HypothesisCategory = HypothesisCategory.UNCLASSIFIED
    delta: Optional[float] = None
    match_confidence: Optional[float] = None
    explanation: Optional[str] = None

class VarianceMetrics(BaseModel):
    abs_sum: float
    pct_avg: float = 0.0
    signed_sum: float
    per_record: list[dict]

class ExecutionResult(BaseModel):
    matched: list[MatchedRecord]
    unmatched: list[UnmatchedRecord]
    duplicates: list[dict]
    splits: list[dict]
    variance: VarianceMetrics

class FinalReport(BaseModel):
    match_rate: float
    precision_vs_truth: Optional[float] = None
    recall_vs_truth: Optional[float] = None
    throughput_rows_per_sec: float
    honest_exception_count: int
    auto_resolved_count: int
    escalated_count: int
    unresolved_count: int
    total_gross: float
    total_net: float
    total_fees: float
    matched_value: float
    exception_value: float
    cost_usd: float
    cost_estimated: bool = False
    elapsed_seconds: float
    llm_user_disagreements: list[dict] = []
    fallback_events: list[str] = []
    constants_version: str
    retention_note: str
    storage_backend: str = "local_hash_chain"

```

### recon_agent/app/core/constants.py

```python
from datetime import datetime

import yaml
from pydantic import BaseModel

from app.core.contracts import FeeSchedule


class Constant(BaseModel):
    name: str
    value: float
    scope: str
    derivation_method: str = "manual_default"
    derived_from: str
    valid_range: list[float] | None = None
    gates: str
    unit: str | None = None


class Registry:
    def __init__(self, path=None):
        if path is None:
            from app.config import BASE_DIR
            path = BASE_DIR / "constants_v0.yaml"
        raw = yaml.safe_load(open(path))
        self.version = raw["version"]
        self.loaded_at = datetime.now()
        self._c = {c["name"]: Constant(**c) for c in raw["constants"]}
        self.fee_schedules = {fs["schedule_id"]: FeeSchedule(**fs)
                              for fs in raw.get("fee_schedules", [])}
        for c in self._c.values():
            if c.valid_range and not c.valid_range[0] <= c.value <= c.valid_range[1]:
                raise ValueError(f"{c.name}={c.value} outside {c.valid_range}")
        for scope in ("mapping", "match", "exception"):
            ws = [c.value for c in self._c.values() if c.name.startswith(f"w_{scope}_")]
            if ws and abs(sum(ws) - 1.0) > 1e-6:
                raise ValueError(f"{scope} weights sum to {sum(ws)}")

    def __getitem__(self, k):
        return self._c[k].value


REG = Registry()

```

### recon_agent/app/core/audit.py

```python
import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

AUDIT_DIR = Path(os.getenv("RECON_AUDIT_DIR", "data/audit"))


class AuditLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.records = []
        self._prev = "GENESIS"
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                r = json.loads(line)
                self.records.append(r)
                self._prev = r["this_hash"]
        self._fh = open(self.path, "a", encoding="utf-8")

    def append(self, payload: dict):
        with self._lock:
            seq = len(self.records)
            canon = json.dumps({"seq": seq, "payload": payload, "prev": self._prev},
                               sort_keys=True, default=str)
            h = hashlib.sha256(canon.encode()).hexdigest()
            rec = {"seq": seq, "ts": datetime.now(timezone.utc).isoformat(),
                   "payload": payload, "prev_hash": self._prev, "this_hash": h}
            self._fh.write(json.dumps(rec, default=str) + "\n")
            self._fh.flush()
            os.fsync(self._fh.fileno())
            self.records.append(rec)
            self._prev = h

    def verify(self) -> bool:
        prev = "GENESIS"
        for line in self.path.read_text().splitlines():
            r = json.loads(line)
            canon = json.dumps({"seq": r["seq"], "payload": r["payload"], "prev": prev},
                               sort_keys=True, default=str)
            if r["prev_hash"] != prev or hashlib.sha256(canon.encode()).hexdigest() != r["this_hash"]:
                return False
            prev = r["this_hash"]
        return True


_LOGS: dict[str, AuditLog] = {}
_LOGS_LOCK = threading.Lock()


def audit_for(session_id: str) -> AuditLog:
    with _LOGS_LOCK:
        if session_id not in _LOGS:
            from app import config
            audit_dir = getattr(config, "AUDIT_DIR", AUDIT_DIR)
            _LOGS[session_id] = AuditLog(audit_dir / f"{session_id}.audit.jsonl")
        return _LOGS[session_id]

```

### recon_agent/app/core/channels.py

```python
from pydantic import ValidationError

from app.core.audit import audit_for
from app.core.contracts import MessageKind, SCHEMAS
from app.core.masking import apply_masking

_subscribers: dict[MessageKind, list] = {k: [] for k in MessageKind}


def subscribe(kind: MessageKind, fn):
    _subscribers[kind].append(fn)


def validate_and_route(session_id: str, kind: MessageKind, payload: dict, source: str):
    try:
        model = SCHEMAS[kind].model_validate(payload)
    except ValidationError as e:
        audit_for(session_id).append({
            "event": "CONTRACT_VIOLATION", "session": session_id,
            "kind": kind.value, "source": source, "err": str(e)[:200]})
        return None
    if kind == MessageKind.ARTIFACT:
        model = apply_masking(model)
    for fn in _subscribers[kind]:
        fn(session_id, model, source)
    return model

```

### recon_agent/app/core/masking.py

```python
import re

from app.core.constants import REG
from app.core.contracts import ArtifactPayload

_PAT = [(re.compile(r"[\w.+-]+@[\w-]+\.\w+"), 1.0),
        (re.compile(r"^\+?\d[\d\s-]{9,14}$"), 0.9),
        (re.compile(r"^[A-Z]{5}\d{4}[A-Z]$"), 0.8),
        (re.compile(r"^\d{12}$"), 0.75)]
_HINTS = ("email", "phone", "mobile", "pan", "aadhaar", "address")


def pii_score(field: str, value) -> float:
    if value is None:
        return 0.0
    s = str(value)
    for rx, sc in _PAT:
        if rx.match(s):
            return sc
    return 0.75 if any(h in field.lower() for h in _HINTS) else 0.0


def apply_masking(m: ArtifactPayload) -> ArtifactPayload:
    if not m.rows:
        return m
    masked = review = 0
    for row in m.rows:
        for k, v in row.items():
            sc = pii_score(k, v)
            if sc >= REG["pii_mask_threshold"]:
                row[k] = "[MASKED:pii]"
                masked += 1
            elif sc >= REG["pii_review_threshold"]:
                review += 1
    if masked:
        m.summary["pii_masked_fields"] = masked
    if review:
        m.summary["pii_review_needed"] = review
    return m

```

### recon_agent/app/core/cost.py

```python
import threading

from app.core.constants import REG


class CostTracker:
    def __init__(self, cap_usd: float):
        self.cap = cap_usd
        self.total = 0.0
        self.estimated_any = False
        self._lock = threading.Lock()

    def authorize(self, budget_usd: float) -> bool:
        with self._lock:
            return self.total + budget_usd <= self.cap

    def record(self, usd: float, estimated: bool = False):
        with self._lock:
            self.total += usd
            self.estimated_any = self.estimated_any or estimated


_TRACKERS: dict[str, CostTracker] = {}


def tracker_for(session_id: str) -> CostTracker:
    if session_id not in _TRACKERS:
        _TRACKERS[session_id] = CostTracker(REG["session_cost_cap_usd"])
    return _TRACKERS[session_id]

```

### recon_agent/app/core/llm_client.py

```python
import json
import os
import re
import urllib.request
from typing import List, Dict, Tuple

from app.config import DEFAULT_API_KEY
from app.core.constants import REG

# Model configuration: Gemma 4 31B
MODEL = os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL", "gemma-4-31b-it"))

_last = {"in": 0, "out": 0, "estimated": False}


def resolve_model_slug(model_name: str) -> str:
    """Normalize model slug for Google Generative Language API endpoints."""
    m = model_name.strip()
    if m in ("gemma-4-31b", "gemma-31b"):
        return "gemma-4-31b-it"
    if m in ("gemma-4b", "gemma-4b-it", "gemma-4-26b"):
        return "gemma-4-26b-a4b-it"
    return m


def get_api_key() -> str:
    return os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or DEFAULT_API_KEY


def _extract_json(text: str) -> dict:
    text = text.strip()
    if "```" in text:
        blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        for b in blocks:
            b = b.strip()
            if b.startswith("{") and b.endswith("}"):
                try:
                    return json.loads(b)
                except Exception:
                    pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    return json.loads(text)


def json_chat(tool_name: str, args: dict, timeout: float = 25.0) -> dict:
    key = get_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set — deterministic fallback will be used")

    actual_model = resolve_model_slug(MODEL)

    if tool_name == "mapping_semantic":
        schema_hint = 'JSON with keys: {"left_table": str, "right_table": str, "left_key": str, "right_key": str, "left_amount": str, "right_amount": str, "left_date": str, "right_date": str}'
    elif tool_name == "semantic_similarity":
        schema_hint = 'JSON with keys: {"score": float (0.0 to 1.0)}'
    else:
        schema_hint = "a valid JSON object matching the tool parameters"

    prompt = (
        f"You are the financial reconciliation system tool '{tool_name}'.\n"
        f"Strict Requirement: Output ONLY a single raw JSON object ({schema_hint}).\n"
        f"Do NOT include explanations, markdown wrappers, preamble, or thoughts.\n\n"
        f"Input Data:\n{json.dumps(args, default=str)}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{actual_model}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0
        }
    }

    print(f"  [LLM] Invoking {actual_model} for tool '{tool_name}' ...", flush=True)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())

    raw_msg = d["candidates"][0]["content"]["parts"][0]["text"]
    u = d.get("usageMetadata", {})
    _last["estimated"] = "usageMetadata" not in d
    _last["in"] = u.get("promptTokenCount", len(prompt) // 4)
    _last["out"] = u.get("candidatesTokenCount", len(raw_msg) // 4)
    print(f"  [LLM] Received response from {actual_model} ({_last['in']} in / {_last['out']} out tokens | cost: ${last_cost_usd():.6f})", flush=True)

    return _extract_json(raw_msg)


def conversational_chat(messages: List[Dict[str, str]], system_instruction: str, timeout: float = 25.0) -> Tuple[str, float]:
    """
    Multi-turn conversation with Gemma 4 31B grounded strictly in current active session context.
    Returns (assistant_reply, cost_usd).
    """
    key = get_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")

    actual_model = resolve_model_slug(MODEL)

    formatted_contents = []
    for msg in messages:
        role = "user" if msg.get("role") in ("user", "human") else "model"
        formatted_contents.append({
            "role": role,
            "parts": [{"text": msg.get("content", "")}]
        })

    # If first message is from model or empty, prepend system instruction to first user message
    if formatted_contents and formatted_contents[0]["role"] == "user":
        formatted_contents[0]["parts"][0]["text"] = (
            f"[SYSTEM INSTRUCTION]:\n{system_instruction}\n\n"
            f"[USER MESSAGE]:\n{formatted_contents[0]['parts'][0]['text']}"
        )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{actual_model}:generateContent?key={key}"
    payload = {
        "contents": formatted_contents,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())

    raw_reply = d["candidates"][0]["content"]["parts"][0]["text"].strip()
    u = d.get("usageMetadata", {})
    t_in = u.get("promptTokenCount", sum(len(m.get('content', '')) for m in messages) // 4)
    t_out = u.get("candidatesTokenCount", len(raw_reply) // 4)
    call_cost = (t_in / 1000 * REG["cost_llm_in_per_1k_usd"]) + (t_out / 1000 * REG["cost_llm_out_per_1k_usd"])
    
    return raw_reply, call_cost


def last_cost_usd() -> float:
    return (_last["in"] / 1000 * REG["cost_llm_in_per_1k_usd"]
            + _last["out"] / 1000 * REG["cost_llm_out_per_1k_usd"])


def last_estimated() -> bool:
    return _last["estimated"]

```

### recon_agent/app/core/dispatcher.py

```python
import time

from pydantic import ValidationError

from app.core import llm_client
from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import MessageKind, ToolCall
from app.core.cost import tracker_for

_breakers: dict[tuple[str, str], int] = {}


def breaker_open(sid: str, tool: str) -> bool:
    return _breakers.get((sid, tool), 0) >= REG["circuit_breaker_failure_count"]


def _count_failure(sid: str, tool: str):
    k = (sid, tool)
    _breakers[k] = _breakers.get(k, 0) + 1
    if _breakers[k] == REG["circuit_breaker_failure_count"]:
        validate_and_route(sid, MessageKind.CONTROL,
                           {"event": "CIRCUIT_BREAKER_OPEN",
                            "detail": {"tool": tool, "session": sid}}, "system")


def reset_breaker(sid: str, tool: str):
    _breakers[(sid, tool)] = 0


def dispatch_tool_call(sid: str, tool: ToolCall, args: dict):
    try:
        validated = tool.args_schema.model_validate(args)
    except ValidationError as e:
        validate_and_route(sid, MessageKind.TRACE,
                           {"event": f"args_rejected:{tool.name}",
                            "detail": {"err": str(e)[:200]}}, "system")
        return tool.fallback(args), tool.name
    if breaker_open(sid, tool.name):
        return tool.fallback(args), tool.name
    if not tracker_for(sid).authorize(tool.cost_budget_usd):
        validate_and_route(sid, MessageKind.CONTROL,
                           {"event": "BUDGET_EXCEEDED",
                            "detail": {"tool": tool.name}}, "system")
        return tool.fallback(args), tool.name
    err = None
    for _ in range(tool.retries + 1):
        t0 = time.time()
        try:
            raw = llm_client.json_chat(tool.name, validated.model_dump(),
                                       timeout=tool.timeout_s)
            result = tool.result_schema.model_validate(raw)
            usd = llm_client.last_cost_usd()
            est = llm_client.last_estimated()
            tracker_for(sid).record(usd, estimated=est)
            if usd > tool.cost_budget_usd:
                validate_and_route(sid, MessageKind.TRACE,
                                   {"event": f"cost_overrun:{tool.name}",
                                    "detail": {"usd": usd}}, "system")
            _breakers[(sid, tool.name)] = 0
            validate_and_route(sid, MessageKind.TRACE,
                               {"event": f"tool_ok:{tool.name}",
                                "detail": {"s": round(time.time() - t0, 2),
                                           "usd": round(usd, 6), "estimated": est}}, "llm")
            return result, None
        except Exception as e:
            err = e
            _count_failure(sid, tool.name)
    validate_and_route(sid, MessageKind.TRACE,
                       {"event": f"llm_fallback:{tool.name}:{type(err).__name__}"}, "system")
    return tool.fallback(args), tool.name

```

### recon_agent/app/core/states.py

```python
import uuid
from enum import Enum

from app.core.channels import validate_and_route
from app.core.contracts import MessageKind
from app.core.dispatcher import reset_breaker


class State(str, Enum):
    INGESTING = "INGESTING"
    PROFILING = "PROFILING"
    MAPPING_PROPOSED = "MAPPING_PROPOSED"
    MAPPING_VALIDATED = "MAPPING_VALIDATED"
    POLICY_GENERATED = "POLICY_GENERATED"
    DRY_RUN = "DRY_RUN"
    EXECUTING = "EXECUTING"
    INSPECTING = "INSPECTING"
    REVISION = "REVISION"
    QA = "QA"
    RESOLVING = "RESOLVING"
    AGGREGATING = "AGGREGATING"
    ARCHIVED = "ARCHIVED"
    HALT = "HALT"
    ABORT_CONFIRMED = "ABORT_CONFIRMED"


class StateMachine:
    def __init__(self, session_id: str):
        self.sid = session_id
        self.state = None
        self._token = None
        self._abort_pending = False
        self._pre_halt = None
        self._halt_tools: list[str] = []

    def enter(self, s: State, detail=""):
        self.state = s
        self._token = uuid.uuid4().hex
        validate_and_route(self.sid, MessageKind.CONTROL,
                           {"event": "STATE_ENTERED", "state": s.value,
                            "abort_token": self._token, "detail": {"d": detail}}, "system")

    def request_abort(self, token: str):
        if token == self._token:
            self._abort_pending = True

    def transition(self, to: State, detail="") -> bool:
        if self._abort_pending:
            self._abort_pending = False
            self.enter(State.ABORT_CONFIRMED)
            return False
        validate_and_route(self.sid, MessageKind.CONTROL,
                           {"event": "STATE_EXITED", "state": self.state.value}, "system")
        self.enter(to, detail)
        return True

    def halt(self, reason: str, tools: list[str] | None = None):
        self._pre_halt = self.state
        self._halt_tools = tools or []
        validate_and_route(self.sid, MessageKind.CONTROL,
                           {"event": "HALT",
                            "detail": {"reason": reason, "tools": self._halt_tools}}, "system")
        self.enter(State.HALT, reason)

    def resume(self):
        for t in self._halt_tools:
            reset_breaker(self.sid, t)
        validate_and_route(self.sid, MessageKind.CONTROL,
                           {"event": "RESUMED", "detail": {"tools": self._halt_tools}}, "user")
        target = self._pre_halt or State.INGESTING
        self._halt_tools = []
        self.enter(target, "resumed")

```

### recon_agent/app/engine/__init__.py

```python


```

### recon_agent/app/engine/chatbot.py

```python
import json
from typing import List, Dict, Tuple, Optional
from app.core import llm_client


def build_grounded_context(pipe) -> str:
    """
    Builds a strict context snapshot containing ONLY the currently active tables,
    schema mappings, matched records, exceptions, and financial balances.
    Deleted files and tables are automatically excluded.
    """
    if not pipe or not getattr(pipe, "tables", None):
        return "NO_ACTIVE_FILES: There are no files or datasets loaded in the current active session."

    lines = []
    lines.append("=== ACTIVE RECONCILIATION DATASET & ENGINE CONTEXT ===")
    
    # 1. Active Tables and Columns
    lines.append("\n[Active Tables Loaded in Session]:")
    for tbl_name, rows in pipe.tables.items():
        sample_rows = rows[:5]
        cols = list(rows[0].keys()) if rows else []
        lines.append(f"- Table '{tbl_name}': {len(rows)} total records. Columns: {cols}")
        lines.append(f"  Sample Data Preview (first {len(sample_rows)} rows): {json.dumps(sample_rows, default=str)}")

    # 2. Active Schema Mapping
    if getattr(pipe, "cfg", None):
        lines.append("\n[Active Schema Mapping]:")
        lines.append(json.dumps(pipe.cfg, indent=2, default=str))

    # 3. Financial Balances & Report Summary
    if getattr(pipe, "final", None):
        lines.append("\n[Final Reconciliation Summary]:")
        lines.append(f"- Match Rate: {pipe.final.match_rate:.1%}")
        lines.append(f"- Total Gross Ledger Volume: INR {pipe.final.total_gross:,.2f}")
        lines.append(f"- Net Bank Inflow: INR {pipe.final.total_net:,.2f}")
        lines.append(f"- Total Fees & Variance: INR {pipe.final.total_fees:,.2f}")
        lines.append(f"- Matched Value: INR {pipe.final.matched_value:,.2f}")
        lines.append(f"- Exception Value: INR {pipe.final.exception_value:,.2f}")
        lines.append(f"- Auto-Resolved (Approved): {pipe.final.auto_resolved_count}")
        lines.append(f"- Escalated (Review Req): {pipe.final.escalated_count}")
        lines.append(f"- Unresolved Pending: {pipe.final.unresolved_count}")

    # 4. Active Classified Exceptions Queue
    if getattr(pipe, "queue", None):
        lines.append(f"\n[Active Exception Queue ({len(pipe.queue)} items)]:")
        for idx, item in enumerate(pipe.queue, 1):
            rec = item["rec"]
            explanation = item.get("explanation") or getattr(rec, "explanation", "")
            lines.append(
                f"  #{idx}. [{rec.side}] Ref: {rec.ref} | RID: {rec.rid} | "
                f"Reason: {rec.reason.value if hasattr(rec.reason, 'value') else rec.reason} | "
                f"Status/Action: {item.get('action')} | "
                f"Delta: {rec.delta} | "
                f"Diagnostic: {explanation}"
            )

    lines.append("\n=== CRITICAL RECONCILIATION ASSISTANT RULES ===")
    lines.append("1. You are the AI Reconciliation Assistant for this financial dataset.")
    lines.append("2. Answer the user's questions strictly using the ACTIVE dataset and report provided above.")
    lines.append("3. If the user asks about a file, order, transaction, or column that was deleted, replaced, or is not in the active dataset, you MUST state clearly that the file/data is not present in the current active session.")
    lines.append("4. Never hallucinate data for deleted files or nonexistent transactions.")
    lines.append("5. Keep answers concise, factual, and formatted in clear markdown.")

    return "\n".join(lines)


class ReconChatSession:
    def __init__(self, sid: str, pipe=None):
        self.sid = sid
        self.pipe = pipe
        self.history: List[Dict[str, str]] = []

    def set_pipe(self, pipe):
        self.pipe = pipe

    def chat(self, user_message: str) -> Dict[str, any]:
        if not self.pipe or not getattr(self.pipe, "tables", None) or len(self.pipe.tables) == 0:
            return {
                "ok": False,
                "error": "No active files loaded. The conversation starts only after files are uploaded/ingested.",
                "response": "Please upload or ingest reconciliation files before starting the conversation."
            }

        context = build_grounded_context(self.pipe)
        
        # Append user message
        self.history.append({"role": "user", "content": user_message})

        try:
            reply, cost = llm_client.conversational_chat(self.history, system_instruction=context)
            self.history.append({"role": "model", "content": reply})
            return {
                "ok": True,
                "response": reply,
                "cost_usd": cost,
                "session_id": self.sid
            }
        except Exception as e:
            # Rollback last user message on failure
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
            return {
                "ok": False,
                "error": str(e),
                "response": f"Failed to generate response: {e}"
            }

```

### recon_agent/app/engine/fee.py

```python
from decimal import Decimal, ROUND_HALF_UP


def compute_fee(gross, schedule):
    g = Decimal(str(gross))
    if schedule.model_type == "flat_rate":
        fee = g * Decimal(str(schedule.params["rate"]))
    elif schedule.model_type == "per_txn_flat":
        fee = Decimal(str(schedule.params["flat"]))
    else:
        fee, rem = Decimal(0), g
        for lo, hi, rate in schedule.params["tiers"]:
            band = min(rem, Decimal(str(hi)) - Decimal(str(lo))) if hi else rem
            fee += band * Decimal(str(rate))
            rem -= band
    if schedule.gst_rate:
        fee *= (1 + Decimal(str(schedule.gst_rate)))
    return float(fee.quantize(Decimal("0.01"), ROUND_HALF_UP))

```

### recon_agent/app/engine/match.py

```python
import datetime

from pydantic import BaseModel, model_validator

from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import EvidencePiece, MessageKind
from app.core.dispatcher import dispatch_tool_call, ToolCall
from app.engine.fee import compute_fee


class SemArgs(BaseModel):
    left: dict
    right: dict

class SemResult(BaseModel):
    score: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def parse_score(cls, data):
        if isinstance(data, dict):
            if "score" in data:
                try:
                    return {"score": float(data["score"])}
                except Exception:
                    pass
            for v in data.values():
                try:
                    return {"score": float(v)}
                except Exception:
                    pass
        elif isinstance(data, (int, float)):
            return {"score": float(data)}
        return {"score": 0.0}


SEM_TOOL = ToolCall(name="semantic_similarity", args_schema=SemArgs,
                    result_schema=SemResult, timeout_s=REG["llm_tool_timeout_s"],
                    retries=2, fallback=lambda a: None, cost_budget_usd=0.005)


def _lev(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _sim(a, b):
    a, b = str(a).lower(), str(b).lower()
    return 1 - _lev(a, b) / max(len(a), len(b), 1)


def _busdays(d1, d2):
    a, b = sorted((d1, d2))
    n, cur = 0, a
    while cur < b:
        cur += datetime.timedelta(days=1)
        if cur.weekday() < 5:
            n += 1
    return n


def _d(v):
    import pandas as pd
    return pd.to_datetime(v).date()


def fee_explains(a: float, rv: float, schedule, tol: float) -> bool:
    if not schedule:
        return False
    raw = abs(a - rv)
    net = abs((a - compute_fee(a, schedule)) - rv)
    return raw > tol and net <= tol


def score_pair(sid, l, r, cfg, schedule, fallback_events):
    tol, win = cfg["tolerance"], cfg["window_days"]
    comps, w = {}, {}
    key = 1.0 if str(l[cfg["left_key"]]) == str(r[cfg["right_key"]]) \
        else _sim(l[cfg["left_key"]], r[cfg["right_key"]])
    comps["key"], w["key"] = key, REG["w_match_key"]

    signed_delta = None
    raw_matched = fee_x = None
    if cfg.get("left_amount") and cfg.get("right_amount"):
        a, rv = float(l[cfg["left_amount"]]), float(r[cfg["right_amount"]])
        raw_delta = abs(a - rv)
        raw_matched = raw_delta <= tol
        fee = compute_fee(a, schedule) if schedule else 0.0
        net_delta = abs((a - fee) - rv)
        net_matched = net_delta <= tol
        fee_x = fee_explains(a, rv, schedule, tol)
        signed_delta = a - rv
        best = min(raw_delta, net_delta)
        comps["amount"] = 1.0 if (raw_matched or net_matched) else max(
            0.0, 1 - best / max(abs(a) * REG["amount_score_scale_pct"], 1.0))
        w["amount"] = REG["w_match_amount"]
    else:
        fallback_events.append("amount_component_skipped")

    ddiff = None
    if cfg.get("left_date") and cfg.get("right_date"):
        ddiff = _busdays(_d(l[cfg["left_date"]]), _d(r[cfg["right_date"]]))
        comps["date"] = max(0.0, 1 - ddiff / win)
        w["date"] = REG["w_match_date"]

    if key == 1.0:
        comps["semantic"], w["semantic"] = 1.0, REG["w_match_semantic"]
    elif key < 0.35:
        comps["semantic"], w["semantic"] = 0.0, REG["w_match_semantic"]
    else:
        sem, fb = dispatch_tool_call(sid, SEM_TOOL, {"left": l, "right": r})
        if isinstance(sem, SemResult):
            comps["semantic"], w["semantic"] = sem.score, REG["w_match_semantic"]
        else:
            fallback_events.append(f"semantic_renormalized:{fb}")

    value = sum(comps[k] * w[k] for k in comps) / sum(w.values())
    evidence = []
    if key == 1.0:
        evidence.append(EvidencePiece.KEY_MATCH)
    if raw_matched:
        evidence.append(EvidencePiece.AMOUNT_WITHIN_TOL)
    if ddiff is not None and ddiff <= win:
        evidence.append(EvidencePiece.DATE_WITHIN_WINDOW)
    if fee_x:
        evidence.append(EvidencePiece.FEE_MODEL_MATCH)
    return value, comps, evidence, signed_delta

```

### recon_agent/app/engine/qa.py

```python
from app.core.contracts import HypothesisCategory as H
from app.core.contracts import HYPOTHESIS_PRIORITY

CTX_KEYS = ["dup_rids", "split_targets", "single_target", "partial", "fee_match",
            "tax_match", "fx_match", "fuzzy_key", "negative_credit",
            "date_only_mismatch"]

_PREDICATES = {
    H.DUPLICATE:             lambda rec, ctx: bool(ctx["dup_rids"]),
    H.SPLIT:                 lambda rec, ctx: bool(ctx["split_targets"]),
    H.PARTIAL_PAYMENT:       lambda rec, ctx: rec.delta is not None and rec.delta > 0
                                                and ctx["single_target"] and ctx["partial"],
    H.REFUND_OFFSET:         lambda rec, ctx: ctx["negative_credit"]
                                                or (rec.delta is not None and rec.delta < 0),
    H.FEE_DEDUCTION:         lambda rec, ctx: ctx["fee_match"],
    H.TAX_WITHHOLDING:       lambda rec, ctx: ctx["tax_match"],
    H.CURRENCY_CONVERSION:   lambda rec, ctx: ctx["fx_match"],
    H.TEMPORAL_DRIFT:        lambda rec, ctx: ctx["date_only_mismatch"],
    H.COUNTERPARTY_MISMATCH: lambda rec, ctx: ctx["fuzzy_key"],
    H.AMOUNT_DELTA:          lambda rec, ctx: rec.delta is not None,
    H.UNCLASSIFIED:          lambda rec, ctx: True,
}

_ORDERED = sorted(HYPOTHESIS_PRIORITY, key=HYPOTHESIS_PRIORITY.get)


def classify(rec, ctx) -> H:
    for category in _ORDERED:
        if _PREDICATES[category](rec, ctx):
            return category
    return H.UNCLASSIFIED

```

### recon_agent/app/engine/resolving.py

```python
from typing import Optional
from app.core.constants import REG
from app.core.contracts import HypothesisCategory, HYPOTHESIS_PRIORITY

_MAX_RANK = max(HYPOTHESIS_PRIORITY.values())


def category_confidence(category: HypothesisCategory) -> float:
    p = HYPOTHESIS_PRIORITY.get(category, _MAX_RANK)
    return round(1.0 - (p - 1) / (_MAX_RANK - 1), 3)


def exception_confidence(evidence_count: int, category: HypothesisCategory, sem: Optional[float] = None) -> float:
    # High confidence for verified business patterns with evidence
    if category in (HypothesisCategory.TEMPORAL_DRIFT, HypothesisCategory.SPLIT, HypothesisCategory.FEE_DEDUCTION):
        base = 0.88 + 0.04 * min(evidence_count, 2)
        return min(round(base, 3), 0.98)
    
    # Well-categorized anomalies
    if category in (HypothesisCategory.DUPLICATE, HypothesisCategory.REFUND_OFFSET):
        return round(0.85, 3)
    
    # Missing / unclassified items require human escalation
    return (min(evidence_count / 4, 1.0) * REG["w_exception_evidence"]
            + category_confidence(category) * REG["w_exception_category"]
            + (sem or 0.0) * REG["w_exception_semantic"])


def decide_action(conf: float, evidence_count: int, category: Optional[HypothesisCategory] = None) -> str:
    # Non-error business variations that should be automatically approved
    if category in (HypothesisCategory.TEMPORAL_DRIFT, HypothesisCategory.SPLIT, HypothesisCategory.FEE_DEDUCTION):
        return "auto_resolve"

    # Strict errors / anomalies that require human escalation
    if category in (HypothesisCategory.DUPLICATE, HypothesisCategory.REFUND_OFFSET, HypothesisCategory.UNCLASSIFIED, HypothesisCategory.COUNTERPARTY_MISMATCH):
        return "request_confirmation"

    if (conf >= REG["exception_auto_resolve_confidence"]
            and evidence_count >= REG["exception_auto_resolve_evidence_min"]):
        return "auto_resolve"
    if 0.40 <= conf < 0.85:
        return "request_confirmation"
    return "mark_pending"


def generate_explanation(rec, ctx: dict, row_data: Optional[dict] = None) -> str:
    cat = rec.reason
    side = rec.side
    ref = rec.ref or "N/A"

    if cat == HypothesisCategory.TEMPORAL_DRIFT:
        return f"Approved [No Error]: Exact amount & reference '{ref}' matched; settlement deferred by bank holiday/clearing window."
    elif cat == HypothesisCategory.SPLIT:
        targets = ctx.get("split_targets", [])
        return f"Approved [No Error]: Batch settlement combines multiple order legs (RIDs {targets}) net of payment gateway fees."
    elif cat == HypothesisCategory.FEE_DEDUCTION:
        return f"Approved [No Error]: Net bank deposit variance matches standard payment gateway fee schedule."
    elif cat == HypothesisCategory.DUPLICATE:
        return f"Error in Source A (Ledger): Duplicate order reference '{ref}' recorded multiple times in payments ledger."
    elif cat == HypothesisCategory.REFUND_OFFSET:
        return f"Anomaly in Source B (Bank): Negative credit entry (-₹{abs(rec.delta or 0):.2f}) representing customer refund or chargeback."
    elif cat == HypothesisCategory.COUNTERPARTY_MISMATCH:
        return f"Error: Counterparty identifier mismatch between payment order reference '{ref}' and bank settlement UTR."
    elif side == "L":
        return f"Error in Source B (Bank): Order '{ref}' exists in payments ledger but has no corresponding bank settlement credit."
    elif side == "R":
        return f"Error in Source A (Ledger): Unmatched bank credit for UTR '{ref}' without corresponding order in payments ledger."
    else:
        return f"Unclassified discrepancy for reference '{ref}'."

```

### recon_agent/app/engine/report.py

```python
from app.core.constants import REG
from app.core.contracts import FinalReport
from app.core.cost import tracker_for


def build_final_report(sid, *, match_rate, precision_vs_truth, recall_vs_truth,
                       throughput_rows_per_sec, exceptions, elapsed_seconds,
                       totals, llm_user_disagreements, fallback_events) -> FinalReport:
    tracker = tracker_for(sid)
    return FinalReport(
        match_rate=match_rate,
        precision_vs_truth=precision_vs_truth,
        recall_vs_truth=recall_vs_truth,
        throughput_rows_per_sec=throughput_rows_per_sec,
        honest_exception_count=len(exceptions),
        auto_resolved_count=sum(1 for e in exceptions if e.get("action") in ("auto_resolve", "mark_resolved")),
        escalated_count=sum(1 for e in exceptions if e.get("action") in ("request_confirmation", "escalate")),
        unresolved_count=sum(1 for e in exceptions if e.get("action") == "mark_pending"),
        total_gross=totals["gross"], total_net=totals["net"], total_fees=totals["fees"],
        matched_value=totals["matched_value"], exception_value=totals["exception_value"],
        cost_usd=round(tracker.total, 6),
        cost_estimated=tracker.estimated_any,
        elapsed_seconds=elapsed_seconds,
        llm_user_disagreements=llm_user_disagreements,
        fallback_events=fallback_events,
        constants_version=REG.version,
        retention_note="intermediates 90d; final report + audit retained indefinitely",
    )

```

### recon_agent/app/server/__init__.py

```python


```

### recon_agent/app/server/api_v2.py

```python
# =============================================================================
# app/server/api_v2.py
#
# API v2 backend — docks the web console to the recon_agent pipeline.
# Drop-in, self-contained, no changes to existing code.
#
# INTEGRATION:
#   from app.server.api_v2 import mount_v2
#   mount_v2(app)          # after `app = FastAPI(...)`
#
#   Console:   http://127.0.0.1:8000/console
#   API:       http://127.0.0.1:8000/api/v2/...   (OpenAPI at /docs)
#   WebSocket: ws://127.0.0.1:8000/ws/v2/{sid}
# =============================================================================

import asyncio
import json
import re
import threading
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, FastAPI, File, HTTPException, Query, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import BASE_DIR, UPLOAD_DIR
from app.core.audit import audit_for
from app.core.channels import subscribe
from app.core.constants import REG
from app.core.contracts import MessageKind
from app.core.cost import tracker_for
from app.core.dispatcher import _breakers
from app.core.masking import pii_score
from app.engine.chatbot import ReconChatSession
from app.pipeline import Pipeline

STATIC_DIR = BASE_DIR / "app" / "static"

# -----------------------------------------------------------------------------
# Per-session registries + priority-tagged event ring buffers
# -----------------------------------------------------------------------------
V2_SESSIONS: dict[str, dict] = {}
CHAT_SESSIONS: dict[str, ReconChatSession] = {}
BUFFERS: dict[str, dict] = {}          # sid -> {"trace": deque, "logs": deque}
_WS: dict[str, dict] = {}              # sid -> {"queues": set, "loop": loop|None}

_P3_PATTERN = re.compile(r"^(tool_ok|cost_overrun|args_rejected|AUDIT_COMMIT)")
_P1_CONTROL = {"STATE_ENTERED", "STATE_EXITED", "HALT", "RESUMED",
               "ABORT_CONFIRMED", "FILE_REQUESTED", "CONFIRMATION_REQUESTED"}


def _buffers(sid: str) -> dict:
    if sid not in BUFFERS:
        BUFFERS[sid] = {"trace": deque(maxlen=2000), "logs": deque(maxlen=5000)}
    return BUFFERS[sid]


def _classify(kind: MessageKind, payload: dict) -> int:
    """Priority tiers: 1=chat/narration, 2=trace, 3=silent logs."""
    if kind in (MessageKind.CHAT, MessageKind.ARTIFACT):
        return 1
    if kind == MessageKind.CONTROL:
        return 1 if payload.get("event") in _P1_CONTROL else 2
    return 3 if _P3_PATTERN.match(payload.get("event", "")) else 2


def _push_ws(sid: str, frame: str):
    s = _WS.get(sid)
    if not s or not s["loop"]:
        return
    for q in list(s["queues"]):
        try:
            s["loop"].call_soon_threadsafe(q.put_nowait, frame)
        except Exception:
            pass


def _bus_bridge(kind: MessageKind):
    def handler(sid: str, model, source: str):
        payload = model.model_dump()
        prio = _classify(kind, payload)
        frame = {"kind": kind.value, "priority": prio, "source": source,
                 "payload": payload, "ts": datetime.now(timezone.utc).isoformat()}
        buf = _buffers(sid)
        (buf["logs"] if prio == 3 else buf["trace"]).append(frame)
        _push_ws(sid, json.dumps(frame, default=str))
    return handler


_bridge_installed = False


def _install_bus_bridge():
    global _bridge_installed
    if _bridge_installed:
        return
    for k in MessageKind:
        subscribe(k, _bus_bridge(k))
    _bridge_installed = True


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _sess(sid: str) -> dict:
    if sid not in V2_SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    return V2_SESSIONS[sid]


def _pipe(sid: str):
    return _sess(sid).get("pipe")


def _totals(pipe) -> dict | None:
    """Port of Pipeline.aggregate() balance math, safe before AGGREGATING."""
    if not pipe or not getattr(pipe, "cfg", None) or not pipe.cfg:
        return None
    cfg = pipe.cfg
    rows_l = pipe.tables.get(cfg.get("left_table", ""), [])
    rows_r = pipe.tables.get(cfg.get("right_table", ""), [])
    la, ra = cfg.get("left_amount"), cfg.get("right_amount")
    if not la or not ra:
        return None
    g = sum(float(x.get(la, 0) or 0) for x in rows_l)
    n = sum(float(x.get(ra, 0) or 0) for x in rows_r)
    matched_rids = {m.l_rid for m in pipe.exec_res.matched} if getattr(pipe, "exec_res", None) else set()
    mv = sum(float(x.get(la, 0) or 0) for x in rows_l if x["_rid"] in matched_rids)
    return {"gross": round(g, 2), "net": round(n, 2), "fees": round(g - n, 2),
            "matched_value": round(mv, 2), "exception_value": round(g - mv, 2)}


def _exception_rows(pipe) -> list[dict]:
    rows = []
    for item in getattr(pipe, "queue", None) or []:
        rec = item["rec"]
        rows.append({
            "rid": rec.rid, "side": rec.side, "ref": rec.ref,
            "reason": rec.reason.value if hasattr(rec.reason, "value") else str(rec.reason),
            "delta": rec.delta, "confidence": round(item.get("conf", 0.0), 3),
            "action": item.get("action", "mark_pending"),
            "explanation": item.get("explanation") or getattr(rec, "explanation", None),
            "pieces": [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])],
        })
    return rows


def _paginate(items: list, page: int, page_size: int) -> dict:
    """Paginate a list and return metadata."""
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


# -----------------------------------------------------------------------------
# API v2 router — one endpoint per console panel
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.post("/sessions")
def create_session():
    sid = uuid.uuid4().hex[:8]
    V2_SESSIONS[sid] = {"pipe": None, "files": {}}
    CHAT_SESSIONS[sid] = ReconChatSession(sid)
    _buffers(sid)
    audit_for(sid).append({"event": "SESSION_INITIALIZED", "session_id": sid})
    return {"session_id": sid}


@router.get("/sessions/{sid}/overview")
def overview(sid: str):
    _sess(sid)
    pipe = _pipe(sid)
    brk = {t: c for (s, t), c in _breakers.items() if s == sid}
    files_map = V2_SESSIONS[sid].get("files", {})
    return {
        "session_id": sid,
        "state": pipe.sm.state.value if pipe and pipe.sm.state else "IDLE",
        "abort_token": pipe.sm._token if pipe else None,
        "halted": bool(pipe and pipe.sm.state and pipe.sm.state.value == "HALT"),
        "circuit_breaker": {
            "threshold": REG["circuit_breaker_failure_count"],
            "tools": brk,
            "open": any(c >= REG["circuit_breaker_failure_count"] for c in brk.values()),
        },
        "cost_usd": round(tracker_for(sid).total, 6),
        "constants_version": REG.version,
        "audit_count": len(audit_for(sid).records),
        "files": list(files_map.keys()),
        "table_counts": {k: len(v) for k, v in (pipe.tables if pipe and getattr(pipe, "tables", None) else {}).items()},
    }


@router.get("/sessions/{sid}/ingestion")
def ingestion(sid: str,
              table: Optional[str] = None,
              page: int = Query(1, ge=1),
              page_size: int = Query(100, ge=1, le=1000)):
    """Return ingested tables with pagination for large datasets."""
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "tables", None):
        return {"tables": {}, "profiles": {}, "table_meta": {}}

    profiles = {}
    mask_at, review_at = REG["pii_mask_threshold"], REG["pii_review_threshold"]
    for name, profs in getattr(pipe, "profiles", {}).items():
        out = []
        for p in profs:
            d = p.model_dump()
            if d["pii_likelihood"] >= mask_at:
                d["sample_values"] = ["[MASKED:pii]"]
            elif d["pii_likelihood"] >= review_at:
                d["pii_review"] = True
            out.append(d)
        profiles[name] = out

    # Build table metadata (always return counts for all tables)
    table_meta = {}
    for name, rows in pipe.tables.items():
        cols = [k for k in (rows[0].keys() if rows else []) if not k.startswith("_")]
        table_meta[name] = {"total_rows": len(rows), "columns": cols}

    # If a specific table is requested, paginate its rows
    tables = {}
    if table and table in pipe.tables:
        pg = _paginate(pipe.tables[table], page, page_size)
        tables[table] = pg
    elif table:
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found")
    else:
        # Return all tables but paginated (first page only for each)
        for name, rows in pipe.tables.items():
            pg = _paginate(rows, page, page_size)
            tables[name] = pg

    return {
        "session_id": sid,
        "tables": tables,
        "profiles": profiles,
        "table_meta": table_meta,
    }


@router.get("/sessions/{sid}/mapping")
def mapping(sid: str):
    pipe = _pipe(sid)
    if not pipe:
        return {"candidates": [], "committed": None, "confidence": 0.0}
    cands = []
    w = (REG["w_mapping_structural"], REG["w_mapping_sample"],
         REG["w_mapping_type"], REG["w_mapping_semantic"])
    for ov, lt, lc, rt, rc in getattr(pipe, "_map_cands", [])[:6]:
        lp = next((p for p in pipe.profiles.get(lt, []) if p.name == lc), None)
        rp = next((p for p in pipe.profiles.get(rt, []) if p.name == rc), None)
        tc = 1.0 if (lp and rp and lp.dtype == rp.dtype) else 0.4
        sem = 0.5
        composite = w[0] * ov + w[1] * ov + w[2] * tc + w[3] * sem
        cands.append({
            "left": f"{lt}.{lc}", "right": f"{rt}.{rc}",
            "signals": {"structural_overlap": round(ov, 3), "sample_match_rate": round(ov, 3),
                        "type_compatibility": tc, "semantic_plausibility": sem},
            "composite": round(composite, 3),
            "band": "auto" if composite >= REG["mapping_auto_accept"] else
                    ("confirm" if composite >= REG["mapping_review_floor"] else "escalate"),
        })
    return {
        "candidates": cands,
        "committed": {k: pipe.cfg.get(k) for k in
                      ("left_table", "right_table", "left_key", "right_key",
                       "left_amount", "right_amount", "left_date", "right_date",
                       "tolerance", "window_days")} if pipe.cfg else None,
        "confidence": round(getattr(pipe, "_map_conf", 0.0), 3),
        "ambiguous": getattr(pipe, "_ambiguous", False),
        "ambiguity_delta": REG["mapping_ambiguity_delta"],
    }


@router.get("/sessions/{sid}/policy")
def policy(sid: str):
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "policy_doc", None):
        return {"components": [], "baseline_match_rate": None, "revision_history": []}
    doc = pipe.policy_doc
    return {
        "components": [c.model_dump() for c in doc.components],
        "generated_from": doc.generated_from,
        "baseline_match_rate": doc.baseline_match_rate,
        "baseline_source": doc.baseline_source,
        "baseline_constants_version": doc.baseline_constants_version,
        "revision_history": doc.revision_history,
        "current_match_rate": getattr(pipe, "match_rate", None),
        "revision_caps": {"iterations": REG["revision_iteration_cap"],
                          "seconds": REG["revision_time_cap_s"],
                          "usd": REG["revision_cost_cap_usd"]},
        "fee_schedules": [fs.model_dump(mode="json") for fs in REG.fee_schedules.values()],
    }


@router.get("/sessions/{sid}/results")
def results(sid: str):
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "exec_res", None):
        return {"executed": False}
    r = pipe.exec_res
    return {
        "executed": True,
        "match_rate": getattr(pipe, "match_rate", None),
        "precision_vs_truth": getattr(pipe, "precision", None),
        "recall_vs_truth": getattr(pipe, "recall", None),
        "throughput_rows_per_sec": getattr(pipe, "throughput", None),
        "matched": [m.model_dump() for m in r.matched],
        "unmatched_count": len(r.unmatched),
        "duplicates": r.duplicates,
        "splits": r.splits,
        "variance": r.variance.model_dump(),
        "totals": _totals(pipe),
        "final_report": pipe.final.model_dump(mode="json") if getattr(pipe, "final", None) else None,
    }


@router.get("/sessions/{sid}/exceptions")
def exceptions(sid: str,
               page: int = Query(1, ge=1),
               page_size: int = Query(50, ge=1, le=500)):
    """Paginated exception queue for large reconciliation runs."""
    pipe = _pipe(sid)
    if not pipe:
        return {"queue": [], "pagination": None}
    all_rows = _exception_rows(pipe)
    pg = _paginate(all_rows, page, page_size)
    return {
        "queue": pg["items"],
        "pagination": {k: v for k, v in pg.items() if k != "items"},
        "auto_resolve_gate": {"confidence": REG["exception_auto_resolve_confidence"],
                              "evidence_min": REG["exception_auto_resolve_evidence_min"]},
        "summary": {
            "total": len(all_rows),
            "auto_resolved": sum(1 for r in all_rows if r["action"] in ("auto_resolve", "mark_resolved")),
            "needs_review": sum(1 for r in all_rows if r["action"] in ("request_confirmation", "escalate")),
            "pending": sum(1 for r in all_rows if r["action"] == "mark_pending"),
        },
    }


class ActionBody(BaseModel):
    action: str          # "approve" | "escalate"
    note: str = ""


@router.post("/sessions/{sid}/exceptions/{rid}/action")
def exception_action(sid: str, rid: int, body: ActionBody):
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "queue", None):
        raise HTTPException(status_code=404, detail="no exception queue")
    item = next((i for i in pipe.queue if i["rec"].rid == rid), None)
    if not item:
        raise HTTPException(status_code=404, detail="exception not found")

    prior_action = item.get("action", "mark_pending")
    prior = {"action": prior_action, "confidence": item.get("conf", 0.0),
             "reason": item["rec"].reason.value if hasattr(item["rec"].reason, "value") else str(item["rec"].reason),
             "pieces": [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])]}
    item["action"] = "mark_resolved" if body.action == "approve" else "escalate"

    audit_for(sid).append({"event": "USER_OVERRIDE", "rid": rid,
                           "action": item["action"], "note": body.note, "prior": prior})

    counts = None
    if getattr(pipe, "final", None) is not None:
        pipe.final.auto_resolved_count = sum(
            1 for e in pipe.queue if e.get("action") in ("auto_resolve", "mark_resolved"))
        pipe.final.escalated_count = sum(
            1 for e in pipe.queue if e.get("action") in ("request_confirmation", "escalate"))
        pipe.final.unresolved_count = sum(
            1 for e in pipe.queue if e.get("action") == "mark_pending")
        if prior_action != item["action"]:
            pipe.final.llm_user_disagreements.append({
                "rid": rid, "system_proposal": prior,
                "user_decision": {"action": item["action"], "note": body.note},
                "disagreement_kind": "exception_override"})
        counts = {"auto_resolved": pipe.final.auto_resolved_count,
                  "escalated": pipe.final.escalated_count,
                  "unresolved": pipe.final.unresolved_count,
                  "honest_total": pipe.final.honest_exception_count}
    return {"ok": True, "rid": rid, "action": item["action"], "counts": counts}


@router.get("/sessions/{sid}/audit")
def audit(sid: str):
    log = audit_for(sid)
    return {"records": log.records, "verified": log.verify(), "count": len(log.records)}


@router.get("/sessions/{sid}/trace")
def trace(sid: str):
    _sess(sid)
    return {"events": list(_buffers(sid)["trace"])}


@router.get("/sessions/{sid}/logs")
def logs(sid: str):
    _sess(sid)
    return {"events": list(_buffers(sid)["logs"])}


# ------------------------------- mutations ----------------------------------
@router.post("/sessions/{sid}/run")
async def run(sid: str, files: list[UploadFile] = File(...)):
    sess = _sess(sid)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for f in files:
        p = UPLOAD_DIR / f"{sid}_{f.filename}"
        p.write_bytes(await f.read())
        sess["files"][f.filename] = p
        paths.append(p)
    if len(paths) < 2:
        raise HTTPException(status_code=400, detail="need at least two tables (ledger + statement)")

    pipe = Pipeline(sid, auto_ack=True)
    sess["pipe"] = pipe
    if sid in CHAT_SESSIONS:
        CHAT_SESSIONS[sid].set_pipe(pipe)
    audit_for(sid).append({"event": "RUN_STARTED",
                           "files": [p.name for p in paths],
                           "ts": datetime.now(timezone.utc).isoformat()})

    def work():
        try:
            pipe.run(paths)
        except Exception as e:
            import traceback
            traceback.print_exc()

    threading.Thread(target=work, daemon=True).start()
    return {"ok": True, "files": [p.name for p in paths]}


@router.post("/sessions/{sid}/resume")
def resume(sid: str):
    pipe = _pipe(sid)
    if not pipe:
        raise HTTPException(status_code=400, detail="no pipeline to resume")
    pipe.sm.resume()

    def cont():
        pipe.continue_run()

    threading.Thread(target=cont, daemon=True).start()
    return {"ok": True, "state": pipe.sm.state.value}


class AbortBody(BaseModel):
    token: str


@router.post("/sessions/{sid}/abort")
def abort(sid: str, body: AbortBody):
    pipe = _pipe(sid)
    if not pipe:
        raise HTTPException(status_code=400, detail="no pipeline to abort")
    pipe.sm.request_abort(body.token)
    return {"ok": True}


class ChatBody(BaseModel):
    message: str


@router.post("/sessions/{sid}/chat")
def chat(sid: str, body: ChatBody):
    _sess(sid)
    if sid not in CHAT_SESSIONS:
        CHAT_SESSIONS[sid] = ReconChatSession(sid, _pipe(sid))
    else:
        CHAT_SESSIONS[sid].set_pipe(_pipe(sid))
    return CHAT_SESSIONS[sid].chat(body.message)


# ------------------------------- websocket ----------------------------------
async def ws_v2(websocket: WebSocket, sid: str):
    await websocket.accept()
    s = _WS.setdefault(sid, {"queues": set(), "loop": None})
    q: asyncio.Queue = asyncio.Queue()
    s["queues"].add(q)
    s["loop"] = asyncio.get_running_loop()
    try:
        await websocket.send_text(json.dumps(
            {"kind": "control", "priority": 1, "source": "system",
             "payload": {"event": "WS_CONNECTED", "session": sid},
             "ts": datetime.now(timezone.utc).isoformat()}))
        while True:
            await websocket.send_text(await q.get())
    except Exception:
        pass
    finally:
        s["queues"].discard(q)


# -----------------------------------------------------------------------------
# Mount
# -----------------------------------------------------------------------------
def mount_v2(app: FastAPI):
    _install_bus_bridge()
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    # CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    # WebSocket route on root app
    app.add_api_websocket_route("/ws/v2/{sid}", ws_v2)

    @app.get("/console", include_in_schema=False)
    def console():
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        return HTMLResponse(
            "<code>app/static/index.html not found — save the console build there, "
            "then reload /console</code>", status_code=404)

    # Serve all static files
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


# -----------------------------------------------------------------------------
# Standalone entry: python -m app.server.api_v2
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    app = FastAPI(title="Recon Agent API v2")
    mount_v2(app)
    uvicorn.run(app, host="127.0.0.1", port=8000)

```

### recon_agent/app/server/main.py

```python
import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import threading
import uuid

from fastapi import FastAPI, File, UploadFile, WebSocket, HTTPException
from pydantic import BaseModel

from app.config import UPLOAD_DIR, LOGS_DIR
from app.core.audit import audit_for
from app.core.channels import subscribe, validate_and_route
from app.core.contracts import MessageKind
from app.core.constants import REG
from app.engine.chatbot import ReconChatSession
from app.pipeline import Pipeline

# Set up file logger for server
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SERVER_LOG_PATH = LOGS_DIR / "server.log"
LATEST_SESSION_LOG = LOGS_DIR / "session.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(SERVER_LOG_PATH, mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger("recon_agent")

app = FastAPI(title="Recon Agent")

# Mount v2 API (console + new endpoints) — drop-in, no changes to v1
from app.server.api_v2 import mount_v2
mount_v2(app)

SESSIONS: dict[str, dict] = {}
CHAT_SESSIONS: dict[str, ReconChatSession] = {}


from app import config

def _write_session_log(sid: str, log_line: str):
    try:
        logs_dir = getattr(config, "LOGS_DIR", LOGS_DIR)
        logs_dir.mkdir(parents=True, exist_ok=True)
        session_file = logs_dir / f"{sid}.log"
        with open(session_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
        latest_session_log = logs_dir / "session.log"
        with open(latest_session_log, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception as e:
        logger.error(f"Failed to write session log: {e}")


def _bridge(kind):
    def fn(sid, model, source):
        ts = datetime.now(timezone.utc).isoformat()
        log_entry = json.dumps({"ts": ts, "sid": sid, "kind": kind.value, "source": source, "payload": model.model_dump()}, default=str)
        _write_session_log(sid, log_entry)
        logger.info(f"[{sid}] [{source}] {kind.value}: {json.dumps(model.model_dump(), default=str)[:140]}")

        s = SESSIONS.get(sid)
        if not s or not s["loop"]:
            return
        item = json.dumps({"kind": kind.value, "source": source,
                           "payload": model.model_dump()}, default=str)
        for aq in list(s["queues"]):
            s["loop"].call_soon_threadsafe(aq.put_nowait, item)
    return fn


for _k in MessageKind:
    subscribe(_k, _bridge(_k))


@app.post("/api/sessions")
def new_session():
    sid = uuid.uuid4().hex[:8]
    SESSIONS[sid] = {"pipe": None, "queues": set(), "loop": None, "files": {}}
    CHAT_SESSIONS[sid] = ReconChatSession(sid)

    # Ensure fresh, empty session log for the new session
    logs_dir = getattr(config, "LOGS_DIR", LOGS_DIR)
    logs_dir.mkdir(parents=True, exist_ok=True)
    session_file = logs_dir / f"{sid}.log"
    latest_session_log = logs_dir / "session.log"
    session_file.write_text("", encoding="utf-8")
    latest_session_log.write_text("", encoding="utf-8")

    init_msg = json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "event": "SESSION_INITIALIZED", "session_id": sid})
    _write_session_log(sid, init_msg)
    logger.info(f"Initialized new session {sid} (cleared active session.log)")

    return {"session_id": sid}


@app.get("/api/sessions/{sid}/files")
def list_files(sid: str):
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    pipe = SESSIONS[sid].get("pipe")
    files_map = SESSIONS[sid].get("files", {})
    tables = list(pipe.tables.keys()) if pipe and getattr(pipe, "tables", None) else []
    return {
        "session_id": sid,
        "files": [{"filename": fname, "path": str(fpath), "size": fpath.stat().st_size if fpath.exists() else 0}
                  for fname, fpath in files_map.items()],
        "active_tables": tables
    }


@app.post("/api/sessions/{sid}/files")
async def add_files(sid: str, files: list[UploadFile] = File(...)):
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    files_map = SESSIONS[sid].setdefault("files", {})
    added = []
    for f in files:
        p = UPLOAD_DIR / f"{sid}_{f.filename}"
        p.write_bytes(await f.read())
        files_map[f.filename] = p
        added.append(f.filename)

    audit_for(sid).append({
        "event": "FILES_ADDED",
        "filenames": added,
        "ts": datetime.now(timezone.utc).isoformat()
    })
    logger.info(f"[{sid}] Added files: {added}")
    return {"ok": True, "added": added, "total_files": list(files_map.keys())}


@app.delete("/api/sessions/{sid}/files/{filename}")
def delete_file(sid: str, filename: str):
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    files_map = SESSIONS[sid].get("files", {})
    target_path = files_map.pop(filename, None)
    if target_path and target_path.exists():
        try:
            os.remove(target_path)
        except Exception as e:
            logger.warning(f"Could not remove file on disk {target_path}: {e}")

    pipe = SESSIONS[sid].get("pipe")
    # Clean up corresponding table from pipeline tables if exists
    stem = Path(filename).stem
    if pipe and getattr(pipe, "tables", None) and stem in pipe.tables:
        del pipe.tables[stem]

    # Reset chat session context so no old deleted data leaks into chat
    if sid in CHAT_SESSIONS:
        CHAT_SESSIONS[sid].history = []
        CHAT_SESSIONS[sid].set_pipe(pipe)

    audit_for(sid).append({
        "event": "FILE_DELETED",
        "deleted_filename": filename,
        "remaining_files": list(files_map.keys()),
        "ts": datetime.now(timezone.utc).isoformat()
    })
    logger.info(f"[{sid}] Deleted file {filename}. Remaining: {list(files_map.keys())}")
    return {"ok": True, "deleted": filename, "remaining_files": list(files_map.keys())}


@app.post("/api/sessions/{sid}/run")
async def run(sid: str, files: list[UploadFile] = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    files_map = SESSIONS[sid].setdefault("files", {})
    for f in files:
        p = UPLOAD_DIR / f"{sid}_{f.filename}"
        p.write_bytes(await f.read())
        paths.append(p)
        files_map[f.filename] = p

    pipe = Pipeline(sid, auto_ack=False)
    SESSIONS[sid]["pipe"] = pipe
    if sid in CHAT_SESSIONS:
        CHAT_SESSIONS[sid].set_pipe(pipe)

    def work():
        pipe.run(paths)
        if getattr(pipe, "queue", None) is not None:
            validate_and_route(sid, MessageKind.ARTIFACT, {
                "kind": "exceptions",
                "rows": [{"rid": i["rec"].rid, "side": i["rec"].side, "ref": i["rec"].ref,
                          "reason": i["rec"].reason.value, "delta": i["rec"].delta,
                          "confidence": round(i["conf"], 3), "action": i["action"],
                          "pieces": [p.value if hasattr(p, "value") else p for p in i["pieces"]]}
                         for i in pipe.queue],
                "summary": {"count": len(pipe.queue)},
                "confidence_threshold": REG["exception_auto_resolve_confidence"],
                "fallback_events": pipe.fb}, "server")

    threading.Thread(target=work, daemon=True).start()
    return {"ok": True}


class ChatRequest(BaseModel):
    message: str


@app.post("/api/sessions/{sid}/chat")
def chat_endpoint(sid: str, body: ChatRequest):
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    pipe = SESSIONS[sid].get("pipe")
    if sid not in CHAT_SESSIONS:
        CHAT_SESSIONS[sid] = ReconChatSession(sid, pipe)
    else:
        CHAT_SESSIONS[sid].set_pipe(pipe)

    return CHAT_SESSIONS[sid].chat(body.message)


@app.websocket("/ws/{sid}")
async def ws(websocket: WebSocket, sid: str):
    await websocket.accept()
    s = SESSIONS.setdefault(sid, {"pipe": None, "queues": set(), "loop": None, "files": {}})
    aq: asyncio.Queue = asyncio.Queue()
    s["queues"].add(aq)
    s["loop"] = asyncio.get_running_loop()
    try:
        while True:
            await websocket.send_text(await aq.get())
    except Exception:
        s["queues"].discard(aq)


@app.get("/api/sessions/{sid}/audit")
def audit(sid: str):
    log = audit_for(sid)
    return {"records": log.records, "verified": log.verify()}


@app.get("/api/sessions/{sid}/report")
def report(sid: str):
    pipe = SESSIONS.get(sid, {}).get("pipe")
    return {"report": pipe.final.model_dump() if pipe and getattr(pipe, "final", None) else None}


@app.get("/api/sessions/{sid}/input_data")
@app.get("/api/sessions/{sid}/data")
def get_input_data(sid: str):
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    pipe = SESSIONS[sid].get("pipe")
    if not pipe or not getattr(pipe, "tables", None):
        return {"session_id": sid, "tables": {}, "profiles": {}}
    profiles = {k: [p.model_dump() for p in v] for k, v in getattr(pipe, "profiles", {}).items()}
    return {
        "session_id": sid,
        "tables": pipe.tables,
        "profiles": profiles
    }


@app.post("/api/sessions/{sid}/exceptions/{rid}/action")
def override(sid: str, rid: int, body: dict):
    pipe = SESSIONS[sid]["pipe"]
    item = next((i for i in pipe.queue if i["rec"].rid == rid), None)
    if not item:
        return {"ok": False}
    prior_action = item.get("action", "mark_pending")
    prior_conf = item.get("conf", 0.0)
    prior_reason = item["rec"].reason.value if hasattr(item["rec"].reason, "value") else str(item["rec"].reason)

    new_action = "mark_resolved" if body["action"] == "approve" else "escalate"
    item["action"] = new_action

    prior_decision = {
        "action": prior_action,
        "confidence": prior_conf,
        "reason": prior_reason,
        "pieces": [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])]
    }
    audit_for(sid).append({"event": "USER_OVERRIDE", "rid": rid,
                           "action": item["action"], "note": body.get("note", ""),
                           "prior": prior_decision})

    if getattr(pipe, "final", None) is not None:
        pipe.final.auto_resolved_count = sum(1 for e in pipe.queue if e.get("action") in ("auto_resolve", "mark_resolved"))
        pipe.final.escalated_count = sum(1 for e in pipe.queue if e.get("action") in ("request_confirmation", "escalate"))
        pipe.final.unresolved_count = sum(1 for e in pipe.queue if e.get("action") == "mark_pending")
        if prior_action != new_action:
            pipe.final.llm_user_disagreements.append({
                "rid": rid,
                "system_proposal": prior_decision,
                "user_decision": {"action": new_action, "note": body.get("note", "")},
                "disagreement_kind": "exception_override"
            })
        validate_and_route(sid, MessageKind.ARTIFACT, {
            "kind": "report",
            "summary": pipe.final.model_dump(),
            "confidence_threshold": REG["match_auto_threshold"],
            "fallback_events": pipe.fb
        }, "engine")

    return {"ok": True}


@app.post("/api/sessions/{sid}/resume")
def resume(sid: str):
    pipe = SESSIONS[sid]["pipe"]
    pipe.sm.resume()
    def cont():
        pipe.continue_run()
        if getattr(pipe, "queue", None) is not None:
            validate_and_route(sid, MessageKind.ARTIFACT, {
                "kind": "exceptions",
                "rows": [{"rid": i["rec"].rid, "side": i["rec"].side, "ref": i["rec"].ref,
                          "reason": i["rec"].reason.value, "delta": i["rec"].delta,
                          "confidence": round(i["conf"], 3), "action": i["action"],
                          "pieces": [p.value if hasattr(p, "value") else p for p in i["pieces"]]}
                         for i in pipe.queue],
                "summary": {"count": len(pipe.queue)},
                "confidence_threshold": REG["exception_auto_resolve_confidence"],
                "fallback_events": pipe.fb}, "server")
    threading.Thread(target=cont, daemon=True).start()
    return {"ok": True}


@app.post("/api/sessions/{sid}/abort")
def abort(sid: str, body: dict):
    SESSIONS[sid]["pipe"].sm.request_abort(body["token"])
    return {"ok": True}

```

### recon_agent/app/static/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Recon Agent · Console</title>
<meta name="description" content="Razorpay Autonomous Financial Reconciliation Agent — Dockable Console">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0b0f19;--surface:#111827;--card:rgba(255,255,255,0.04);
  --border:rgba(255,255,255,0.08);--border2:rgba(255,255,255,0.14);
  --text:#f1f5f9;--muted:#64748b;--dim:#475569;
  --accent:#3b82f6;--accent2:#06b6d4;--accent-g:linear-gradient(135deg,#3b82f6,#06b6d4);
  --green:#10b981;--amber:#f59e0b;--red:#ef4444;--purple:#a855f7;
  --radius:10px;--radius-sm:6px;
  --font:'Inter',system-ui,sans-serif;--mono:'JetBrains Mono',monospace;
  --glass:rgba(17,24,39,0.7);--blur:blur(16px);
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden}
body{font-family:var(--font);font-size:13px;color:var(--text);background:var(--bg);display:flex;flex-direction:column}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.12);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,0.2)}
button{font-family:var(--font);cursor:pointer;border:none;outline:none;font-size:12px;font-weight:500}
input,textarea,select{font-family:var(--font);font-size:12px;color:var(--text);background:var(--surface);border:1px solid var(--border2);border-radius:var(--radius-sm);padding:8px 12px;outline:none;transition:border .2s}
input:focus,textarea:focus{border-color:var(--accent)}
table{width:100%;border-collapse:collapse}
th{font-size:11px;font-weight:600;color:var(--muted);text-align:left;padding:8px 10px;border-bottom:1px solid var(--border2);text-transform:uppercase;letter-spacing:.04em}
td{padding:8px 10px;border-bottom:1px solid var(--border);font-size:12px}
tr:hover td{background:rgba(255,255,255,0.02)}

/* ---- Buttons ---- */
.btn{padding:7px 16px;border-radius:var(--radius-sm);font-weight:600;transition:all .2s;display:inline-flex;align-items:center;gap:6px}
.btn-primary{background:var(--accent-g);color:#fff;box-shadow:0 2px 12px rgba(59,130,246,0.3)}
.btn-primary:hover{box-shadow:0 4px 20px rgba(59,130,246,0.45);transform:translateY(-1px)}
.btn-ghost{background:transparent;color:var(--text);border:1px solid var(--border2)}
.btn-ghost:hover{border-color:var(--accent);color:var(--accent)}
.btn-sm{padding:4px 10px;font-size:11px}
.btn-danger{background:var(--red);color:#fff}
.btn:disabled{opacity:.35;cursor:default;transform:none!important;box-shadow:none!important}

/* ---- Badges ---- */
.badge{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:99px;font-size:10px;font-weight:600;white-space:nowrap}
.badge-auto{background:rgba(16,185,129,0.15);color:var(--green)}
.badge-review{background:rgba(245,158,11,0.15);color:var(--amber)}
.badge-pending{background:rgba(100,116,139,0.15);color:var(--muted)}
.badge-error{background:rgba(239,68,68,0.15);color:var(--red)}
.badge-info{background:rgba(59,130,246,0.15);color:var(--accent)}

/* ---- Top Bar ---- */
#topbar{flex:none;height:54px;background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;padding:0 16px;z-index:50}
#brand{font-size:16px;font-weight:800;background:var(--accent-g);-webkit-background-clip:text;-webkit-text-fill-color:transparent;white-space:nowrap}
#brand small{font-size:10px;font-weight:500;-webkit-text-fill-color:var(--muted);margin-left:6px}
.chip{font-size:11px;padding:3px 10px;border-radius:99px;font-weight:600;white-space:nowrap}
.chip-state{background:rgba(59,130,246,0.15);color:var(--accent)}
.chip-cost{background:rgba(16,185,129,0.1);color:var(--green);font-family:var(--mono)}
.spacer{flex:1}
#topbar .controls{display:flex;gap:8px;align-items:center}
#fileInput{display:none}

/* ---- Main Layout ---- */
#main{flex:1;display:grid;min-height:0;
  grid-template-columns:340px 1fr 380px;
  grid-template-rows:1fr;gap:0}
#main>section{min-height:0;min-width:0;display:flex;flex-direction:column;border-right:1px solid var(--border)}
#col-left{overflow:hidden}
#col-center{overflow:hidden;border-right:1px solid var(--border)}
#col-right{border-right:none;overflow:hidden}

/* ---- Panels (scrollable areas inside columns) ---- */
.col-scroll{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:12px}
.panel{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;backdrop-filter:var(--blur)}
.panel-head{display:flex;align-items:center;gap:8px;padding:10px 14px;border-bottom:1px solid var(--border);cursor:pointer;user-select:none}
.panel-head:hover{background:rgba(255,255,255,0.02)}
.panel-dot{width:8px;height:8px;border-radius:50%;flex:none;background:var(--dim);transition:background .3s}
.panel-dot.active{background:var(--green)}
.panel-dot.pulse{background:var(--accent);animation:pulse 1.5s ease infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(59,130,246,0.4)}50%{box-shadow:0 0 0 6px rgba(59,130,246,0)}}
.panel-dot.warn{background:var(--amber)}
.panel-title{font-size:13px;font-weight:700;flex:1}
.panel-chip{font-size:10px;color:var(--muted);font-family:var(--mono)}
.panel-toggle{color:var(--muted);background:none;font-size:14px;padding:2px 6px;transition:color .2s}
.panel-toggle:hover{color:var(--text)}
.panel-body{padding:14px;overflow:auto}
.panel.collapsed .panel-body{display:none}
.panel.collapsed .panel-head{border-bottom:none}

/* ---- Activity Feed ---- */
.activity-feed{display:flex;flex-direction:column;gap:2px}
.act-step{border:1px solid var(--border);border-radius:var(--radius-sm);overflow:hidden;transition:border-color .2s}
.act-step.current{border-color:var(--accent)}
.act-step-head{display:flex;align-items:center;gap:8px;padding:8px 12px;cursor:pointer;font-size:12px;transition:background .15s}
.act-step-head:hover{background:rgba(255,255,255,0.03)}
.act-icon{font-size:14px;flex:none;width:20px;text-align:center}
.act-label{flex:1;font-weight:500}
.act-time{font-size:10px;color:var(--muted);font-family:var(--mono)}
.act-status{width:6px;height:6px;border-radius:50%;flex:none}
.act-status.done{background:var(--green)}
.act-status.running{background:var(--accent);animation:pulse 1.2s ease infinite}
.act-status.pending{background:var(--dim)}
.act-status.error{background:var(--red)}
.act-detail{display:none;padding:4px 12px 10px 40px;font-size:11px;color:var(--muted)}
.act-step.open .act-detail{display:block}
.act-sub{padding:3px 0;border-left:2px solid var(--border);padding-left:10px;margin:2px 0}
.act-sub.fail{border-left-color:var(--red);color:var(--red)}
.act-sub.ok{border-left-color:var(--green)}

/* ---- Chat ---- */
.chat-area{display:flex;flex-direction:column;flex:1;min-height:0}
#chatLog{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}
.msg{max-width:92%;animation:fadeUp .2s ease}
@keyframes fadeUp{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.msg .who{font-size:10px;color:var(--muted);margin-bottom:3px;font-weight:600}
.msg .bub{border-radius:var(--radius-sm);padding:8px 12px;line-height:1.5;font-size:12px;display:inline-block;max-width:100%}
.msg.engine .bub{background:var(--card);border:1px solid var(--border)}
.msg.user{align-self:flex-end;text-align:right}
.msg.user .bub{background:var(--accent-g);color:#fff;border:none}
.msg.sys{align-self:center;text-align:center}
.msg.sys .bub{background:none;color:var(--muted);font-size:10px;padding:4px}
.caret{display:inline-block;width:2px;height:13px;background:var(--accent);vertical-align:-2px;animation:blink 1s steps(1) infinite;margin-left:1px}
@keyframes blink{50%{opacity:0}}
#chatForm{flex:none;display:flex;gap:8px;padding:10px 12px;border-top:1px solid var(--border)}
#chatInput{flex:1;min-width:0;background:rgba(255,255,255,0.04);border-color:var(--border)}

/* ---- Stat Grid ---- */
.stat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px}
.stat{border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 12px;background:var(--card)}
.stat .v{font-size:20px;font-weight:800;font-family:var(--mono)}
.stat .k{font-size:10px;color:var(--muted);margin-top:2px;font-weight:500}
.stat.accent .v{background:var(--accent-g);-webkit-background-clip:text;-webkit-text-fill-color:transparent}

/* ---- KV rows ---- */
.kv{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--border);font-size:12px}
.kv:last-child{border-bottom:none}
.kv .kl{color:var(--muted)}
.kv .kv-val{font-weight:600;font-family:var(--mono);text-align:right}

/* ---- Ribbon ---- */
.ribbon{display:flex;height:24px;border-radius:var(--radius-sm);overflow:hidden;border:1px solid var(--border)}
.ribbon div{display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#fff;white-space:nowrap;padding:0 6px;transition:width .5s ease}

/* ---- Signal bars ---- */
.sig{display:flex;align-items:center;gap:6px;font-size:10px;color:var(--muted);margin:2px 0}
.sig .bar{flex:1;height:4px;background:rgba(255,255,255,0.06);border-radius:2px;min-width:40px;overflow:hidden}
.sig .bar i{display:block;height:100%;background:var(--accent-g);border-radius:2px;transition:width .4s ease}
.sig .val{width:32px;text-align:right;color:var(--text);font-family:var(--mono)}

/* ---- Exception cards ---- */
.exc-card{border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px;margin-bottom:8px;background:var(--card);transition:border-color .2s}
.exc-card:hover{border-color:var(--border2)}
.exc-header{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.exc-actions{display:flex;gap:6px;margin-top:8px}

/* ---- Confidence bar ---- */
.conf-bar{display:inline-flex;align-items:center;gap:4px;font-size:10px;font-family:var(--mono)}
.conf-track{width:44px;height:5px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden}
.conf-fill{height:100%;border-radius:3px;transition:width .4s ease}

/* ---- Pagination ---- */
.pagination{display:flex;align-items:center;justify-content:center;gap:8px;padding:10px 0;font-size:11px;color:var(--muted)}
.pagination button{padding:4px 10px;border-radius:var(--radius-sm);background:var(--card);border:1px solid var(--border);color:var(--text);font-size:11px}
.pagination button:hover:not(:disabled){border-color:var(--accent)}
.pagination button:disabled{opacity:.3}

/* ---- Trace rows ---- */
.tev{padding:6px 10px;border-bottom:1px solid var(--border);font-size:11px}
.tev .t{color:var(--dim);font-size:10px;margin-right:6px;font-family:var(--mono)}
.tev .n{font-weight:600}
.tev .d{color:var(--muted);margin-top:2px;font-size:10px}

/* ---- Modal ---- */
#overlay{position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);z-index:100;display:none;align-items:flex-start;justify-content:center;padding-top:10vh}
#overlay.open{display:flex}
.modal{background:var(--surface);border:1px solid var(--border2);border-radius:var(--radius);width:500px;max-width:94vw;max-height:80vh;display:flex;flex-direction:column}
.modal-head{padding:14px 18px;border-bottom:1px solid var(--border);font-weight:700;font-size:15px}
.modal-body{padding:16px 18px;overflow:auto;flex:1}
.modal-foot{padding:12px 18px;border-top:1px solid var(--border);display:flex;gap:8px;justify-content:flex-end}

/* ---- Toast ---- */
#toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%) translateY(80px);background:var(--accent-g);color:#fff;padding:10px 20px;font-size:12px;font-weight:600;border-radius:var(--radius-sm);z-index:120;opacity:0;transition:all .3s ease}
#toast.show{transform:translateX(-50%) translateY(0);opacity:1}

/* ---- Responsive ---- */
@media(max-width:1100px){#main{grid-template-columns:300px 1fr}#col-right{display:none}}
@media(max-width:700px){#main{grid-template-columns:1fr;grid-template-rows:auto}#col-left{max-height:45vh}#col-center{min-height:50vh}}
</style>
</head>
<body>

<header id="topbar">
  <div id="brand">Recon Agent<small>financial reconciliation</small></div>
  <span class="chip chip-state" id="chipState">IDLE</span>
  <span class="chip chip-cost" id="chipCost">$0.0000</span>
  <div class="spacer"></div>
  <div class="controls">
    <input type="file" id="fileInput" multiple accept=".csv,.xlsx,.xls">
    <button class="btn btn-ghost btn-sm" id="btnUpload">Upload Files</button>
    <button class="btn btn-ghost btn-sm" id="btnSample">Sample Data</button>
    <button class="btn btn-primary btn-sm" id="btnStart">▶ Start Run</button>
    <button class="btn btn-danger btn-sm" id="btnAbort" disabled>Abort</button>
  </div>
</header>

<main id="main">
  <!-- LEFT: Activity Feed + Chat -->
  <section id="col-left">
    <div class="col-scroll">
      <!-- Activity Feed -->
      <div class="panel" id="p-activity">
        <div class="panel-head" onclick="togglePanel('activity')">
          <span class="panel-dot" id="dotActivity"></span>
          <span class="panel-title">Pipeline Activity</span>
          <span class="panel-chip" id="chipActivity">idle</span>
          <button class="panel-toggle" id="togActivity">▾</button>
        </div>
        <div class="panel-body" id="activityBody" style="padding:8px;max-height:280px;overflow-y:auto">
          <div class="activity-feed" id="actFeed">
            <div style="color:var(--muted);font-size:11px;padding:8px">Upload files and start a run to see pipeline activity.</div>
          </div>
        </div>
      </div>
      <!-- Chat -->
      <div class="panel" style="flex:1;display:flex;flex-direction:column;min-height:240px">
        <div class="panel-head">
          <span class="panel-dot active"></span>
          <span class="panel-title">Chat</span>
          <span class="panel-chip">grounded Q&A</span>
        </div>
        <div class="chat-area">
          <div id="chatLog"></div>
          <form id="chatForm">
            <input type="text" id="chatInput" placeholder="Ask about orders, fees, exceptions…" autocomplete="off">
            <button type="submit" class="btn btn-primary btn-sm">Send</button>
          </form>
        </div>
      </div>
    </div>
  </section>

  <!-- CENTER: Main Panels -->
  <section id="col-center">
    <div class="col-scroll" id="centerScroll">
      <!-- Panels will be rendered here dynamically -->
    </div>
  </section>

  <!-- RIGHT: Exceptions + Audit -->
  <section id="col-right">
    <div class="col-scroll" id="rightScroll">
      <!-- Exception queue + audit rendered here -->
    </div>
  </section>
</main>

<div id="overlay"></div>
<div id="toast"></div>

<script>
/* ===================== HELPERS ===================== */
const $=s=>document.querySelector(s);
const $$=s=>document.querySelectorAll(s);
const el=(tag,cls,html)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(html!==undefined)n.innerHTML=html;return n;};
const money=v=>'₹'+Number(v||0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2});
const pct=v=>v!=null?(v*100).toFixed(1)+'%':'—';
const nowT=()=>new Date().toLocaleTimeString('en-GB');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

/* ===================== SESSION STATE ===================== */
const API={sid:null,ws:null};
let S={
  state:'IDLE',running:false,abortToken:null,cost:0,
  tables:{},tableMeta:{},profiles:{},
  activity:[],traceEvents:[],logEvents:[],
  cfg:null,mapConf:0,candidates:[],
  exec:null,matchRate:null,precision:null,recall:null,throughput:null,
  queue:[],excSummary:{},final:null,
  audit:[],
  chatHistory:[]
};

/* ===================== HUMAN-FRIENDLY LABELS ===================== */
const STATE_LABELS={
  INGESTING:['📥','Ingesting uploaded files','Reading and parsing your CSV/Excel data files'],
  PROFILING:['📊','Profiling column statistics','Analyzing data types, cardinality, null rates, and PII patterns'],
  MAPPING_PROPOSED:['🔗','Discovering schema mappings','AI is analyzing column relationships to find key alignments'],
  MAPPING_VALIDATED:['✅','Validating schema alignment','Confirming the best column mapping with confidence scoring'],
  POLICY_GENERATED:['📋','Assembling reconciliation policy','Building matching rules: key, amount, date, fee model, tolerance'],
  DRY_RUN:['🧪','Running calibration dry-run','Testing matching engine on a sample subset to establish baseline'],
  EXECUTING:['⚡','Executing matching engine','Running full multi-attribute matching across all records'],
  INSPECTING:['🔍','Inspecting match quality','Checking match rate against revision threshold'],
  REVISION:['🔄','Revising tolerance parameters','Auto-tuning tolerance to improve match rate'],
  QA:['🏷️','Classifying exceptions','Categorizing unmatched records by root cause'],
  RESOLVING:['⚖️','Resolving exception actions','Auto-approving safe exceptions, flagging others for review'],
  AGGREGATING:['📊','Aggregating financial balances','Computing gross, net, fees, matched value, and signing audit chain'],
  ARCHIVED:['✨','Reconciliation complete','All records processed, report finalized, audit chain verified'],
  HALT:['⏸️','Pipeline halted','Waiting for user acknowledgment to continue'],
  ABORT_CONFIRMED:['🛑','Run aborted','Pipeline stopped by user request']
};
const TRACE_LABELS={
  'LLM_CALL_STARTED':'AI is analyzing data patterns',
  'LLM_CALL_FAILED':'AI analysis attempt failed, retrying',
  'LLM_CALL_COMPLETED':'AI analysis completed successfully',
  'LLM_FALLBACK':'Falling back to deterministic analysis',
  'CIRCUIT_BREAKER_OPEN':'Circuit breaker opened — too many failures',
  'CIRCUIT_BREAKER_CLOSED':'Circuit breaker reset — resuming normally',
  'SANDBOX_CREATED':'Secure sandbox environment created',
  'SANDBOX_DESTROYED':'Sandbox environment cleaned up',
  'CALIBRATION_DRIFT_WARNING':'Calibration drift detected — scores below expected',
  'INGEST_DONE':'All files parsed and normalized',
  'MAPPING_PROPOSED':'Schema mapping candidates discovered',
  'MAPPING_VALIDATED':'Schema mapping committed',
  'DRY_RUN_COMPLETED':'Dry-run calibration finished',
  'EXECUTION_COMPLETED':'Matching engine finished',
  'POLICY_REVISED':'Tolerance parameters adjusted',
  'RUN_COMPLETE':'Pipeline run completed successfully'
};
function friendlyTrace(name,detail){
  if(name.startsWith('tool_ok:'))return '✅ '+name.replace('tool_ok:','').replace(/_/g,' ')+' tool completed';
  if(name.startsWith('llm_fallback:'))return '🔀 Fell back to deterministic path for '+name.split(':')[1];
  if(name.startsWith('cost_overrun:'))return '💰 Cost overrun on '+name.split(':')[1];
  if(name==='AUDIT_COMMIT')return '🔒 Audit record committed';
  return TRACE_LABELS[name]||(name.replace(/_/g,' '));
}

/* ===================== API CLIENT ===================== */
async function apiJSON(path,opts){
  const r=await fetch(path,opts);
  if(!r.ok)throw new Error(r.status+' '+r.statusText);
  return r.json();
}
const apiPost=(path,body)=>apiJSON(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});

async function createSession(){
  const d=await apiJSON('/api/v2/sessions',{method:'POST'});
  API.sid=d.session_id;
  return API.sid;
}
function uploadAndRun(files){
  const fd=new FormData();
  Array.from(files).forEach(f=>fd.append('files',f));
  return apiJSON('/api/v2/sessions/'+API.sid+'/run',{method:'POST',body:fd});
}
function fetchPanel(name,params){
  let qs=params?'?'+new URLSearchParams(params):'';
  return apiJSON('/api/v2/sessions/'+API.sid+'/'+name+qs);
}
function overrideException(rid,action,note){
  return apiPost('/api/v2/sessions/'+API.sid+'/exceptions/'+rid+'/action',{action,note:note||''});
}
function sendChat(message){return apiPost('/api/v2/sessions/'+API.sid+'/chat',{message});}
function resumeRun(){return apiJSON('/api/v2/sessions/'+API.sid+'/resume',{method:'POST'});}
function abortRun(token){return apiPost('/api/v2/sessions/'+API.sid+'/abort',{token});}

/* ===================== WEBSOCKET ===================== */
function connectWS(){
  if(!API.sid)return;
  const proto=location.protocol==='https:'?'wss':'ws';
  API.ws=new WebSocket(proto+'://'+location.host+'/ws/v2/'+API.sid);
  API.ws.onmessage=function(e){
    let ev;try{ev=JSON.parse(e.data);}catch(_){return;}
    handleWSEvent(ev);
  };
  API.ws.onclose=function(){setTimeout(()=>{if(API.sid)connectWS();},2000);};
}
function handleWSEvent(ev){
  const p=ev.payload||{};
  // Priority 1: Chat/narration/control
  if(ev.kind==='chat'&&p.text){
    addEngineMsg(p.text);
  }
  if(ev.kind==='control'){
    if(p.event==='STATE_ENTERED'){
      S.state=p.state||S.state;
      S.abortToken=p.abort_token||S.abortToken;
      addActivityStep(p.state,p.abort_token);
      updateChips();
    }
    if(p.event==='STATE_EXITED'){
      completeActivityStep(p.state);
    }
    if(p.event==='HALT'){
      S.state='HALT';updateChips();
      addEngineMsg('⏸️ Pipeline halted: '+(p.detail?.reason||'unknown reason')+'. Click Resume to continue.');
    }
    if(p.event==='RESUMED'){
      addEngineMsg('▶️ Pipeline resumed.');
    }
    if(p.event==='ABORT_CONFIRMED'){
      S.state='ABORT_CONFIRMED';S.running=false;updateChips();
      addEngineMsg('🛑 Run aborted.');
    }
  }
  // Priority 2: Trace
  if(ev.priority===2){
    S.traceEvents.push(ev);
    appendTraceToActivity(p.event||ev.kind,JSON.stringify(p.detail||{}).slice(0,120));
  }
  // Priority 3: Logs
  if(ev.priority===3){
    S.logEvents.push(ev);
  }
  // Artifact: refresh panels
  if(ev.kind==='artifact'){
    if(p.kind==='report')refreshResults();
    if(p.kind==='exceptions')refreshExceptions();
  }
}

/* ===================== ACTIVITY FEED ===================== */
let actSteps=[];
function resetActivity(){
  actSteps=[];S.traceEvents=[];S.logEvents=[];
  $('#actFeed').innerHTML='';
}
function addActivityStep(state){
  const info=STATE_LABELS[state]||['⏳',state.replace(/_/g,' '),'Processing...'];
  // Mark previous step as done
  if(actSteps.length){
    const prev=actSteps[actSteps.length-1];
    prev.status='done';
    const el=document.getElementById('act-'+prev.state);
    if(el){el.classList.remove('current');el.querySelector('.act-status').className='act-status done';}
  }
  const step={state,icon:info[0],label:info[1],desc:info[2],status:'running',subs:[],time:nowT()};
  actSteps.push(step);
  const feed=$('#actFeed');
  const div=document.createElement('div');div.className='act-step current';div.id='act-'+state;
  div.innerHTML=`<div class="act-step-head" onclick="toggleActStep('${state}')">
    <span class="act-icon">${step.icon}</span>
    <span class="act-label">${step.label}</span>
    <span class="act-time">${step.time}</span>
    <span class="act-status running"></span>
  </div>
  <div class="act-detail" id="actd-${state}"><div style="color:var(--dim);font-size:10px">${step.desc}</div></div>`;
  feed.appendChild(div);
  div.scrollIntoView({behavior:'smooth',block:'nearest'});
  $('#chipActivity').textContent=step.label;
  $('#dotActivity').className='panel-dot pulse';
}
function completeActivityStep(state){
  const step=actSteps.find(s=>s.state===state);
  if(step)step.status='done';
  const el=document.getElementById('act-'+state);
  if(el){el.classList.remove('current');el.querySelector('.act-status').className='act-status done';}
}
function appendTraceToActivity(evName,detail){
  if(!actSteps.length)return;
  const step=actSteps[actSteps.length-1];
  const friendly=friendlyTrace(evName,detail);
  step.subs.push({name:friendly,detail,fail:evName.includes('FAIL')||evName.includes('failed')});
  const detEl=document.getElementById('actd-'+step.state);
  if(detEl){
    const sub=document.createElement('div');
    sub.className='act-sub'+(evName.includes('FAIL')||evName.includes('failed')?' fail':' ok');
    sub.textContent=friendly;
    detEl.appendChild(sub);
  }
}
function toggleActStep(state){
  const el=document.getElementById('act-'+state);
  if(el)el.classList.toggle('open');
}

/* ===================== CHAT ===================== */
function addEngineMsg(text){
  const log=$('#chatLog');if(!log)return;
  const m=el('div','msg engine','<div class="who">engine</div>');
  const b=el('span','bub');b.textContent=text;m.appendChild(b);log.appendChild(m);
  log.scrollTop=log.scrollHeight;
}
function addUserMsg(text){
  const log=$('#chatLog');if(!log)return;
  const m=el('div','msg user','<div class="who">you</div>');
  const b=el('span','bub');b.textContent=text;m.appendChild(b);log.appendChild(m);
  log.scrollTop=log.scrollHeight;
}
function addSysMsg(text){
  const log=$('#chatLog');if(!log)return;
  const m=el('div','msg sys');const b=el('span','bub');b.textContent=text;m.appendChild(b);log.appendChild(m);
  log.scrollTop=log.scrollHeight;
}

$('#chatForm').onsubmit=async e=>{
  e.preventDefault();
  const v=$('#chatInput').value.trim();if(!v)return;
  $('#chatInput').value='';
  addUserMsg(v);
  // Handle local commands
  if(v.toLowerCase()==='status'){
    addEngineMsg('State: '+S.state+' · Cost: $'+S.cost.toFixed(4)+(S.matchRate!=null?' · Match rate: '+pct(S.matchRate):''));return;}
  if(v.toLowerCase()==='help'){
    addEngineMsg('Commands: status, help. After a run, ask about specific orders (e.g. "ORD_2"), fees, balances, or exceptions.');return;}
  // Send to backend
  try{
    const r=await sendChat(v);
    if(r.ok)addEngineMsg(r.response);
    else addEngineMsg('⚠️ '+(r.error||r.response||'Failed to get response'));
  }catch(e){addEngineMsg('⚠️ Chat error: '+e.message);}
};

/* ===================== PANEL RENDERING ===================== */
function togglePanel(id){
  const p=$('#p-'+id);if(p)p.classList.toggle('collapsed');
}
function updateChips(){
  $('#chipState').textContent=S.state;
  $('#chipCost').textContent='$'+(S.cost||0).toFixed(4);
  $('#btnAbort').disabled=!S.running;
  if(S.state==='ARCHIVED'||S.state==='ABORT_CONFIRMED'||S.state==='IDLE'){
    $('#dotActivity').className='panel-dot'+(S.state==='ARCHIVED'?' active':'');
    if(S.state==='ARCHIVED')$('#chipActivity').textContent='complete';
  }
}

/* ---- Ingestion Panel ---- */
function renderIngestion(data){
  let h='';
  if(!data.table_meta||!Object.keys(data.table_meta).length){
    return '<div style="color:var(--muted);padding:16px;text-align:center">No files ingested yet. Upload CSV/Excel files or load sample data.</div>';
  }
  for(const [name,meta] of Object.entries(data.table_meta)){
    const pg=data.tables[name];
    const rows=pg?pg.items:[];
    const prof=(data.profiles||{})[name]||[];
    h+=`<div style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="font-weight:700">${name}</span>
        <span class="badge badge-info">${meta.total_rows.toLocaleString()} records · ${meta.columns.length} cols</span>
      </div>`;
    // Profile table
    if(prof.length){
      h+='<table><thead><tr><th>Column</th><th>Type</th><th>Numeric</th><th>Date</th><th>Cardinality</th><th>Nulls</th><th>Samples</th></tr></thead><tbody>';
      prof.forEach(p=>{
        h+=`<tr><td style="font-weight:600">${p.name}</td><td>${p.dtype}</td>
          <td>${p.numeric_ratio.toFixed(2)}</td><td>${p.date_ratio.toFixed(2)}</td>
          <td>${p.cardinality.toFixed(2)}</td><td>${p.null_rate.toFixed(2)}</td>
          <td style="color:var(--muted);font-size:10px">${(p.sample_values||[]).join(', ')}</td></tr>`;
      });
      h+='</tbody></table>';
    }
    // Data preview
    if(rows.length){
      const cols=meta.columns;
      h+=`<details style="margin-top:8px"><summary style="cursor:pointer;color:var(--muted);font-size:11px">Data preview (page ${pg.page}/${pg.total_pages}, showing ${rows.length} of ${pg.total})</summary>
        <div style="max-height:200px;overflow:auto;margin-top:4px">
        <table><thead><tr><th>#</th>${cols.map(c=>'<th>'+c+'</th>').join('')}</tr></thead><tbody>
        ${rows.map(r=>'<tr><td>'+r._rid+'</td>'+cols.map(c=>'<td>'+(r[c]??'')+'</td>').join('')+'</tr>').join('')}
        </tbody></table></div>`;
      if(pg.total_pages>1){
        h+=`<div class="pagination">
          <button onclick="loadIngestionPage('${name}',${pg.page-1})" ${pg.has_prev?'':'disabled'}>← Prev</button>
          <span>Page ${pg.page} of ${pg.total_pages}</span>
          <button onclick="loadIngestionPage('${name}',${pg.page+1})" ${pg.has_next?'':'disabled'}>Next →</button>
        </div>`;
      }
      h+='</details>';
    }
    h+='</div>';
  }
  return h;
}
async function loadIngestionPage(table,page){
  try{
    const data=await fetchPanel('ingestion',{table,page,page_size:100});
    // Re-render just the ingestion panel body
    const body=$('#ingestionBody');
    if(body)body.innerHTML=renderIngestion(data);
  }catch(e){toast('Failed to load page: '+e.message);}
}

/* ---- Mapping Panel ---- */
function renderMapping(data){
  if(!data.candidates||!data.candidates.length){
    return '<div style="color:var(--muted);text-align:center;padding:16px">Mapping candidates appear after profiling.</div>';
  }
  let h='<div style="color:var(--muted);font-size:11px;margin-bottom:10px">Confidence = 0.35·structural + 0.30·sample + 0.20·type + 0.15·semantic</div>';
  h+='<table><thead><tr><th>Candidate</th><th>Signals</th><th>Score</th><th>Band</th></tr></thead><tbody>';
  data.candidates.forEach(c=>{
    const sig=c.signals;
    const bandCls=c.band==='auto'?'badge-auto':(c.band==='confirm'?'badge-review':'badge-error');
    h+=`<tr><td style="font-weight:600">${c.left} ↔ ${c.right}</td>
      <td style="min-width:160px">
        ${['structural_overlap','sample_match_rate','type_compatibility','semantic_plausibility'].map(k=>
          `<div class="sig"><span style="width:52px;font-size:10px">${k.split('_')[0]}</span><div class="bar"><i style="width:${(sig[k]*100)}%"></i></div><span class="val">${sig[k].toFixed(2)}</span></div>`
        ).join('')}
      </td>
      <td><span style="font-weight:700;font-family:var(--mono)">${c.composite.toFixed(3)}</span></td>
      <td><span class="badge ${bandCls}">${c.band}</span></td></tr>`;
  });
  h+='</tbody></table>';
  if(data.committed){
    h+=`<div style="margin-top:12px;border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px">
      <div style="font-weight:700;margin-bottom:6px">Committed Mapping <span class="badge badge-auto">conf ${data.confidence.toFixed(3)}</span></div>
      ${['left_key','right_key','left_amount','right_amount','left_date','right_date','tolerance','window_days'].map(k=>
        `<div class="kv"><span class="kl">${k}</span><span class="kv-val">${data.committed[k]??'—'}</span></div>`
      ).join('')}
    </div>`;
  }
  return h;
}

/* ---- Results Panel ---- */
function renderResults(data){
  if(!data.executed)return '<div style="color:var(--muted);text-align:center;padding:16px">Results appear after the matching engine runs.</div>';
  let h='';
  // Stat grid
  h+=`<div class="stat-grid">
    <div class="stat accent"><div class="v">${pct(data.match_rate)}</div><div class="k">match rate</div></div>
    <div class="stat"><div class="v">${data.matched?.length||0}</div><div class="k">matched</div></div>
    <div class="stat"><div class="v">${data.unmatched_count||0}</div><div class="k">unmatched</div></div>
    <div class="stat"><div class="v">${pct(data.precision_vs_truth)}</div><div class="k">precision</div></div>
    <div class="stat"><div class="v">${pct(data.recall_vs_truth)}</div><div class="k">recall</div></div>
    <div class="stat"><div class="v">${(data.throughput_rows_per_sec||0).toFixed(0)} r/s</div><div class="k">throughput</div></div>
  </div>`;
  // Financial balances
  if(data.totals){
    h+=`<div style="margin-top:12px;border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px">
      <div style="font-weight:700;margin-bottom:6px">Financial Balances</div>
      ${[['Gross ledger',data.totals.gross],['Net bank inflow',data.totals.net],['Fees variance',data.totals.fees],
        ['Matched value',data.totals.matched_value],['Exception value',data.totals.exception_value]]
        .map(([k,v])=>`<div class="kv"><span class="kl">${k}</span><span class="kv-val">${money(v)}</span></div>`).join('')}
    </div>`;
  }
  // Match table
  if(data.matched&&data.matched.length){
    h+=`<details style="margin-top:12px"><summary style="cursor:pointer;font-weight:600;font-size:12px">Matched Pairs (${data.matched.length})</summary>
      <table style="margin-top:6px"><thead><tr><th>L</th><th>R</th><th>Score</th><th>Key</th><th>Amount</th><th>Date</th></tr></thead><tbody>
      ${data.matched.slice(0,200).map(m=>`<tr><td>${m.l_rid}</td><td>${m.r_rid}</td>
        <td style="font-weight:700;font-family:var(--mono)">${m.composite_score.toFixed(3)}</td>
        <td>${(m.components.key||0).toFixed(2)}</td><td>${(m.components.amount||0).toFixed(2)}</td>
        <td>${(m.components.date||0).toFixed(2)}</td></tr>`).join('')}
      </tbody></table>
      ${data.matched.length>200?'<div style="color:var(--muted);font-size:11px;padding:8px">Showing first 200 of '+data.matched.length+' matches</div>':''}
    </details>`;
  }
  // Final report
  if(data.final_report){
    const f=data.final_report;
    h+=`<div style="margin-top:14px;border-top:1px solid var(--border);padding-top:12px">
      <div style="font-size:11px;color:var(--muted);margin-bottom:8px;font-weight:600">FINAL REPORT</div>
      <div class="stat-grid">
        <div class="stat accent"><div class="v">${pct(f.match_rate)}</div><div class="k">match rate</div></div>
        <div class="stat"><div class="v">${f.honest_exception_count}</div><div class="k">exceptions</div></div>
        <div class="stat"><div class="v">${f.auto_resolved_count}</div><div class="k">auto-resolved</div></div>
        <div class="stat"><div class="v">${f.escalated_count}</div><div class="k">needs review</div></div>
        <div class="stat"><div class="v">${money(f.matched_value)}</div><div class="k">matched value</div></div>
        <div class="stat"><div class="v">$${f.cost_usd.toFixed(4)}</div><div class="k">LLM cost</div></div>
      </div>
      <div style="margin-top:8px">
        <button class="btn btn-ghost btn-sm" onclick="downloadJSON('report.json',${JSON.stringify(JSON.stringify(f))})">Download Report</button>
      </div>
    </div>`;
  }
  return h;
}

/* ---- Exceptions Panel ---- */
function renderExceptions(data){
  if(!data.queue||!data.queue.length){
    return '<div style="color:var(--muted);text-align:center;padding:16px">Exception queue populates after QA classification.</div>';
  }
  const sm=data.summary||{};
  let h=`<div class="ribbon" style="margin-bottom:10px">
    <div style="width:${(sm.auto_resolved||0)/(sm.total||1)*100}%;background:var(--green)">${sm.auto_resolved||0} auto</div>
    <div style="width:${(sm.needs_review||0)/(sm.total||1)*100}%;background:var(--amber)">${sm.needs_review||0} review</div>
    <div style="width:${(sm.pending||0)/(sm.total||1)*100}%;background:var(--dim)">${sm.pending||0} pending</div>
  </div>
  <div style="color:var(--muted);font-size:11px;margin-bottom:8px">Auto-approve gate: confidence ≥ 0.85 ∧ evidence ≥ 2</div>`;
  data.queue.forEach(q=>{
    const confPct=Math.round((q.confidence||0)*100);
    const confColor=q.confidence>=0.85?'var(--green)':(q.confidence>=0.4?'var(--amber)':'var(--red)');
    const actionBadge=q.action==='auto_resolve'||q.action==='mark_resolved'?'<span class="badge badge-auto">AUTO · NO ERROR</span>':
      q.action==='request_confirmation'?'<span class="badge badge-review">NEEDS REVIEW</span>':
      q.action==='escalate'?'<span class="badge badge-error">ESCALATED</span>':'<span class="badge badge-pending">PENDING</span>';
    h+=`<div class="exc-card">
      <div class="exc-header">
        <span style="font-weight:700">#${q.rid}</span>
        <span class="badge badge-info">${q.side}</span>
        <span class="badge" style="background:rgba(168,85,247,0.15);color:var(--purple)">${q.reason}</span>
        <span style="color:var(--muted);font-size:11px">ref: ${q.ref||'—'}</span>
        <div class="spacer"></div>
        ${actionBadge}
      </div>
      <div class="conf-bar" style="margin-top:6px">
        <span style="color:var(--muted)">confidence</span>
        <div class="conf-track"><div class="conf-fill" style="width:${confPct}%;background:${confColor}"></div></div>
        <span style="color:${confColor}">${q.confidence.toFixed(2)}</span>
        <span style="color:var(--muted);margin-left:8px">evidence: ${(q.pieces||[]).length}</span>
      </div>
      <div style="font-size:12px;margin-top:6px;line-height:1.5">${q.explanation||'No diagnostic available.'}</div>
      ${q.delta!=null?'<div style="font-size:11px;color:var(--muted);margin-top:4px">Delta: '+money(q.delta)+'</div>':''}
      ${q.action==='request_confirmation'?`<div class="exc-actions">
        <button class="btn btn-primary btn-sm" onclick="doOverride(${q.rid},'approve')">Approve</button>
        <button class="btn btn-ghost btn-sm" onclick="doOverride(${q.rid},'escalate')">Escalate</button>
      </div>`:''}
    </div>`;
  });
  // Pagination
  if(data.pagination&&data.pagination.total_pages>1){
    const pg=data.pagination;
    h+=`<div class="pagination">
      <button onclick="loadExceptionsPage(${pg.page-1})" ${pg.has_prev?'':'disabled'}>← Prev</button>
      <span>Page ${pg.page} of ${pg.total_pages} (${pg.total} total)</span>
      <button onclick="loadExceptionsPage(${pg.page+1})" ${pg.has_next?'':'disabled'}>Next →</button>
    </div>`;
  }
  return h;
}
async function loadExceptionsPage(page){
  try{
    const data=await fetchPanel('exceptions',{page,page_size:50});
    const body=$('#exceptionsBody');if(body)body.innerHTML=renderExceptions(data);
  }catch(e){toast('Failed: '+e.message);}
}
async function doOverride(rid,action){
  const note=prompt((action==='approve'?'Approve':'Escalate')+' exception #'+rid+'?\nOptional note (recorded in audit):');
  if(note===null)return;
  try{
    await overrideException(rid,action,note);
    toast('Exception #'+rid+' '+action+'d');
    refreshExceptions();
  }catch(e){toast('Error: '+e.message);}
}

/* ---- Audit Panel ---- */
function renderAudit(data){
  const verified=data.verified;
  let h=`<div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
    <span class="badge ${verified?'badge-auto':'badge-error'}">${verified?'CHAIN VERIFIED':'CHAIN TAMPERED'}</span>
    <span style="color:var(--muted);font-size:11px">${data.count||0} records</span>
    <div class="spacer"></div>
    <button class="btn btn-ghost btn-sm" onclick="downloadJSON('audit.jsonl',${JSON.stringify(JSON.stringify(data.records||[]))})">Export</button>
  </div>`;
  const recs=(data.records||[]).slice().reverse().slice(0,50);
  if(!recs.length)return h+'<div style="color:var(--muted);text-align:center;padding:16px">No audit records yet.</div>';
  h+='<table><thead><tr><th>#</th><th>Event</th><th>Details</th></tr></thead><tbody>';
  recs.forEach((r,i)=>{
    const p=typeof r==='string'?JSON.parse(r):r;
    const ev=p.event||p.payload?.event||'—';
    h+=`<tr><td style="font-family:var(--mono)">${recs.length-i}</td>
      <td><span style="font-weight:600">${ev}</span>${p.decision_kind?' · '+p.decision_kind:''}</td>
      <td style="font-size:10px;color:var(--muted);max-width:200px;overflow:hidden;text-overflow:ellipsis">${JSON.stringify(p).slice(0,120)}</td></tr>`;
  });
  h+='</tbody></table>';
  return h;
}

/* ---- Policy Panel ---- */
function renderPolicy(data){
  if(!data.components||!data.components.length){
    return '<div style="color:var(--muted);text-align:center;padding:16px">Policy is generated after mapping validation.</div>';
  }
  let h=`<div class="stat-grid" style="margin-bottom:12px">
    <div class="stat"><div class="v">${data.baseline_match_rate!=null?data.baseline_match_rate.toFixed(3):'—'}</div><div class="k">baseline (dry-run)</div></div>
    <div class="stat accent"><div class="v">${data.current_match_rate!=null?data.current_match_rate.toFixed(3):'—'}</div><div class="k">current (live)</div></div>
  </div>`;
  h+='<table><thead><tr><th>Prec</th><th>Component</th><th>Enabled</th><th>Params</th></tr></thead><tbody>';
  data.components.forEach(c=>{
    h+=`<tr><td><span class="badge badge-info">${c.precedence}</span></td>
      <td style="font-weight:600">${(c.component||'').replace(/_/g,' ')}</td>
      <td>${c.enabled?'✅':'—'}</td>
      <td style="font-size:10px;color:var(--muted)">${JSON.stringify(c.params||{})}</td></tr>`;
  });
  h+='</tbody></table>';
  if(data.fee_schedules&&data.fee_schedules.length){
    h+=`<div style="margin-top:10px;color:var(--muted);font-size:11px">Fee schedule: ${data.fee_schedules.map(f=>f.provider+' · '+f.schedule_id).join(', ')}</div>`;
  }
  return h;
}

/* ===================== PANEL STRUCTURE ===================== */
function buildPanels(){
  const center=$('#centerScroll');
  const right=$('#rightScroll');
  center.innerHTML='';right.innerHTML='';

  // Center panels
  const centerPanels=[
    {id:'ingestion',title:'Ingestion',chip:'data preview'},
    {id:'mapping',title:'Mapping',chip:'schema alignment'},
    {id:'policy',title:'Policy',chip:'matching rules'},
    {id:'results',title:'Results',chip:'match output'},
  ];
  centerPanels.forEach(p=>{
    const div=el('div','panel');div.id='p-'+p.id;
    div.innerHTML=`<div class="panel-head" onclick="togglePanel('${p.id}')">
      <span class="panel-dot" id="dot-${p.id}"></span>
      <span class="panel-title">${p.title}</span>
      <span class="panel-chip">${p.chip}</span>
      <button class="panel-toggle">▾</button>
    </div>
    <div class="panel-body" id="${p.id}Body">
      <div style="color:var(--muted);text-align:center;padding:16px">Waiting for pipeline data…</div>
    </div>`;
    center.appendChild(div);
  });

  // Right panels
  const rightPanels=[
    {id:'exceptions',title:'Exception Queue',chip:'review'},
    {id:'audit',title:'Audit Chain',chip:'hash-linked'},
  ];
  rightPanels.forEach(p=>{
    const div=el('div','panel');div.id='p-'+p.id;
    div.innerHTML=`<div class="panel-head" onclick="togglePanel('${p.id}')">
      <span class="panel-dot" id="dot-${p.id}"></span>
      <span class="panel-title">${p.title}</span>
      <span class="panel-chip">${p.chip}</span>
      <button class="panel-toggle">▾</button>
    </div>
    <div class="panel-body" id="${p.id}Body">
      <div style="color:var(--muted);text-align:center;padding:16px">Waiting for pipeline data…</div>
    </div>`;
    right.appendChild(div);
  });
}

/* ===================== REFRESH PANELS ===================== */
async function refreshIngestion(){
  try{
    const data=await fetchPanel('ingestion');
    const body=$('#ingestionBody');if(body)body.innerHTML=renderIngestion(data);
    const dot=$('#dot-ingestion');if(dot&&data.table_meta&&Object.keys(data.table_meta).length)dot.className='panel-dot active';
  }catch(e){}
}
async function refreshMapping(){
  try{
    const data=await fetchPanel('mapping');
    const body=$('#mappingBody');if(body)body.innerHTML=renderMapping(data);
    const dot=$('#dot-mapping');if(dot&&data.committed)dot.className='panel-dot active';
  }catch(e){}
}
async function refreshPolicy(){
  try{
    const data=await fetchPanel('policy');
    const body=$('#policyBody');if(body)body.innerHTML=renderPolicy(data);
    const dot=$('#dot-policy');if(dot&&data.components?.length)dot.className='panel-dot active';
  }catch(e){}
}
async function refreshResults(){
  try{
    const data=await fetchPanel('results');
    const body=$('#resultsBody');if(body)body.innerHTML=renderResults(data);
    S.matchRate=data.match_rate;S.precision=data.precision_vs_truth;S.recall=data.recall_vs_truth;
    S.final=data.final_report;S.cost=data.final_report?.cost_usd||S.cost;
    updateChips();
    const dot=$('#dot-results');if(dot&&data.executed)dot.className='panel-dot active';
  }catch(e){}
}
async function refreshExceptions(){
  try{
    const data=await fetchPanel('exceptions');
    const body=$('#exceptionsBody');if(body)body.innerHTML=renderExceptions(data);
    const dot=$('#dot-exceptions');
    if(dot){
      if(data.summary?.needs_review>0)dot.className='panel-dot warn';
      else if(data.summary?.total>0)dot.className='panel-dot active';
    }
  }catch(e){}
}
async function refreshAudit(){
  try{
    const data=await fetchPanel('audit');
    const body=$('#auditBody');if(body)body.innerHTML=renderAudit(data);
    const dot=$('#dot-audit');if(dot&&data.count>0)dot.className='panel-dot active';
  }catch(e){}
}
async function refreshAll(){
  await Promise.allSettled([refreshIngestion(),refreshMapping(),refreshPolicy(),refreshResults(),refreshExceptions(),refreshAudit()]);
}
// Poll for updates while running
let pollTimer=null;
function startPolling(){
  if(pollTimer)return;
  pollTimer=setInterval(async()=>{
    if(!API.sid)return;
    try{
      const ov=await fetchPanel('overview');
      S.state=ov.state||S.state;
      S.cost=ov.cost_usd||S.cost;
      updateChips();
      // Refresh panels based on state
      await refreshAll();
      // Stop polling when archived or aborted
      if(S.state==='ARCHIVED'||S.state==='ABORT_CONFIRMED'||S.state==='IDLE'){
        S.running=false;updateChips();stopPolling();
      }
    }catch(e){}
  },2500);
}
function stopPolling(){if(pollTimer){clearInterval(pollTimer);pollTimer=null;}}

/* ===================== MAIN ACTIONS ===================== */
async function startRun(files){
  if(S.running){toast('A run is already in progress.');return;}
  if(!files||!files.length){toast('No files selected.');return;}
  if(files.length<2){toast('Need at least 2 files (ledger + statement).');return;}
  S.running=true;S.state='STARTING';
  resetActivity();updateChips();
  addSysMsg('Starting reconciliation run…');
  try{
    const r=await uploadAndRun(files);
    addEngineMsg('🚀 Pipeline started with '+r.files.join(', ')+'. Watch the Activity Feed for progress.');
    startPolling();
  }catch(e){
    S.running=false;updateChips();
    addEngineMsg('❌ Failed to start: '+e.message);
  }
}

/* ---- Sample data helper ---- */
async function loadSampleData(){
  if(S.running){toast('A run is already in progress.');return;}
  addSysMsg('Loading sample dataset…');
  // Create sample CSV blobs
  const payCSV='order_id,amount,date\nORD_1,1000,2026-03-01\nORD_2,2000,2026-03-01\nORD_3,3000,2026-03-06\nORD_4,500,2026-03-02\nORD_4,500,2026-03-02\nORD_6,400,2026-03-02\nORD_7,700,2026-03-02\nMIS_800,900,2026-03-03';
  const bankCSV='utr,credit,date\nORD_1,1000,2026-03-02\nORD_2,1952.80,2026-03-02\nORD_3,3000,2026-03-13\nORD_4,500,2026-03-03\nBATCH,1074.04,2026-03-03\nORD_9,850,2026-03-05\nREFUND,-250,2026-03-05';
  const payFile=new File([payCSV],'payments.csv',{type:'text/csv'});
  const bankFile=new File([bankCSV],'bank.csv',{type:'text/csv'});
  addEngineMsg('📦 Sample data: payments (8 records) + bank (7 records). Starting run…');
  await startRun([payFile,bankFile]);
}

/* ===================== UTILITIES ===================== */
function downloadJSON(name,text){
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([text],{type:'application/json'}));
  a.download=name;a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),2000);
  toast('Downloaded '+name);
}
let toastTimer=null;
function toast(msg){
  const t=$('#toast');t.textContent=msg;t.classList.add('show');
  clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('show'),3000);
}

/* ===================== INIT ===================== */
async function init(){
  buildPanels();
  try{
    await createSession();
    connectWS();
    addSysMsg('Session '+API.sid+' initialized. Upload files or load sample data to begin.');
  }catch(e){
    addEngineMsg('⚠️ Could not connect to backend: '+e.message+'. Check that the server is running.');
  }
}

/* ---- Wire up buttons ---- */
$('#btnUpload').onclick=()=>$('#fileInput').click();
$('#fileInput').onchange=e=>{
  const files=[...e.target.files];
  if(files.length)startRun(files);
  e.target.value='';
};
$('#btnSample').onclick=loadSampleData;
$('#btnStart').onclick=()=>{
  if(!S.running){
    // If no files selected, prompt
    $('#fileInput').click();
  }
};
$('#btnAbort').onclick=async()=>{
  if(S.abortToken){
    try{await abortRun(S.abortToken);toast('Abort requested.');}
    catch(e){toast('Abort failed: '+e.message);}
  }
};

updateChips();
init();
</script>
</body>
</html>

```

### recon_agent/tests/__init__.py

```python


```

### recon_agent/tests/conftest.py

```python
import os
import shutil
import tempfile
import pytest
from pathlib import Path


@pytest.fixture(autouse=True, scope="session")
def isolate_test_environment():
    """Ensure tests write temporary logs and audit files to a temporary directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix="recon_test_"))
    test_audit = temp_dir / "audit"
    test_logs = temp_dir / "logs"
    test_uploads = temp_dir / "uploads"
    test_audit.mkdir(parents=True, exist_ok=True)
    test_logs.mkdir(parents=True, exist_ok=True)
    test_uploads.mkdir(parents=True, exist_ok=True)

    old_audit = os.environ.get("RECON_AUDIT_DIR")
    old_logs = os.environ.get("RECON_LOGS_DIR")
    os.environ["RECON_AUDIT_DIR"] = str(test_audit)
    os.environ["RECON_LOGS_DIR"] = str(test_logs)

    # Import modules to patch directories
    from app.core import audit
    from app import config
    audit.AUDIT_DIR = test_audit
    config.AUDIT_DIR = test_audit
    config.LOGS_DIR = test_logs
    config.UPLOAD_DIR = test_uploads

    yield

    # Cleanup after test session
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    if old_audit is not None:
        os.environ["RECON_AUDIT_DIR"] = old_audit
    else:
        os.environ.pop("RECON_AUDIT_DIR", None)
    if old_logs is not None:
        os.environ["RECON_LOGS_DIR"] = old_logs
    else:
        os.environ.pop("RECON_LOGS_DIR", None)

```

### recon_agent/tests/test_api_v2_e2e.py

```python
import io
import json
import sys
import time
import requests
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

BASE_URL = "http://127.0.0.1:8000"

def test_api_v2_full_suite():
    print("==================================================")
    print("🚀 STARTING RECONCILIATION AGENT API v2 TEST SUITE")
    print("==================================================")

    # 1. Test Session Creation
    print("\n[Step 1] Creating new session...")
    r = requests.post(f"{BASE_URL}/api/v2/sessions")
    assert r.status_code == 200, f"Session creation failed: {r.text}"
    sid = r.json()["session_id"]
    print(f"✅ Session Created: {sid}")

    # 2. Test Overview (Empty State)
    print("\n[Step 2] Testing initial overview...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/overview")
    assert r.status_code == 200
    ov = r.json()
    assert ov["state"] == "IDLE"
    print(f"✅ Initial State: {ov['state']}, Constants Version: {ov['constants_version']}")

    # 3. Test File Upload & Run with Sample Data
    print("\n[Step 3] Testing multipart file upload and reconciliation run...")
    with open("sample_data/payments.csv", "rb") as f1, open("sample_data/bank.csv", "rb") as f2:
        files = [
            ("files", ("payments.csv", f1, "text/csv")),
            ("files", ("bank.csv", f2, "text/csv")),
        ]
        r = requests.post(f"{BASE_URL}/api/v2/sessions/{sid}/run", files=files)
    assert r.status_code == 200, f"Upload run failed: {r.text}"
    print(f"✅ Upload & Run triggered: {r.json()['files']}")

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
    print(f"✅ Pipeline reached {final_state} in {time.time() - start_t:.2f}s")

    # 5. Test Ingestion Endpoint & Pagination
    print("\n[Step 5] Testing /ingestion endpoint & metadata...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/ingestion")
    assert r.status_code == 200
    ing = r.json()
    assert "table_meta" in ing
    assert "payments" in ing["table_meta"]
    assert "bank" in ing["table_meta"]
    print(f"✅ Ingested Tables: payments ({ing['table_meta']['payments']['total_rows']} rows), bank ({ing['table_meta']['bank']['total_rows']} rows)")

    # 6. Test Mapping Endpoint
    print("\n[Step 6] Testing /mapping endpoint...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/mapping")
    assert r.status_code == 200
    mapping = r.json()
    assert mapping["committed"] is not None
    print(f"✅ Committed Mapping: {mapping['committed']['left_key']} <-> {mapping['committed']['right_key']} (confidence: {mapping['confidence']})")

    # 7. Test Policy Endpoint
    print("\n[Step 7] Testing /policy endpoint...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/policy")
    assert r.status_code == 200
    pol = r.json()
    assert len(pol["components"]) > 0
    print(f"✅ Policy synthesized: {len(pol['components'])} components, baseline match rate: {pol['baseline_match_rate']}")

    # 8. Test Results Endpoint
    print("\n[Step 8] Testing /results endpoint...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/results")
    assert r.status_code == 200
    res = r.json()
    assert res["executed"] is True
    print(f"✅ Results: Match Rate = {res['match_rate']:.1%}, Matched Pairs = {len(res['matched'])}, Totals = {res['totals']}")

    # 9. Test Exception Queue Endpoint
    print("\n[Step 9] Testing /exceptions endpoint...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/exceptions")
    assert r.status_code == 200
    exc = r.json()
    assert len(exc["queue"]) > 0
    print(f"✅ Exception Queue: {len(exc['queue'])} items. Summary: {exc['summary']}")

    # 10. Test Exception Override Action
    print("\n[Step 10] Testing exception override action...")
    first_exc = exc["queue"][0]
    rid = first_exc["rid"]
    r = requests.post(f"{BASE_URL}/api/v2/sessions/{sid}/exceptions/{rid}/action", json={"action": "approve", "note": "Verified by manager"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    print(f"✅ Exception #{rid} override status: {r.json()['action']}")

    # 11. Test Cryptographic Audit Log
    print("\n[Step 11] Testing /audit endpoint & SHA-256 chain verification...")
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid}/audit")
    assert r.status_code == 200
    audit = r.json()
    assert audit["verified"] is True
    print(f"✅ Audit records logged: {audit['count']}, Chain Integrity: {audit['verified']}")

    # 12. Test Grounded Chat
    print("\n[Step 12] Testing /chat grounded Q&A endpoint...")
    r = requests.post(f"{BASE_URL}/api/v2/sessions/{sid}/chat", json={"message": "What is the match rate and total gross ledger volume?"})
    assert r.status_code == 200
    chat_res = r.json()
    print(f"✅ Chat response: {chat_res.get('response', '')[:140]}...")

    # 13. Test High-Volume 10,000+ Row Dataset (Excel .xlsx and CSV)
    print("\n[Step 13] Generating 10,000+ row dataset in Excel (.xlsx) and CSV format...")
    N = 10000
    dates = pd.date_range("2026-03-01", periods=30).astype(str).tolist()
    
    # Left ledger (payments)
    orders = [f"ORD_{i:06d}" for i in range(1, N + 1)]
    amounts = np.random.uniform(50.0, 5000.0, size=N).round(2)
    pay_dates = [dates[i % len(dates)] for i in range(N)]
    
    df_pay = pd.DataFrame({"order_id": orders, "amount": amounts, "date": pay_dates})
    
    # Right statement (bank) - 95% match, 5% fee variance or drift
    bank_utrs = orders.copy()
    bank_credits = amounts.copy()
    # Introduce fee deductions to 10%
    for i in range(0, N, 10):
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

    print(f"Generated payments (10,000 rows in Excel .xlsx) and bank (10,000 rows in CSV)")
    
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
    while time.time() - t0 < 60:
        r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid_large}/overview")
        st = r.json()["state"]
        if st in ("ARCHIVED", "RUN_FAILED"):
            break
        time.sleep(1)

    elapsed = time.time() - t0
    print(f"✅ 10,000+ Row Dataset Reconciled in {elapsed:.2f}s! Final state: {st}")

    # Verify results of 10k run
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid_large}/results")
    res_large = r.json()
    assert res_large["executed"] is True
    print(f"✅ 10k Run Stats: Match Rate = {res_large['match_rate']:.1%}, Matched = {len(res_large['matched'])}, Throughput = {res_large.get('throughput_rows_per_sec', 0):.0f} rows/sec")

    # Verify paginated ingestion
    r = requests.get(f"{BASE_URL}/api/v2/sessions/{sid_large}/ingestion?table=payments&page=1&page_size=50")
    ing_large = r.json()
    assert "payments" in ing_large["tables"]
    assert ing_large["tables"]["payments"]["total"] == 10000
    assert len(ing_large["tables"]["payments"]["items"]) == 50
    print(f"✅ Paginated Ingestion: Total {ing_large['tables']['payments']['total']} rows, Page size: 50, Total pages: {ing_large['tables']['payments']['total_pages']}")

    print("\n==================================================")
    print("🎉 ALL API v2 & LARGE DATASET TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_api_v2_full_suite()

```

### recon_agent/tests/test_constants.py

```python
from app.core.constants import REG


def test_registry_loads_and_fee_schedule_parsed():
    assert REG.version == "v0"
    assert REG["match_auto_threshold"] == 0.85
    assert "razorpay_test_mode" in REG.fee_schedules
    fs = REG.fee_schedules["razorpay_test_mode"]
    assert fs.params["rate"] == 0.02 and fs.gst_rate == 0.18

```

### recon_agent/tests/test_durability.py

```python
from app.core.audit import AuditLog


def test_restart_and_tamper(tmp_path):
    p = tmp_path / "s1.audit.jsonl"
    a = AuditLog(p)
    a.append({"event": "STATE_ENTERED", "state": "INGESTING"})
    a.append({"event": "tool_ok:x", "usd": 0.001})
    a.append({"event": "STATE_EXITED", "state": "INGESTING"})
    del a
    b = AuditLog(p)
    assert len(b.records) == 3 and b.verify()
    txt = p.read_text().splitlines()
    txt[1] = txt[1].replace("tool_ok:x", "tool_ok:EVIL")
    p.write_text("\n".join(txt) + "\n")
    assert not AuditLog(p).verify()

```

### recon_agent/tests/test_file_lifecycle_and_chat.py

```python
import io
import pytest
from fastapi.testclient import TestClient

from app.engine.chatbot import build_grounded_context, ReconChatSession
from app.pipeline import Pipeline
from app.server.main import app, SESSIONS, CHAT_SESSIONS


def test_chat_refuses_without_files():
    session = ReconChatSession("test_sid", pipe=None)
    res = session.chat("What was the total volume?")
    assert res["ok"] is False
    assert "No active files loaded" in res["error"]

    empty_pipe = Pipeline("empty_sid", auto_ack=True)
    session.set_pipe(empty_pipe)
    res2 = session.chat("Explain ORD_1")
    assert res2["ok"] is False
    assert "No active files loaded" in res2["error"]


def test_deleted_file_excluded_from_context(tmp_path):
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


def test_server_file_lifecycle_and_chat_endpoints():
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

```

### recon_agent/tests/test_halt_reentry_safety.py

```python
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

```

### recon_agent/tests/test_interactive_resume.py

```python
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

```

### recon_agent/tests/test_match_evidence.py

```python
import pytest

from app.core import llm_client
from app.core.constants import REG
from app.core.contracts import EvidencePiece
from app.engine import match


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("llm down")
    monkeypatch.setattr(llm_client, "json_chat", boom)


CFG = {"left_key": "order_id", "right_key": "utr", "left_amount": "amount",
       "right_amount": "credit", "left_date": "date", "right_date": "date",
       "tolerance": 0.01, "window_days": 3}
SCHED = REG.fee_schedules["razorpay_test_mode"]


def test_exact_raw_match_scores_full_amount():
    l = {"order_id": "A", "amount": 1000.0, "date": "2026-03-01"}
    r = {"utr": "A", "credit": 1000.0, "date": "2026-03-02"}
    v, comps, ev, sd = match.score_pair("t", l, r, CFG, SCHED, [])
    assert comps["amount"] == 1.0
    assert EvidencePiece.AMOUNT_WITHIN_TOL in ev and EvidencePiece.FEE_MODEL_MATCH not in ev
    assert v >= REG["match_auto_threshold"]


def test_fee_case_exclusive_and_detected():
    l = {"order_id": "B", "amount": 2000.0, "date": "2026-03-01"}
    r = {"utr": "B", "credit": 1952.80, "date": "2026-03-02"}
    v, comps, ev, sd = match.score_pair("t", l, r, CFG, SCHED, [])
    assert EvidencePiece.FEE_MODEL_MATCH in ev and EvidencePiece.AMOUNT_WITHIN_TOL not in ev
    assert comps["amount"] == 1.0

```

### recon_agent/tests/test_no_duplicate_exceptions.py

```python
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

```

### recon_agent/tests/test_overrides_and_discrepancies.py

```python
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

```

### recon_agent/tests/test_pipeline_evidence_flow.py

```python
import pytest

from app.core import llm_client


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("llm down")
    monkeypatch.setattr(llm_client, "json_chat", boom)


def test_end_to_end_classifications_and_evidence(tmp_path):
    from app.data.generator import generate
    generate(tmp_path)
    from app.pipeline import Pipeline
    p = Pipeline("test-session", auto_ack=True)
    final = p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"],
                  tmp_path / "ground_truth.jsonl")
    assert final is not None
    reasons = {i["rec"].reason.value for i in p.queue}
    assert {"refund_offset", "split", "temporal_drift", "duplicate"} <= reasons
    from app.core.contracts import EvidencePiece
    for item in p.queue:
        pieces = set(item["pieces"])
        assert not ({EvidencePiece.AMOUNT_WITHIN_TOL, EvidencePiece.FEE_MODEL_MATCH} <= pieces)
    assert final.precision_vs_truth == 1.0 and final.recall_vs_truth == 1.0

```
