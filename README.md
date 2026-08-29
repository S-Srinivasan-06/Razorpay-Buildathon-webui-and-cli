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

All 14 test suites covering state machine transitions, cryptographic ledger verification, fee calculations, file deletion context isolation, and ground-truth benchmarks execute in under 1 second in offline mode.#   R a z o r p a y - B u i l d a t h o n - w e b u i - a n d - c l i  
 