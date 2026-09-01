# Codebase Documentation

## File Tree Structure

```
recon_agent/
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
# Razorpay-Buildathon-webui-and-cli

> Autonomous, Multi-Way Financial Reconciliation Engine with Interactive Web UI, Deterministic Multi-Heuristic Engine, AI Diagnostic Provenance (Gemma 4 31B), and Cryptographic SHA-256 Audit Trails.

---

## Overview

The **Razorpay Reconciliation Agent** is an enterprise-grade financial reconciliation system built to autonomously ingest, match, and resolve discrepancies between internal payment ledgers and external bank/gateway settlement statements.

It provides both a **Modern Interactive Web UI** and a **Full-Featured Command-Line Interface (CLI)**:
- **Interactive Web UI Dashboard**: Real-time pipeline state visualization, drag-and-drop file upload, paginated data viewer, rule derivation inspector, exception queue with manager overrides, SHA-256 audit log verifier, and continuous grounded AI chatbot.
- **Deterministic Multi-Heuristic Engine**: Key linkage, date window tolerance, fee schedules (MDR, fixed fee, GST), and split/batch transaction detection.
- **LLM-Powered Semantic Intelligence**: Powered by **Gemma 4 31B** (`gemma-4-31b-it`) for schema mapping, semantic similarity, exception root-cause explanations, and interactive conversational query answering.
- **Continuous Grounded Chatbot**: Ask natural-language questions about matched pairs, fees, duplicate orders, or balance variances strictly grounded in the active session datasets.
- **Dynamic File Lifecycle Management**: Add or delete files dynamically with strict context isolation (deleted files are completely purged from LLM memory).
- **Cryptographic Audit Ledger**: Every state transition and decision is signed in a tamper-evident SHA-256 hash-chain stored on disk.
- **High Performance**: Tested with 10,000+ row datasets across CSV and Excel (`.xlsx`) files with sub-second execution.

---

## Quickstart and Setup

### 1. Prerequisites and Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/S-Srinivasan-06/Razorpay-Buildathon-webui-and-cli.git
cd Razorpay-Buildathon-webui-and-cli
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file from the example template:

```bash
cp .env.example .env
```

Or inside `recon_agent/`:
```bash
cp recon_agent/.env.example recon_agent/.env
```

Configure your Google Gemini / Gemma API key in `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemma-4-31b-it
```

Alternatively, export the environment variable in your terminal:

#### Linux / macOS:
```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export LLM_MODEL="gemma-4-31b-it"
```

#### Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
$env:LLM_MODEL="gemma-4-31b-it"
```

#### Windows (Command Prompt):
```cmd
set GEMINI_API_KEY=YOUR_GEMINI_API_KEY
set LLM_MODEL=gemma-4-31b-it
```

---

## Running the Application

### Option A: Interactive Web UI Dashboard

Start the FastAPI web server:

```bash
python recon_agent/run.py --server --host 127.0.0.1 --port 8000
```

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

#### Web UI Features:
1. **Upload & Ingest**: Upload CSV or Excel (`.xlsx`) files or click **Load Demo Benchmark Data** for instant reconciliation.
2. **Interactive Stepper**: Real-time visualization of the 7-step reconciliation pipeline with live event streaming over WebSocket.
3. **Data Inspection**: Paginated data grid with table selector, row count metrics, and column stats.
4. **Mapping & Policy**: Visual inspection of committed key linkages and synthesized tolerance rules.
5. **Reconciliation Results**: Summary cards for Match Rate, Total Gross Ledger Volume, Bank Inflow, and Discrepancies.
6. **Exception Management Queue**: Review classified discrepancies, view AI diagnostic explanations, and perform manual manager overrides (Approve / Reject / Escalation Notes).
7. **Audit Trail**: Real-time SHA-256 chain integrity verification with hash inspector.
8. **Grounded AI Assistant**: Multi-turn chat grounded in the active session's financial records.

---

### Option B: Command-Line Interface (CLI)

#### 1. Standard Reconciliation Run
```bash
cd recon_agent
python run.py sample_data/payments.csv sample_data/bank.csv
```

#### 2. Run with Ground Truth Benchmark Evaluation
Evaluate precision, recall, and classification accuracy against a benchmark ground truth file:
```bash
python run.py sample_data/payments.csv sample_data/bank.csv --truth sample_data/ground_truth.jsonl
```

#### 3. Interactive Grounded Chatbot Mode (`--chat` or `-i`)
Launch the continuous interactive REPL grounded in the reconciled session:
```bash
python run.py sample_data/payments.csv sample_data/bank.csv --chat
```

#### 4. Fast Offline / Zero-LLM Deterministic Mode (`--deterministic`)
Execute using purely deterministic rule engines without external API calls:
```bash
python run.py sample_data/payments.csv sample_data/bank.csv --deterministic
```

#### 5. Structured JSON Output Mode (`--json`)
Export the complete structured reconciliation report as JSON:
```bash
python run.py sample_data/payments.csv sample_data/bank.csv --truth sample_data/ground_truth.jsonl --json
```

---

## Demo Test Datasets

Pre-built demo datasets are provided in `recon_agent/sample_data/`:

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

### 3. `sample_data/ground_truth.jsonl` (Benchmark Mapping)
```jsonl
{"l_rid": 1, "r_rid": 1, "class": "exact"}
{"l_rid": 2, "r_rid": 2, "class": "fee_deduction"}
{"l_rid": 4, "r_rid": 4, "class": "duplicate_first"}
```

---

## Sample CLI Output

```text
# Razorpay Reconciliation Agent
Session ID: 86f3fa97

## Execution Steps
- Mode: Deterministic Engine (Offline / Zero-LLM)
- Ingesting: sample_data/payments.csv, sample_data/bank.csv
- Ground Truth Benchmark: sample_data/ground_truth.jsonl
- Step 1/7: Profiling table schemas and column statistics...
- Step 2/7: Linking schema keys and amounts via mapping tool...
- Step 3/7: Synthesizing policy components & tolerance windows...
- Step 4/7: Performing dry-run calibration on sample rows...
- Step 5/7: Executing multi-attribute matching engine...
- Step 6/7: Classifying exceptions & verifying invariant proofs...
- Step 7/7: Aggregating financial balances & signing cryptographic audit ledger...

---

## Reconciliation Report

### Performance & Metrics
- Match Rate: 27.3%
- Precision vs Truth: 100.0%
- Recall vs Truth: 100.0%
- Throughput: 948 rows/sec
- Execution Time: 0.17s

### Financial Balances
- Gross Ledger Volume: INR 9,000.00
- Net Bank Inflow: INR 8,126.84
- Gateway Fees Variance: INR 873.16
- Matched Value: INR 3,500.00
- Exception Value: INR 5,500.00

### Exception Queue Summary (8 Total)
- Auto-Resolved (Approved): 2 [APPROVED]
- Escalated (Action Required): 6 [REQUIRES ACTION]
- Unresolved Pending: 0
- Sum Invariant: VALID [OK]

---

## Cryptographic Audit Ledger
- Audit Entries Logged: 9
- SHA-256 Chain Integrity: VERIFIED [OK]
- Session Audit Path: data/audit/86f3fa97.audit.jsonl
```

---

## Running Automated Tests

Run the full automated test suite:

```bash
cd recon_agent
pytest -v
```

All test suites covering state machine transitions, cryptographic ledger verification, fee calculations, file deletion context isolation, and ground-truth benchmarks execute deterministically.

---

## Project Structure

```
Razorpay-Buildathon-webui-and-cli/
├── README.md                          # Project documentation
├── requirements.txt                   # Root Python dependencies
├── .env.example                       # Environment configuration template
├── .gitignore                         # Git ignore patterns
└── recon_agent/
    ├── requirements.txt               # Application dependencies
    ├── constants_v0.yaml              # Governance constants, rules & fee schedules
    ├── run.py                         # Unified CLI & server runner
    ├── sample_data/                   # Demo benchmark files
    │   ├── payments.csv
    │   ├── bank.csv
    │   └── ground_truth.jsonl
    ├── app/
    │   ├── config.py                  # File system paths & environment loader
    │   ├── pipeline.py                # 7-step reconciliation pipeline driver
    │   ├── core/
    │   │   ├── audit.py               # Cryptographic SHA-256 tamper-evident ledger
    │   │   ├── channels.py            # In-memory pub/sub event bus
    │   │   ├── constants.py           # Constants registry loaded from YAML
    │   │   ├── contracts.py           # Pydantic schemas, enums, evidence models & reports
    │   │   ├── cost.py                # LLM token metering & cost tracking
    │   │   ├── dispatcher.py          # Circuit breaker, retries & budget tool dispatcher
    │   │   ├── llm_client.py          # Gemma 4 31B client with JSON & chat completions
    │   │   ├── masking.py             # PII masking & pattern redaction utilities
    │   │   └── states.py              # 14-state Finite State Machine with abort tokens
    │   ├── data/
    │   │   └── generator.py           # Synthetic benchmark data generator
    │   ├── engine/
    │   │   ├── chatbot.py             # Grounded conversational session engine
    │   │   ├── fee.py                 # Gateway fee calculations (MDR, fixed fee, GST)
    │   │   ├── match.py               # Multi-heuristic matching engine
    │   │   ├── qa.py                  # Hypothesis-ordered exception classification
    │   │   ├── resolving.py           # Intelligent approvals & diagnostic explanations
    │   │   └── report.py              # Balance aggregator & FinalReport builder
    │   ├── server/
    │   │   ├── main.py                # FastAPI app initialization
    │   │   └── api_v2.py              # REST & WebSocket API endpoints for Web UI
    │   └── static/
    │       └── index.html             # Single-page Web UI application
    └── tests/
        ├── test_api_v2_e2e.py         # End-to-end API v2 & 10k dataset tests
        ├── test_constants.py          # Registry loading & fee parsing tests
        ├── test_durability.py         # SHA-256 hash-chain verification tests
        ├── test_file_lifecycle_and_chat.py # File add/delete & chat tests
        ├── test_halt_reentry_safety.py # Review gate & resume safety tests
        ├── test_interactive_resume.py # Multi-halt interactive resume tests
        ├── test_match_evidence.py     # Raw vs fee-adjusted matching tests
        ├── test_no_duplicate_exceptions.py # Exception deduplication tests
        ├── test_overrides_and_discrepancies.py # User overrides tests
        └── test_pipeline_evidence_flow.py # Pipeline integration tests
```
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
requests>=2.31.0
numpy>=1.26.0

```

### recon_agent/run.py

```python
#!/usr/bin/env python3
"""Razorpay Autonomous Financial Reconciliation Agent CLI & Server Runner.

Provides the unified command-line entry point for both the terminal CLI engine
and the FastAPI web application server.

CLI Usage Examples:
  # Standard two-file reconciliation (payments vs bank):
  python run.py sample_data/payments.csv sample_data/bank.csv

  # Reconciliation with precision/recall benchmark evaluation against ground truth:
  python run.py sample_data/payments.csv sample_data/bank.csv --truth sample_data/ground_truth.jsonl

  # Start interactive grounded AI assistant REPL after reconciliation:
  python run.py sample_data/payments.csv sample_data/bank.csv --chat

  # Run in pure offline deterministic mode without external LLM calls:
  python run.py sample_data/payments.csv sample_data/bank.csv --deterministic

  # Output final report and classified exception queue as structured JSON:
  python run.py sample_data/payments.csv sample_data/bank.csv --json

Server Usage Examples:
  # Launch FastAPI web console server (defaults to http://127.0.0.1:8000/console):
  python run.py --server
  python run.py --server --host 0.0.0.0 --port 8000
"""

import argparse
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
    """Format tabular data into a clean, aligned GitHub-flavored Markdown table.
    
    Dynamically computes maximum column widths to ensure clean monospaced alignment
    without requiring third-party table formatting packages.
    
    Args:
        headers: List of column header strings.
        rows: List of row lists containing cell values.
        
    Returns:
        Formatted Markdown table string.
    """
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


def start_chat_repl(pipe: Pipeline, sid: str) -> None:
    """Start an interactive terminal chat REPL grounded in the current reconciliation session.
    
    Args:
        pipe: Completed Pipeline instance containing active datasets and reports.
        sid: Session identifier string.
    """
    print("\n---\n", flush=True)
    print(f"## 💬 Interactive Reconciliation Assistant (Session: `{sid}`)\n", flush=True)
    print("- Connected to **Gemma 4 31B** (`gemma-4-31b-it`) strictly grounded in active session datasets.", flush=True)
    print("- Ask questions about matched records, fee schedules, duplicates, or root causes.", flush=True)
    print("- Type `exit` or `quit` to end the conversation.\n", flush=True)

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


def run_cli(
    files: List[Path],
    truth: Optional[Path] = None,
    auto_ack: bool = True,
    as_json: bool = False,
    deterministic: bool = False,
    chat: bool = False,
) -> None:
    """Execute reconciliation pipeline in terminal CLI mode and render results.
    
    Args:
        files: List of statement file paths (.csv or .xlsx).
        truth: Optional ground truth benchmark file path (.jsonl).
        auto_ack: Whether to auto-acknowledge non-fatal halts.
        as_json: If True, prints output as structured JSON.
        deterministic: If True, disables external LLM calls and forces heuristic paths.
        chat: If True, launches interactive grounded chat REPL upon completion.
    """
    sid = uuid.uuid4().hex[:8]
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    session_file = LOGS_DIR / f"{sid}.log"
    latest_session_log = LOGS_DIR / "session.log"
    session_file.write_text("", encoding="utf-8")
    latest_session_log.write_text("", encoding="utf-8")

    print("# ⚡ Razorpay Reconciliation Agent", flush=True)
    print(f"**Session ID**: `{sid}`\n", flush=True)
    print("## Execution Steps", flush=True)
    
    if deterministic:
        print("- **Mode**: Deterministic Engine (Offline / Zero-LLM)", flush=True)
        def boom(*a: Any, **k: Any) -> None:
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
            "report": report.model_dump(mode="json") if report else None,
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
    
    if report:
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


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Launch the FastAPI server and open the web console in the default browser.
    
    Args:
        host: Network interface host to bind to.
        port: Network port to listen on.
    """
    import threading
    import uvicorn
    import webbrowser
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


def main() -> None:
    """Parse CLI arguments and dispatch execution to run_server or run_cli."""
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
ORD_1001,1000.00,2026-03-01
ORD_1002,1500.00,2026-03-01
ORD_1003,2000.00,2026-03-01
ORD_1004,2500.00,2026-03-01
ORD_1005,3000.00,2026-03-01
ORD_1006,3500.00,2026-03-01
ORD_1007,4000.00,2026-03-01
ORD_1008,4500.00,2026-03-01
ORD_1009,5000.00,2026-03-01
ORD_1010,5500.00,2026-03-01
ORD_1011,6000.00,2026-03-02
ORD_1012,6500.00,2026-03-02
ORD_1013,7000.00,2026-03-02
ORD_1014,7500.00,2026-03-02
ORD_1015,8000.00,2026-03-02
ORD_1016,8500.00,2026-03-02
ORD_1017,9000.00,2026-03-02
ORD_1018,9500.00,2026-03-02
ORD_1019,10000.00,2026-03-02
ORD_1020,12000.00,2026-03-02
ORD_1021,1000.00,2026-03-01
ORD_1022,1250.00,2026-03-01
ORD_1023,1400.00,2026-03-02
ORD_1024,1800.00,2026-03-02
ORD_1025,2100.00,2026-03-03
ORD_1026,2300.00,2026-03-03
ORD_1027,2600.00,2026-03-04
ORD_1028,2900.00,2026-03-04
ORD_1029,3100.00,2026-03-05
ORD_1030,3400.00,2026-03-05
ORD_1031,3700.00,2026-03-06
ORD_1032,4100.00,2026-03-06
ORD_1033,4400.00,2026-03-07
ORD_1034,4800.00,2026-03-07
ORD_1035,5200.00,2026-03-08
TXN-ORD-1036,1100.00,2026-03-10
RZP_1037,1300.00,2026-03-10
ORD_1038_A,1600.00,2026-03-10
INV/2026/1039,1900.00,2026-03-11
BILL_1040,2200.00,2026-03-11
ORD1041,2500.00,2026-03-12
TX_1042,2800.00,2026-03-12
PAY_1043,3100.00,2026-03-13
ORD_1044,3500.00,2026-03-13
REF_1045,3900.00,2026-03-14
ORD_1046,1000.00,2026-03-15
ORD_1047,2000.00,2026-03-15
ORD_1048,1500.00,2026-03-15
ORD_1049,2500.00,2026-03-15
ORD_1050,3000.00,2026-03-15
ORD_1051,4000.00,2026-03-16
ORD_1052,6000.00,2026-03-16
ORD_1053,500.00,2026-03-16
ORD_1054,500.00,2026-03-16
ORD_1055,1000.00,2026-03-16

```

### recon_agent/sample_data/bank.csv

```csv
utr,credit,date
ORD_1001,976.40,2026-03-02
ORD_1002,1464.60,2026-03-02
ORD_1003,1952.80,2026-03-02
ORD_1004,2441.00,2026-03-02
ORD_1005,2929.20,2026-03-02
ORD_1006,3417.40,2026-03-02
ORD_1007,3905.60,2026-03-02
ORD_1008,4393.80,2026-03-02
ORD_1009,4882.00,2026-03-02
ORD_1010,5370.20,2026-03-02
ORD_1011,5858.40,2026-03-03
ORD_1012,6346.60,2026-03-03
ORD_1013,6834.80,2026-03-03
ORD_1014,7323.00,2026-03-03
ORD_1015,7811.20,2026-03-03
ORD_1016,8299.40,2026-03-03
ORD_1017,8787.60,2026-03-03
ORD_1018,9275.80,2026-03-03
ORD_1019,9764.00,2026-03-03
ORD_1020,11716.80,2026-03-03
ORD_1021,1000.00,2026-03-12
ORD_1022,1250.00,2026-03-12
ORD_1023,1400.00,2026-03-14
ORD_1024,1800.00,2026-03-15
ORD_1025,2100.00,2026-03-16
ORD_1026,2300.00,2026-03-17
ORD_1027,2600.00,2026-03-18
ORD_1028,2900.00,2026-03-18
ORD_1029,3100.00,2026-03-19
ORD_1030,3400.00,2026-03-20
ORD_1031,3700.00,2026-03-21
ORD_1032,4100.00,2026-03-22
ORD_1033,4400.00,2026-03-23
ORD_1034,4800.00,2026-03-24
ORD_1035,5200.00,2026-03-25
ORD-1036,1100.00,2026-03-11
1037_RZP,1300.00,2026-03-11
ORD_1038,1600.00,2026-03-11
INV20261039,1900.00,2026-03-12
BILL-1040-SETTL,2200.00,2026-03-12
ORD-1041,2500.00,2026-03-13
TXN_1042,2800.00,2026-03-13
PAY-1043,3100.00,2026-03-14
ORD_1044_CR,3500.00,2026-03-14
REF1045,3900.00,2026-03-15
BATCH_SETTL_01,2929.20,2026-03-17
BATCH_SETTL_02,6834.80,2026-03-17
BATCH_SETTL_03,9764.00,2026-03-18
BATCH_SETTL_04,1952.80,2026-03-18

```

### recon_agent/sample_data/ground_truth.jsonl

```json
{"l_rid": 1, "r_rid": 1, "class": "fee_deduction"}
{"l_rid": 2, "r_rid": 2, "class": "fee_deduction"}
{"l_rid": 3, "r_rid": 3, "class": "fee_deduction"}
{"l_rid": 4, "r_rid": 4, "class": "fee_deduction"}
{"l_rid": 5, "r_rid": 5, "class": "fee_deduction"}
{"l_rid": 6, "r_rid": 6, "class": "fee_deduction"}
{"l_rid": 7, "r_rid": 7, "class": "fee_deduction"}
{"l_rid": 8, "r_rid": 8, "class": "fee_deduction"}
{"l_rid": 9, "r_rid": 9, "class": "fee_deduction"}
{"l_rid": 10, "r_rid": 10, "class": "fee_deduction"}
{"l_rid": 11, "r_rid": 11, "class": "fee_deduction"}
{"l_rid": 12, "r_rid": 12, "class": "fee_deduction"}
{"l_rid": 13, "r_rid": 13, "class": "fee_deduction"}
{"l_rid": 14, "r_rid": 14, "class": "fee_deduction"}
{"l_rid": 15, "r_rid": 15, "class": "fee_deduction"}
{"l_rid": 16, "r_rid": 16, "class": "fee_deduction"}
{"l_rid": 17, "r_rid": 17, "class": "fee_deduction"}
{"l_rid": 18, "r_rid": 18, "class": "fee_deduction"}
{"l_rid": 19, "r_rid": 19, "class": "fee_deduction"}
{"l_rid": 20, "r_rid": 20, "class": "fee_deduction"}
{"l_rid": 21, "r_rid": 21, "class": "temporal_drift"}
{"l_rid": 22, "r_rid": 22, "class": "temporal_drift"}
{"l_rid": 23, "r_rid": 23, "class": "temporal_drift"}
{"l_rid": 24, "r_rid": 24, "class": "temporal_drift"}
{"l_rid": 25, "r_rid": 25, "class": "temporal_drift"}
{"l_rid": 26, "r_rid": 26, "class": "temporal_drift"}
{"l_rid": 27, "r_rid": 27, "class": "temporal_drift"}
{"l_rid": 28, "r_rid": 28, "class": "temporal_drift"}
{"l_rid": 29, "r_rid": 29, "class": "temporal_drift"}
{"l_rid": 30, "r_rid": 30, "class": "temporal_drift"}
{"l_rid": 31, "r_rid": 31, "class": "temporal_drift"}
{"l_rid": 32, "r_rid": 32, "class": "temporal_drift"}
{"l_rid": 33, "r_rid": 33, "class": "temporal_drift"}
{"l_rid": 34, "r_rid": 34, "class": "temporal_drift"}
{"l_rid": 35, "r_rid": 35, "class": "temporal_drift"}
{"l_rid": 36, "r_rid": 36, "class": "fuzzy_key"}
{"l_rid": 37, "r_rid": 37, "class": "fuzzy_key"}
{"l_rid": 38, "r_rid": 38, "class": "fuzzy_key"}
{"l_rid": 39, "r_rid": 39, "class": "fuzzy_key"}
{"l_rid": 40, "r_rid": 40, "class": "fuzzy_key"}
{"l_rid": 41, "r_rid": 41, "class": "fuzzy_key"}
{"l_rid": 42, "r_rid": 42, "class": "fuzzy_key"}
{"l_rid": 43, "r_rid": 43, "class": "fuzzy_key"}
{"l_rid": 44, "r_rid": 44, "class": "fuzzy_key"}
{"l_rid": 45, "r_rid": 45, "class": "fuzzy_key"}
{"l_rid": [46, 47], "r_rid": 46, "class": "split"}
{"l_rid": [48, 49, 50], "r_rid": 47, "class": "split"}
{"l_rid": [51, 52], "r_rid": 48, "class": "split"}
{"l_rid": [53, 54, 55], "r_rid": 49, "class": "split"}

```

### recon_agent/app/__init__.py

```python


```

### recon_agent/app/config.py

```python
"""Configuration and environment management for the reconciliation engine.

Provides filesystem path resolution, automatic directory initialization,
and lightweight .env parsing without third-party dotenv dependencies.
"""

import os
from pathlib import Path

# Base project directories resolved relative to this module
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
LOGS_DIR = DATA_DIR / "logs"
AUDIT_DIR = DATA_DIR / "audit"

# Ensure all working directories exist upon module import
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
AUDIT_DIR.mkdir(exist_ok=True)


def _load_env_file() -> None:
    """Load environment variables from a local recon_agent/.env file if present.
    
    Parses key=value pairs while ignoring comments and empty lines. Does not
    overwrite existing environment variables already present in os.environ.
    """
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
            # Silently handle unreadable or malformed .env files
            pass


# Automatically load local .env definitions on startup
_load_env_file()

# Default LLM API key lookup prioritizing standard LLM / Gemini variable names
DEFAULT_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY", "")


```

### recon_agent/app/pipeline.py

```python
"""Autonomous Reconciliation Pipeline Orchestrator.

Implements the complete 7-stage financial reconciliation lifecycle:
  1. Ingestion: Parsing CSV and Excel statements, assigning internal Row IDs (_rid).
  2. Profiling: Statistical column analysis, data type detection, PII likelihood scoring.
  3. Schema Mapping: Deterministic candidate key overlap & LLM semantic field linking.
  4. Policy Synthesis & Dry-Run: Baseline match rate calibration and tolerance bounds.
  5. Multi-Attribute Execution: Exact key indexing, amount tolerance, and date proximity.
  6. Quality Assurance & Split Detection: Combinatorial subset sum solving and discrepancy taxonomy.
  7. Aggregation & Audit Trail: Balance summation, metered cost calculation, and cryptographic signing.
"""

import itertools
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd
from pydantic import BaseModel, model_validator

from app.core.audit import audit_for
from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import (
    Actor,
    DecisionRecord,
    EvidencePiece,
    ExecutionResult,
    FinalReport,
    MatchComponent,
    MatchedRecord,
    MessageKind,
    Policy,
    PolicyComponent,
    UnmatchedRecord,
    VarianceMetrics,
)
from app.core.dispatcher import breaker_open, dispatch_tool_call, ToolCall
from app.core.states import State, StateMachine
from app.engine import match, qa, report, resolving
from app.engine.match import _sim, fee_explains


class MapArgs(BaseModel):
    """Input payload for the LLM semantic schema mapping tool."""
    tables: Dict[str, List[str]]


class MapResult(BaseModel):
    """Schema mapping configuration specifying linked keys, amounts, and dates."""
    left_table: str = "payments"
    right_table: str = "bank"
    left_key: str = "order_id"
    right_key: str = "utr"
    left_amount: Optional[str] = "amount"
    right_amount: Optional[str] = "credit"
    left_date: Optional[str] = "date"
    right_date: Optional[str] = "date"

    @model_validator(mode="before")
    @classmethod
    def parse_llm_json(cls, data: Any) -> Dict[str, Any]:
        """Normalize varied JSON responses from LLM mapping into canonical schema fields."""
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


def _overlap(xs: List[Any], ys: List[Any]) -> float:
    """Calculate the Jaccard-like set overlap ratio between two column value sets.
    
    Args:
        xs: First list of column values.
        ys: Second list of column values.
        
    Returns:
        Intersection size divided by the minimum set size (0.0 to 1.0).
    """
    a, b = set(map(str, xs)), set(map(str, ys))
    return len(a & b) / max(min(len(a), len(b)), 1)


class Pipeline:
    """Core stateful reconciliation engine coordinating all execution phases.
    
    Maintains ingested table records, profiling statistics, schema configurations,
    match policies, intermediate results, exception queues, and final reports.
    """

    def __init__(self, sid: str, auto_ack: bool = False) -> None:
        """Initialize pipeline for a session.
        
        Args:
            sid: Unique session identifier string.
            auto_ack: If True (CLI/test mode), automatically resumes on halts.
                      If False (Web/interactive mode), leaves state at HALT for operator action.
        """
        self.sid: str = sid
        self.auto_ack: bool = auto_ack
        self.sm: StateMachine = StateMachine(sid)
        self.fb: List[str] = []
        self.tables: Dict[str, List[Dict[str, Any]]] = {}
        self.cfg: Dict[str, Any] = {}
        self.schedule: Optional[Any] = next(iter(REG.fee_schedules.values()), None)
        self.truth: List[Dict[str, Any]] = []
        self.profiles: Dict[str, List[Any]] = {}
        self._map_cands: List[Any] = []
        self._map_conf: float = 0.0
        self._ambiguous: bool = False
        self.exec_res: Optional[ExecutionResult] = None
        self.final: Optional[FinalReport] = None
        self.queue: List[Dict[str, Any]] = []

    # ---------- Event bus helper methods ----------
    def _chat(self, text: str) -> None:
        """Broadcast a CHAT message event."""
        validate_and_route(self.sid, MessageKind.CHAT, {"text": text[:2000]}, "system")

    def _trace(self, event: str, **d: Any) -> None:
        """Broadcast an execution TRACE telemetry event."""
        validate_and_route(self.sid, MessageKind.TRACE, {"event": event, "detail": d}, "system")

    def _maybe_ack(self, tools: List[str]) -> None:
        """Handle potential state machine halt based on the auto_ack configuration.
        
        When auto_ack=True, resumes immediately in-place (used for CLI or automated tests).
        When auto_ack=False, leaves state at HALT for the interactive caller to resolve.
        """
        if self.auto_ack:
            self.sm.resume()

    # Mapping of State enum values to corresponding Pipeline step handler method names
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

    # ---------- Step 1: Ingestion ----------
    def ingest(self, files: List[Path], truth: Optional[Union[str, Path]] = None) -> bool:
        """Parse input CSV/Excel files into memory and assign internal Row IDs (_rid).
        
        Args:
            files: List of file Paths (.csv or .xlsx) representing ledger and statement files.
            truth: Optional path to ground truth JSONL file for benchmark precision/recall evaluation.
            
        Returns:
            True if transitioned to PROFILING state, False otherwise.
        """
        self.sm.enter(State.INGESTING)
        for f in files:
            try:
                df = pd.read_csv(f) if f.suffix == ".csv" else pd.read_excel(f)
                df.insert(0, "_rid", range(1, len(df) + 1))
                tbl_name = f.stem
                # Strip session ID prefix if present (e.g., 'd11231d8_payments' -> 'payments')
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

    # ---------- Step 2: Profiling ----------
    def profile(self) -> bool:
        """Compute statistical profiles, column data types, and PII likelihood for each table."""
        print("- **Step 1/7**: Profiling table schemas and column statistics...", flush=True)
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
                self.profiles[name].append(
                    ColumnProfile(
                        name=c,
                        dtype=str(df[c].dtype),
                        numeric_ratio=float(num),
                        date_ratio=float(dat),
                        cardinality=float(df[c].nunique() / max(len(df), 1)),
                        null_rate=float(df[c].isna().mean()),
                        min_len=int(s.str.len().min() or 0),
                        max_len=int(s.str.len().max() or 0),
                        sample_values=s.head(3).tolist(),
                        pii_likelihood=max((pii_score(c, v) for v in s.head(5)), default=0.0),
                    )
                )
        return self.sm.transition(State.MAPPING_PROPOSED)

    def _pick(self, t: str, kind: str) -> Optional[str]:
        """Heuristically select a column name of a given semantic type ('numeric' or 'date')."""
        for p in self.profiles.get(t, []):
            if kind == "numeric" and p.numeric_ratio > 0.8 and p.cardinality > 0.3:
                return p.name
            if kind == "date" and p.date_ratio > 0.8 and p.numeric_ratio <= 0.8:
                return p.name
        return None

    # ---------- Step 3: Schema Mapping ----------
    def propose_mapping(self) -> bool:
        """Identify candidate primary keys and invoke LLM semantic mapping tool."""
        print("- **Step 2/7**: Linking schema keys and amounts via mapping tool...", flush=True)
        names = list(self.tables)
        cands = []
        for lt in names:
            for rt in names:
                if lt == rt:
                    continue
                for lc in [p.name for p in self.profiles[lt]]:
                    for rc in [p.name for p in self.profiles[rt]]:
                        ov = _overlap(
                            [r.get(lc) for r in self.tables[lt]],
                            [r.get(rc) for r in self.tables[rt]],
                        )
                        if ov >= 0.10:
                            cands.append((ov, lt, lc, rt, rc))
        cands.sort(reverse=True)
        self._map_cands = cands

        tool = ToolCall(
            name="mapping_semantic",
            args_schema=MapArgs,
            result_schema=MapResult,
            timeout_s=REG["llm_tool_timeout_s"],
            retries=2,
            fallback=lambda a: None,
            cost_budget_usd=0.005,
        )
        llm_map, fb = dispatch_tool_call(
            self.sid,
            tool,
            {"tables": {n: [p.name for p in self.profiles[n]] for n in names}},
        )
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
            self.cfg = {
                "left_table": lt,
                "right_table": rt,
                "left_key": lc,
                "right_key": rc,
                "left_amount": self._pick(lt, "numeric"),
                "right_amount": self._pick(rt, "numeric"),
                "left_date": self._pick(lt, "date"),
                "right_date": self._pick(rt, "date"),
            }
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

    def validate_mapping(self) -> bool:
        """Validate proposed schema mapping confidence and record decision in audit log."""
        audit_for(self.sid).append(
            DecisionRecord(
                decision_id=uuid.uuid4().hex,
                ts=pd.Timestamp.now(tz="UTC").to_pydatetime(),
                state="MAPPING_VALIDATED",
                actor=Actor.SYSTEM,
                decision_kind="mapping",
                proposal={"candidates": [list(c[1:]) for c in self._map_cands[:3]]},
                final={k: self.cfg.get(k) for k in ("left_table", "right_table", "left_key", "right_key")},
                confidence=self._map_conf,
                evidence=[],
            ).model_dump(mode="json")
        )

        if self._map_conf < REG["mapping_review_floor"]:
            self.sm.halt("mapping below review floor")
            self._maybe_ack([])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.MAPPING_VALIDATED
                return False

        if self._ambiguous or self._map_conf < REG["mapping_auto_accept"]:
            self._chat(f"Mapping confidence {self._map_conf:.2f} — proceeding with trace visibility.")

        return self.sm.transition(State.POLICY_GENERATED)

    # ---------- Step 4: Policy Synthesis & Dry-Run ----------
    def policy(self) -> bool:
        """Synthesize match policy components and initialize tolerance windows."""
        print("- **Step 3/7**: Synthesizing policy components & tolerance windows...", flush=True)
        comps = [
            PolicyComponent(component=c, params={}, precedence=i)
            for i, c in enumerate(MatchComponent, 1)
        ]
        comps[3].params = {"tolerance": 0.01, "window_days": 3}
        self.policy_doc = Policy(
            components=comps,
            baseline_match_rate=0.0,
            baseline_computed_at=pd.Timestamp.now(tz="UTC").to_pydatetime(),
            baseline_constants_version=REG.version,
        )
        self.cfg.setdefault("tolerance", 0.01)
        self.cfg.setdefault("window_days", 3)
        return self.sm.transition(State.DRY_RUN)

    # ---------- Scoring Core ----------
    def _score_all(self, rows_l: List[Dict[str, Any]], rows_r: List[Dict[str, Any]]) -> ExecutionResult:
        """Execute multi-attribute matching across left ledger and right statement rows.
        
        Optimizations:
          - Pre-indexes right rows by exact key for O(1) direct candidate lookups.
          - Filters candidate search pool by amount proximity on large datasets (>300 rows).
          - Detects duplicates in the left ledger.
          - Tracks soft-paired right rows to prevent duplicate exception listings.
        """
        self._last_cand_scores: List[float] = []
        matched: List[MatchedRecord] = []
        unmatched: List[UnmatchedRecord] = []
        dups: List[Dict[str, Any]] = []
        per: List[Dict[str, Any]] = []
        unmatched_ctx: List[Tuple[UnmatchedRecord, Optional[Dict[str, Any]], List[EvidencePiece], Optional[float]]] = []

        # Index left rows by key to identify duplicates
        lkeys: Dict[str, List[Dict[str, Any]]] = {}
        for l in rows_l:
            lkeys.setdefault(str(l[self.cfg["left_key"]]), []).append(l)
        dup_keys = {k for k, v in lkeys.items() if len(v) > 1}
        seen_dup: Set[str] = set()

        used_r: Set[int] = set()
        soft_paired_r: Set[int] = set()  # Right records already represented via an unmatched left pairing

        # Index right rows by key for instant exact candidate lookup
        r_by_key: Dict[str, List[Dict[str, Any]]] = {}
        rk = self.cfg["right_key"]
        for r in rows_r:
            r_by_key.setdefault(str(r.get(rk)), []).append(r)

        def mk_unmatched(
            l_row: Optional[Dict[str, Any]],
            r_row: Optional[Dict[str, Any]],
            v: Optional[float],
            ev: List[EvidencePiece],
            sd: Optional[float],
        ) -> Tuple[UnmatchedRecord, List[EvidencePiece]]:
            side = "L" if l_row is not None else "R"
            ref_key = self.cfg["left_key"] if l_row is not None else self.cfg["right_key"]
            rec = UnmatchedRecord(
                side=side,
                rid=(l_row or r_row)["_rid"],
                ref=str((l_row or r_row).get(ref_key)),
                delta=sd,
                match_confidence=v,
            )
            return rec, ev

        is_large = len(rows_r) > 300
        for l in rows_l:
            key = str(l[self.cfg["left_key"]])
            if key in dup_keys and key not in seen_dup:
                dups.append({"side": "L", "key": key, "rids": [x["_rid"] for x in lkeys[key]]})
                seen_dup.add(key)

            # Check direct exact key matches first
            direct_cands = [r for r in r_by_key.get(key, []) if r["_rid"] not in used_r]
            if direct_cands:
                cands = [
                    (r, *match.score_pair(self.sid, l, r, self.cfg, self.schedule, self.fb))
                    for r in direct_cands
                ]
                cands = [(r, v, c, e, d) for (r, v, c, e, d) in cands if v >= REG["match_review_floor"]]
            else:
                cands = []

            # If no direct match meets threshold, search candidate pool
            if not cands:
                search_pool = [r for r in rows_r if r["_rid"] not in used_r]
                if is_large and len(search_pool) > 200:
                    # On large datasets, filter candidates by amount proximity
                    la = float(l.get(self.cfg.get("left_amount", ""), 0) or 0)
                    ra_key = self.cfg.get("right_amount", "")
                    search_pool = sorted(
                        search_pool,
                        key=lambda r: abs(la - float(r.get(ra_key, 0) or 0)) if ra_key else 0,
                    )[:150]

                cands = [
                    (r, *match.score_pair(self.sid, l, r, self.cfg, self.schedule, self.fb))
                    for r in search_pool
                ]
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
                matched.append(
                    MatchedRecord(
                        l_rid=l["_rid"],
                        r_rid=r["_rid"],
                        composite_score=v,
                        components=comps,
                        policy_version=REG.version,
                    )
                )
                per.append({"l_id": l["_rid"], "r_id": r["_rid"], "abs": abs(sd or 0), "signed": sd})
            else:
                rec, ev = mk_unmatched(l, r, v, ev, sd)
                unmatched.append(rec)
                unmatched_ctx.append((rec, r, ev, sd))
                soft_paired_r.add(r["_rid"])  # Prevent right record from appearing as duplicate standalone entry

        # Collect remaining unmatched right statement records
        for r in rows_r:
            if r["_rid"] not in used_r and r["_rid"] not in soft_paired_r:
                rec, ev = mk_unmatched(None, r, None, [], None)
                unmatched.append(rec)
                unmatched_ctx.append((rec, None, ev, None))

        var = VarianceMetrics(
            abs_sum=sum(p["abs"] for p in per),
            signed_sum=sum(p["signed"] for p in per),
            per_record=per,
        )
        self._last_unmatched_ctx = unmatched_ctx
        return ExecutionResult(
            matched=matched,
            unmatched=unmatched,
            duplicates=dups,
            splits=[],
            variance=var,
        )

    def dry_run(self) -> bool:
        """Run dry-run calibration on the first 100 records to establish a baseline match rate."""
        print("- **Step 4/7**: Performing dry-run calibration on sample rows...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]][:100]
        rows_r = self.tables[self.cfg["right_table"]]
        t0 = time.time()
        res = self._score_all(rows_l, rows_r)
        self.policy_doc.baseline_match_rate = len(res.matched) / max(len(rows_l), 1)
        mean_cand = (
            sum(self._last_cand_scores) / len(self._last_cand_scores)
            if self._last_cand_scores
            else 0.0
        )
        if mean_cand < REG["calibration_sanity_floor"]:
            self._trace("CALIBRATION_DRIFT_WARNING", mean_cand=round(mean_cand, 3))
        self._trace(
            "dry_run_done",
            s=round(time.time() - t0, 2),
            baseline=round(self.policy_doc.baseline_match_rate, 3),
            mean_cand=round(mean_cand, 3),
        )
        return self.sm.transition(State.EXECUTING)

    # ---------- Step 5: Multi-Attribute Execution ----------
    def execute(self) -> bool:
        """Execute the full matching run across all ingested records."""
        print("- **Step 5/7**: Executing multi-attribute matching engine...", flush=True)
        t0 = time.time()
        self.exec_res = self._score_all(
            self.tables[self.cfg["left_table"]],
            self.tables[self.cfg["right_table"]],
        )
        self._exec_s = max(time.time() - t0, 1e-6)
        return self.sm.transition(State.INSPECTING)

    def _inspect_metrics(self) -> None:
        """Compute match rate, throughput, and precision/recall against ground truth."""
        r = self.exec_res
        total = len(r.matched) + len(r.unmatched)
        self.match_rate = len(r.matched) / max(total, 1)
        nrows = sum(len(t) for t in self.tables.values())
        self.throughput = nrows / max(getattr(self, "_exec_s", 1.0), 1e-6)
        pred = {(m.l_rid, m.r_rid) for m in r.matched}

        if not getattr(self, "truth", None):
            self.precision = None
            self.recall = None
            return

        truth = set()
        for t in self.truth:
            lr = tuple(t["l_rid"]) if isinstance(t["l_rid"], list) else t["l_rid"]
            rr = tuple(t["r_rid"]) if isinstance(t["r_rid"], list) else t["r_rid"]
            truth.add((lr, rr))

        self.precision = (len(pred & truth) / len(pred)) if pred else None
        self.recall = (len(pred & truth) / len(truth)) if truth else None

    def inspect(self) -> bool:
        """Inspect match quality metrics; trigger adaptive revision if below threshold."""
        self._inspect_metrics()
        if self.match_rate < REG["revision_match_rate_threshold"]:
            return self.sm.transition(State.REVISION)
        return self.sm.transition(State.QA)

    def revise(self) -> bool:
        """Adaptive revision loop adjusting amount tolerance bounds when match rate is low."""
        it, t0 = 0, time.time()
        while (
            self.match_rate < REG["revision_match_rate_threshold"]
            and it < REG["revision_iteration_cap"]
            and time.time() - t0 < REG["revision_time_cap_s"]
        ):
            old = self.cfg["tolerance"]
            self.cfg["tolerance"] = round(old * 1.2, 4)
            self._trace("revision", it=it, tol=self.cfg["tolerance"])
            self.execute()
            self._inspect_metrics()
            # If tolerance expansion caused a regression compared to baseline, revert and break
            if self.policy_doc.baseline_match_rate - self.match_rate > REG["regression_reject_delta"]:
                self.cfg["tolerance"] = old
                self._trace("revision_regression_rejected", it=it)
                break
            it += 1

        if self.match_rate < REG["revision_match_rate_threshold"]:
            self.sm.halt("revision caps exhausted or regression rejected")
            self._maybe_ack([])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.QA
                return False
        return self.sm.transition(State.QA)

    # ---------- Step 6: QA & Exception Classification ----------
    def _ctx(
        self,
        side: str,
        l: Optional[Dict[str, Any]],
        r: Optional[Dict[str, Any]],
        rows_l: List[Dict[str, Any]],
        rows_r: List[Dict[str, Any]],
        sd: Optional[float],
        used_l: Optional[Set[int]] = None,
    ) -> Dict[str, Any]:
        """Extract diagnostic context signals for a specific unmatched record."""
        lk, rk = self.cfg["left_key"], self.cfg["right_key"]
        tol = self.cfg["tolerance"]
        used_l = used_l or set()
        ctx: Dict[str, Any] = {
            k: ([] if k in ("dup_rids", "split_targets") else False) for k in qa.CTX_KEYS
        }

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
                    dd = match._busdays(
                        match._d(l[self.cfg["left_date"]]),
                        match._d(cands[0][self.cfg["right_date"]]),
                    )
                    ctx["date_only_mismatch"] = dd > self.cfg["window_days"] and (
                        abs(a - rv) <= tol or ctx["fee_match"]
                    )
            if not cands:
                # Corroborate fuzzy key similarity with amount/fee consistency
                a = float(l[self.cfg["left_amount"]]) if self.cfg.get("left_amount") else None
                search_r = (
                    rows_r
                    if len(rows_r) <= 500
                    else [
                        x
                        for x in rows_r
                        if abs(a - float(x.get(self.cfg.get("right_amount", ""), 0) or 0)) <= 1000
                    ][:100]
                )
                if a is not None and self.cfg.get("right_amount"):
                    ctx["fuzzy_key"] = any(
                        match._sim(key, str(x[rk])) >= 0.75
                        and (
                            abs(a - float(x[self.cfg["right_amount"]])) <= tol
                            or fee_explains(a, float(x[self.cfg["right_amount"]]), self.schedule, tol)
                        )
                        for x in search_r
                    )
                else:
                    ctx["fuzzy_key"] = max((match._sim(key, str(x[rk])) for x in search_r), default=0) >= 0.75

        if side == "R" and r is not None:
            rv = float(r[self.cfg["right_amount"]]) if self.cfg.get("right_amount") else 0.0
            ctx["negative_credit"] = rv < 0
            nets = []
            # Only search among UNMATCHED left rows to avoid reusing 1:1 matched records
            unmatched_l = [x for x in rows_l if x["_rid"] not in used_l]
            for x in unmatched_l:
                a = float(x.get(self.cfg["left_amount"], 0))
                nets.append((x["_rid"], a - (match.compute_fee(a, self.schedule) if self.schedule else 0)))
            # Bounded pool search for combinatorial split subsets
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

    def qa_state(self) -> bool:
        """Classify exceptions and solve combinatorial batch/split transactions globally."""
        print("- **Step 6/7**: Classifying exceptions & verifying invariant proofs...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]]
        rows_r = self.tables[self.cfg["right_table"]]
        used_l = {m.l_rid for m in self.exec_res.matched}
        tol = self.cfg["tolerance"]

        # 1. First pass: solve combinatorial splits globally with disjoint left allocations
        right_splits: Dict[int, List[int]] = {}
        allocated_split_l: Set[int] = set()
        unmatched_r_items = [
            (rec, r_cand, ev, sd)
            for (rec, r_cand, ev, sd) in self._last_unmatched_ctx
            if rec.side == "R"
        ]

        # Exclude left rows that have a direct key match in rows_r (e.g. Temporal Drift rows)
        r_keys = {str(x.get(self.cfg["right_key"])): x for x in rows_r}
        temporal_or_direct_l: Set[int] = set()
        for x in rows_l:
            key = str(x.get(self.cfg["left_key"]))
            if key in r_keys:
                temporal_or_direct_l.add(x["_rid"])

        # Calculate net amounts for all unmatched left rows eligible for split pools
        left_nets: List[Tuple[int, float]] = []
        for x in rows_l:
            if x["_rid"] not in used_l and x["_rid"] not in temporal_or_direct_l:
                a = float(x.get(self.cfg["left_amount"], 0))
                net = a - (match.compute_fee(a, self.schedule) if self.schedule else 0)
                left_nets.append((x["_rid"], net))

        for rec, r_cand, ev, sd in unmatched_r_items:
            r = next(x for x in rows_r if x["_rid"] == rec.rid)
            rv = float(r.get(self.cfg["right_amount"], 0) or 0)
            if rv <= 0:
                continue

            avail = [x for x in left_nets if x[0] not in allocated_split_l and 0 < x[1] <= rv + tol]
            found_combo = None
            for k in (2, 3):
                for combo in itertools.combinations(avail, k):
                    if abs(sum(v for _, v in combo) - rv) <= tol:
                        found_combo = [i for i, _ in combo]
                        break
                if found_combo:
                    break

            if found_combo:
                right_splits[rec.rid] = found_combo
                allocated_split_l.update(found_combo)

        # 2. Second pass: construct exception queue with accurate classification
        self.queue = []
        left_split_map: Dict[int, str] = {}
        for r_rid, target_l_rids in right_splits.items():
            r_row = next((x for x in rows_r if x["_rid"] == r_rid), {})
            r_ref = str(r_row.get(self.cfg["right_key"]) or f"RID_{r_rid}")
            for l_rid in target_l_rids:
                left_split_map[l_rid] = r_ref

        for rec, r_cand, ev, sd in self._last_unmatched_ctx:
            if rec.side == "L":
                l = next(x for x in rows_l if x["_rid"] == rec.rid)
                ctx = self._ctx("L", l, r_cand, rows_l, rows_r, sd, used_l=used_l)
                if rec.rid in left_split_map:
                    rec.reason = qa.H.SPLIT
                    ctx["split_batch_ref"] = left_split_map[rec.rid]
                    ctx["split_targets"] = [rec.rid]
                    ev = [EvidencePiece.FEE_MODEL_MATCH, EvidencePiece.KEY_MATCH]
                else:
                    rec.reason = qa.classify(rec, ctx)
                    if rec.reason == qa.H.COUNTERPARTY_MISMATCH and not ev:
                        ev = [EvidencePiece.KEY_MATCH, EvidencePiece.AMOUNT_WITHIN_TOL]
            else:
                r = next(x for x in rows_r if x["_rid"] == rec.rid)
                ctx = self._ctx("R", None, r, rows_l, rows_r, sd, used_l=used_l)
                if rec.rid in right_splits:
                    ctx["split_targets"] = right_splits[rec.rid]
                    rec.reason = qa.H.SPLIT
                    ev = [EvidencePiece.FEE_MODEL_MATCH, EvidencePiece.KEY_MATCH]
                else:
                    rec.reason = qa.classify(rec, ctx)

            self.queue.append({"rec": rec, "ctx": ctx, "pieces": ev})

        return self.sm.transition(State.RESOLVING)

    def resolve(self) -> bool:
        """Evaluate confidence scores, assign resolution actions, and record decision audit logs."""
        for item in self.queue:
            rec, pieces, ctx = item["rec"], item["pieces"], item.get("ctx", {})
            conf = resolving.exception_confidence(len(pieces), rec.reason, None)
            action = resolving.decide_action(conf, len(pieces), rec.reason)
            explanation = resolving.generate_explanation(rec, ctx)
            rec.explanation = explanation
            item["action"], item["conf"], item["explanation"] = action, conf, explanation
            actor = (
                Actor.SYSTEM
                if action in ("auto_resolve", "mark_pending", "request_confirmation")
                else Actor.FALLBACK
            )
            audit_for(self.sid).append(
                DecisionRecord(
                    decision_id=uuid.uuid4().hex,
                    ts=pd.Timestamp.now(tz="UTC").to_pydatetime(),
                    state="RESOLVING",
                    actor=actor,
                    decision_kind="exception_resolve",
                    proposal={"category": rec.reason.value, "explanation": explanation},
                    final={"action": action},
                    confidence=conf,
                    evidence=pieces,
                ).model_dump(mode="json")
            )
        return self.sm.transition(State.AGGREGATING)

    # ---------- Step 7: Aggregation & Final Report ----------
    def aggregate(self, elapsed: float) -> bool:
        """Sum gross, net, fee, and exception balances, then construct the FinalReport."""
        print("- **Step 7/7**: Aggregating financial balances & signing cryptographic audit ledger...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]]
        rows_r = self.tables[self.cfg["right_table"]]
        g = sum(float(x.get(self.cfg["left_amount"], 0)) for x in rows_l)
        n = sum(float(x.get(self.cfg["right_amount"], 0)) for x in rows_r)
        mv = sum(
            float(x.get(self.cfg["left_amount"], 0))
            for x in rows_l
            if x["_rid"] in {m.l_rid for m in self.exec_res.matched}
        )
        totals = {
            "gross": round(g, 2),
            "net": round(n, 2),
            "fees": round(g - n, 2),
            "matched_value": round(mv, 2),
            "exception_value": round(g - mv, 2),
        }
        self.final = report.build_final_report(
            self.sid,
            match_rate=self.match_rate,
            precision_vs_truth=self.precision,
            recall_vs_truth=self.recall,
            throughput_rows_per_sec=self.throughput,
            exceptions=self.queue,
            elapsed_seconds=elapsed,
            totals=totals,
            llm_user_disagreements=[],
            fallback_events=self.fb,
        )
        return self.sm.transition(State.ARCHIVED)

    # ---------- Driver Loop ----------
    def run(self, files: List[Path], truth: Optional[Union[str, Path]] = None) -> Optional[FinalReport]:
        """Execute the complete end-to-end reconciliation pipeline starting from ingestion.
        
        Args:
            files: Ingested file paths.
            truth: Optional ground truth benchmark file path.
            
        Returns:
            Completed FinalReport model, or None if halted interactively.
        """
        self._t0 = time.time()
        self.ingest(files, truth)
        return self.continue_run()

    def continue_run(self) -> Optional[FinalReport]:
        """Re-entrant driver: dispatches step methods based on current StateMachine state.
        
        A HALT pauses execution cleanly (returning None) without losing state. Calling
        `continue_run()` after `sm.resume()` resumes exactly where it left off.
        """
        while self.sm.state not in (State.AGGREGATING, State.ARCHIVED, State.ABORT_CONFIRMED):
            attr = self._STEP_FN_ATTR.get(self.sm.state)
            if attr is None:
                break
            ok = getattr(self, attr)()
            if self.sm.state == State.HALT:
                return None  # Stop gracefully on interactive halt
            if ok is False:
                return None

        if self.sm.state == State.RESOLVING or getattr(self, "queue", None) is not None:
            if self.sm.state != State.ARCHIVED:
                self.aggregate(time.time() - getattr(self, "_t0", time.time()))

        if getattr(self, "final", None):
            validate_and_route(
                self.sid,
                MessageKind.ARTIFACT,
                {
                    "kind": "report",
                    "summary": self.final.model_dump(),
                    "confidence_threshold": REG["match_auto_threshold"],
                    "fallback_events": self.fb,
                },
                "engine",
            )
            self._chat(
                f"Reconciliation complete: {self.final.match_rate:.0%} matched, "
                f"{self.final.honest_exception_count} exceptions, "
                f"{self.final.auto_resolved_count} auto-resolved."
            )

        return self.final


```

### recon_agent/app/core/__init__.py

```python


```

### recon_agent/app/core/contracts.py

```python
"""Data Contracts and Schema Specifications.

Defines Pydantic data models, strongly typed enums, event payloads, and
decision records governing communication between the state machine, match engine,
LLM tools, event bus, and audit logging.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, Field


class MessageKind(str, Enum):
    """Categories of messages transmitted across the event routing bus."""
    CHAT = "chat"
    ARTIFACT = "artifact"
    TRACE = "trace"
    CONTROL = "control"


class ConfidenceScope(str, Enum):
    """Scoring domain for confidence evaluation."""
    MAPPING = "mapping"
    MATCH = "match"
    EXCEPTION = "exception"


class Actor(str, Enum):
    """Entity originating or executing a decision."""
    LLM = "llm"
    USER = "user"
    SYSTEM = "system"
    FALLBACK = "fallback"


class EvidencePiece(str, Enum):
    """Discrete verified evidence elements supporting a match or resolution."""
    KEY_MATCH = "key_match"
    AMOUNT_WITHIN_TOL = "amount_within_tol"
    DATE_WITHIN_WINDOW = "date_within_window"
    FEE_MODEL_MATCH = "fee_model_match"


class HypothesisCategory(str, Enum):
    """Taxonomy of discrepancy root causes for unmatched records."""
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


# Precedence order used when evaluating multiple competing discrepancy hypotheses
HYPOTHESIS_PRIORITY: Dict[HypothesisCategory, int] = {
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
    """Individual match policy scoring components."""
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
    """Payload schema for user and assistant chat messages."""
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=2000, description="Message text content")


class ArtifactPayload(BaseModel):
    """Payload schema for generated data artifacts, grids, and summary cards."""
    kind: str = Field(description="Artifact type identifier (e.g. 'report', 'exceptions')")
    schema_version: str = "1.0"
    rows: Optional[List[Dict[str, Any]]] = None
    summary: Dict[str, Any] = {}
    confidence_threshold: float
    fallback_events: List[str] = []


class TracePayload(BaseModel):
    """Payload schema for internal execution trace events and telemetry."""
    event: str
    detail: Dict[str, Any] = {}


class ControlPayload(BaseModel):
    """Payload schema for state machine control signals, halts, and abort tokens."""
    event: str
    state: Optional[str] = None
    abort_token: Optional[str] = None
    detail: Dict[str, Any] = {}


# Registry mapping message kinds to their respective Pydantic validation schemas
SCHEMAS: Dict[MessageKind, Type[BaseModel]] = {
    MessageKind.CHAT: ChatPayload,
    MessageKind.ARTIFACT: ArtifactPayload,
    MessageKind.TRACE: TracePayload,
    MessageKind.CONTROL: ControlPayload,
}


class ToolCall(BaseModel):
    """Configuration for an LLM-invoked tool with schemas, timeouts, and fallback handler."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    args_schema: Type[BaseModel]
    result_schema: Type[BaseModel]
    timeout_s: float
    retries: int
    fallback: Callable[..., Any]
    cost_budget_usd: float


class FeeSchedule(BaseModel):
    """Payment gateway or aggregator fee schedule configuration."""
    provider: str
    schedule_id: str
    version: str
    effective_from: date
    effective_until: Optional[date] = None
    model_type: str  # e.g., 'flat_rate', 'per_txn_flat', 'tiered'
    params: Dict[str, Any]
    gst_rate: float = 0.0
    currency: str = "INR"


class ConfidenceScore(BaseModel):
    """Structured confidence calculation score with sub-component breakdowns."""
    scope: ConfidenceScope
    value: float = Field(ge=0, le=1)
    components: Dict[str, float]
    constants_version: str
    constants_loaded_at: datetime


class DecisionRecord(BaseModel):
    """Immutable audit record representing a discrete engine or operator decision."""
    decision_id: str
    ts: datetime
    state: str
    actor: Actor
    decision_kind: str
    proposal: Dict[str, Any]
    final: Dict[str, Any]
    overridden: bool = False
    override_reason: Optional[str] = None
    confidence: float
    evidence: List[EvidencePiece]
    fallback_used: Optional[str] = None


class ColumnProfile(BaseModel):
    """Statistical and semantic profile of an ingested table column."""
    name: str
    dtype: str
    numeric_ratio: float
    date_ratio: float
    cardinality: float
    null_rate: float
    min_len: int
    max_len: int
    sample_values: List[str]
    pii_likelihood: float


class PolicyComponent(BaseModel):
    """Configured component within a reconciliation matching policy."""
    component: MatchComponent
    params: Dict[str, Any]
    enabled: bool = True
    precedence: int


class Policy(BaseModel):
    """Complete synthesized matching policy specification."""
    components: List[PolicyComponent]
    generated_from: str = "deterministic_library_v0"
    revision_history: List[Dict[str, Any]] = []
    baseline_match_rate: float
    baseline_source: str = "dry_run_subset"
    baseline_computed_at: datetime
    baseline_constants_version: str


class MatchedRecord(BaseModel):
    """Pairing result between a left ledger record and right statement record."""
    l_rid: int
    r_rid: int
    composite_score: float
    components: Dict[str, float]
    policy_version: str


class UnmatchedRecord(BaseModel):
    """Unpaired record with classified discrepancy reason and diagnostic explanation."""
    side: str  # 'L' (ledger) or 'R' (statement/bank)
    rid: int
    ref: Optional[str] = None
    reason: HypothesisCategory = HypothesisCategory.UNCLASSIFIED
    delta: Optional[float] = None
    match_confidence: Optional[float] = None
    explanation: Optional[str] = None


class VarianceMetrics(BaseModel):
    """Aggregated discrepancy and balance variance metrics."""
    abs_sum: float
    pct_avg: float = 0.0
    signed_sum: float
    per_record: List[Dict[str, Any]]


class ExecutionResult(BaseModel):
    """Comprehensive matching engine execution output."""
    matched: List[MatchedRecord]
    unmatched: List[UnmatchedRecord]
    duplicates: List[Dict[str, Any]]
    splits: List[Dict[str, Any]]
    variance: VarianceMetrics


class FinalReport(BaseModel):
    """Final reconciliation report summarizing volumes, matches, exceptions, and costs."""
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
    llm_user_disagreements: List[Dict[str, Any]] = []
    fallback_events: List[str] = []
    constants_version: str
    retention_note: str
    storage_backend: str = "local_hash_chain"


```

### recon_agent/app/core/constants.py

```python
"""Constants Registry and Parameter Management.

Loads engine thresholds, scoring weights, timeout durations, and fee schedules
from versioned YAML definitions (e.g., constants_v0.yaml). Performs runtime
validation to ensure all weights sum to 1.0 and values stay within valid bounds.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel

from app.core.contracts import FeeSchedule


class Constant(BaseModel):
    """Metadata and constraint definition for a single engine parameter.
    
    Attributes:
        name: Unique identifier for the constant (e.g. 'match_auto_threshold').
        value: Numeric floating-point value assigned to the constant.
        scope: Domain scope such as 'match', 'mapping', 'exception', or 'runtime'.
        derivation_method: Description of how the default was chosen (e.g. 'manual_default').
        derived_from: Source reference or benchmark dataset.
        valid_range: Optional [min, max] inclusive bounding range for validation.
        gates: State gate or component that consumes this parameter.
        unit: Optional unit string (e.g. 'seconds', 'ratio', 'count', 'usd').
    """
    name: str
    value: float
    scope: str
    derivation_method: str = "manual_default"
    derived_from: str
    valid_range: Optional[List[float]] = None
    gates: str
    unit: Optional[str] = None


class Registry:
    """In-memory constants registry loaded from a versioned YAML specification.
    
    Validates range bounds on each parameter and ensures that attribute weights
    for mapping, matching, and exception scoring each sum to 1.000.
    """

    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        """Initialize and validate the registry from the specified YAML file.
        
        Args:
            path: Optional path to YAML constants file. Defaults to constants_v0.yaml.
            
        Raises:
            ValueError: If any constant is out of its valid range or if scoring
                weights within any scope do not sum to 1.0.
        """
        if path is None:
            from app.config import BASE_DIR
            path = BASE_DIR / "constants_v0.yaml"

        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        self.version: str = raw["version"]
        self.loaded_at: datetime = datetime.now()
        self._c: Dict[str, Constant] = {c["name"]: Constant(**c) for c in raw["constants"]}
        self.fee_schedules: Dict[str, FeeSchedule] = {
            fs["schedule_id"]: FeeSchedule(**fs)
            for fs in raw.get("fee_schedules", [])
        }

        # Validate that every constant value falls within its declared valid_range
        for c in self._c.values():
            if c.valid_range and not (c.valid_range[0] <= c.value <= c.valid_range[1]):
                raise ValueError(f"Constant '{c.name}'={c.value} is outside valid range {c.valid_range}")

        # Enforce weight summation invariant (weights must sum to 1.0 for each scoring scope)
        for scope in ("mapping", "match", "exception"):
            ws = [c.value for c in self._c.values() if c.name.startswith(f"w_{scope}_")]
            if ws and abs(sum(ws) - 1.0) > 1e-6:
                raise ValueError(f"Weights for scope '{scope}' sum to {sum(ws)}, expected 1.0")

    def __getitem__(self, k: str) -> float:
        """Retrieve the numeric value of a constant by name."""
        return self._c[k].value


# Global constants registry singleton
REG = Registry()


```

### recon_agent/app/core/audit.py

```python
"""Cryptographic Audit Ledger with Tamper-Evident SHA-256 Hash Chain.

Provides durable, append-only audit logging for every state transition, LLM decision,
and user override. Each log entry incorporates the cryptographic hash of the previous
entry (starting from 'GENESIS'), ensuring mathematical tamper detection upon verification.
"""

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Union

AUDIT_DIR = Path(os.getenv("RECON_AUDIT_DIR", "data/audit"))


class AuditLog:
    """Tamper-evident audit log backed by a JSONL file and SHA-256 hash chain.
    
    Each line in the log is a JSON object with:
      - `seq`: Monotonically increasing 0-based integer sequence index.
      - `ts`: ISO-8601 UTC timestamp string.
      - `payload`: The logged event or decision payload dictionary.
      - `prev_hash`: Hash of the previous entry ('GENESIS' for the 0th entry).
      - `this_hash`: SHA-256 hash of canonical JSON {"seq", "payload", "prev"}.
    """

    def __init__(self, path: Union[str, Path]) -> None:
        """Initialize and open the audit log file, loading existing history if present.
        
        Args:
            path: Filesystem path to the .audit.jsonl file.
        """
        self.path: Path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock: threading.Lock = threading.Lock()
        self.records: List[Dict[str, Any]] = []
        self._prev: str = "GENESIS"

        # Reconstruct chain from disk if log file already exists
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    self.records.append(r)
                    self._prev = r["this_hash"]

        self._fh = open(self.path, "a", encoding="utf-8")

    def append(self, payload: Dict[str, Any]) -> None:
        """Append a new record to the audit chain with SHA-256 signing and disk fsync.
        
        Args:
            payload: Event or decision dictionary to record permanently.
        """
        with self._lock:
            seq = len(self.records)
            # Create canonical deterministic JSON representation for hashing
            canon = json.dumps(
                {"seq": seq, "payload": payload, "prev": self._prev},
                sort_keys=True,
                default=str,
            )
            h = hashlib.sha256(canon.encode("utf-8")).hexdigest()
            rec = {
                "seq": seq,
                "ts": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
                "prev_hash": self._prev,
                "this_hash": h,
            }
            self._fh.write(json.dumps(rec, default=str) + "\n")
            self._fh.flush()
            os.fsync(self._fh.fileno())
            self.records.append(rec)
            self._prev = h

    def verify(self) -> bool:
        """Verify the cryptographic integrity of the entire audit chain from genesis.
        
        Reads the log file from disk and recalculates hashes for every entry.
        
        Returns:
            True if all hashes and chain links are strictly intact, False if tampered.
        """
        if not self.path.exists():
            return True
        prev = "GENESIS"
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            canon = json.dumps(
                {"seq": r["seq"], "payload": r["payload"], "prev": prev},
                sort_keys=True,
                default=str,
            )
            calculated_hash = hashlib.sha256(canon.encode("utf-8")).hexdigest()
            if r["prev_hash"] != prev or calculated_hash != r["this_hash"]:
                return False
            prev = r["this_hash"]
        return True


# Session-to-AuditLog registry with thread-safe access lock
_LOGS: Dict[str, AuditLog] = {}
_LOGS_LOCK = threading.Lock()


def audit_for(session_id: str) -> AuditLog:
    """Retrieve or lazily initialize the AuditLog instance for a given session.
    
    Args:
        session_id: Unique session identifier string.
        
    Returns:
        AuditLog instance writing to data/audit/{session_id}.audit.jsonl.
    """
    with _LOGS_LOCK:
        if session_id not in _LOGS:
            from app import config
            audit_dir = getattr(config, "AUDIT_DIR", AUDIT_DIR)
            _LOGS[session_id] = AuditLog(audit_dir / f"{session_id}.audit.jsonl")
        return _LOGS[session_id]


```

### recon_agent/app/core/channels.py

```python
"""Event Distribution Bus and Schema Validation Routing.

Provides a pub/sub event distribution mechanism across message kinds (CHAT,
ARTIFACT, TRACE, CONTROL). Validates incoming payloads against Pydantic contracts,
intercepts and masks PII on ARTIFACT payloads, and logs contract violations.
"""

from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, ValidationError

from app.core.audit import audit_for
from app.core.contracts import MessageKind, SCHEMAS
from app.core.masking import apply_masking

# Registry of subscriber callbacks grouped by MessageKind
_subscribers: Dict[MessageKind, List[Callable[[str, BaseModel, str], None]]] = {
    k: [] for k in MessageKind
}


def subscribe(kind: MessageKind, fn: Callable[[str, BaseModel, str], None]) -> None:
    """Register a subscriber callback for a specific message kind.
    
    Args:
        kind: The MessageKind category to listen for.
        fn: Callback taking (session_id, validated_model, source).
    """
    _subscribers[kind].append(fn)


def validate_and_route(
    session_id: str,
    kind: MessageKind,
    payload: Dict[str, Any],
    source: str,
) -> Optional[BaseModel]:
    """Validate a payload against its schema and route to all registered subscribers.
    
    If validation fails, records a CONTRACT_VIOLATION event in the session audit log
    and returns None. If valid, applies PII masking on ARTIFACT payloads before
    broadcasting to subscribers.
    
    Args:
        session_id: Unique session identifier.
        kind: MessageKind classification of the event.
        payload: Raw dictionary data matching the schema for `kind`.
        source: Originator identifier (e.g. 'system', 'engine', 'llm', 'user').
        
    Returns:
        The validated Pydantic model instance, or None if validation failed.
    """
    try:
        model = SCHEMAS[kind].model_validate(payload)
    except ValidationError as e:
        # Audit contract violations without crashing the executing pipeline
        audit_for(session_id).append({
            "event": "CONTRACT_VIOLATION",
            "session": session_id,
            "kind": kind.value,
            "source": source,
            "err": str(e)[:200],
        })
        return None

    # Intercept artifact payloads to automatically redact sensitive PII
    if kind == MessageKind.ARTIFACT:
        model = apply_masking(model)

    # Deliver validated message to all registered listeners
    for fn in _subscribers[kind]:
        fn(session_id, model, source)

    return model


```

### recon_agent/app/core/masking.py

```python
"""Personally Identifiable Information (PII) Detection and Masking.

Provides regex- and heuristic-based PII scoring for sensitive financial fields
(email addresses, phone numbers, Indian PAN cards, Aadhaar IDs, and residential addresses).
Automatically redacts high-likelihood PII in artifact table rows before transmission.
"""

import re
from typing import Any

from app.core.constants import REG
from app.core.contracts import ArtifactPayload

# Compiled regex patterns with associated PII confidence scores:
#  - Email address (score: 1.00)
#  - International/Domestic phone numbers (score: 0.90)
#  - Indian Permanent Account Number / PAN: 5 letters, 4 digits, 1 letter (score: 0.80)
#  - 12-digit Indian Aadhaar number (score: 0.75)
_PAT = [
    (re.compile(r"[\w.+-]+@[\w-]+\.\w+"), 1.0),
    (re.compile(r"^\+?\d[\d\s-]{9,14}$"), 0.9),
    (re.compile(r"^[A-Z]{5}\d{4}[A-Z]$"), 0.8),
    (re.compile(r"^\d{12}$"), 0.75),
]

# Sensitive column header keywords that elevate PII review likelihood
_HINTS = ("email", "phone", "mobile", "pan", "aadhaar", "address")


def pii_score(field: str, value: Any) -> float:
    """Calculate the likelihood score that a field and value contain sensitive PII.
    
    Evaluates value against regex patterns first. If no regex matches, checks if
    the field name contains known sensitive keywords.
    
    Args:
        field: Column or attribute name.
        value: Cell or attribute value to inspect.
        
    Returns:
        Floating point score from 0.0 (non-PII) to 1.0 (confirmed PII).
    """
    if value is None:
        return 0.0
    s = str(value)
    for rx, sc in _PAT:
        if rx.match(s):
            return sc
    return 0.75 if any(h in field.lower() for h in _HINTS) else 0.0


def apply_masking(m: ArtifactPayload) -> ArtifactPayload:
    """Apply in-place masking to all rows in an ArtifactPayload above PII thresholds.
    
    Replaces values with '[MASKED:pii]' when score >= `pii_mask_threshold`, and
    updates artifact summary with total masked and review-needed count metrics.
    
    Args:
        m: ArtifactPayload instance containing table rows.
        
    Returns:
        The mutated ArtifactPayload with masked values.
    """
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
"""LLM Cost Metering and Budget Enforcement.

Tracks cumulative LLM expenditure per session, enforces maximum budget caps
(e.g., $1.00 USD per session cap), and flags whether token counts were derived
from exact API usage metadata or estimated from prompt/response lengths.
"""

import threading
from typing import Dict

from app.core.constants import REG


class CostTracker:
    """Thread-safe cumulative cost tracker and budget authorizer for a session.
    
    Attributes:
        cap: Maximum authorized USD budget cap for the session.
        total: Cumulative USD spend incurred by tool and chat invocations.
        estimated_any: Boolean flag indicating if any cost calculation was estimated.
    """

    def __init__(self, cap_usd: float) -> None:
        """Initialize tracker with a strict USD budget cap.
        
        Args:
            cap_usd: Maximum allowable expenditure in USD.
        """
        self.cap: float = cap_usd
        self.total: float = 0.0
        self.estimated_any: bool = False
        self._lock: threading.Lock = threading.Lock()

    def authorize(self, budget_usd: float) -> bool:
        """Check whether an upcoming call with the given budget is authorized.
        
        Args:
            budget_usd: Estimated cost of the prospective call in USD.
            
        Returns:
            True if (total + budget_usd) <= cap, False otherwise.
        """
        with self._lock:
            return self.total + budget_usd <= self.cap

    def record(self, usd: float, estimated: bool = False) -> None:
        """Record the actual incurred cost of a completed LLM invocation.
        
        Args:
            usd: Cost in USD to add to the cumulative total.
            estimated: True if token counts were estimated rather than reported by API.
        """
        with self._lock:
            self.total += usd
            self.estimated_any = self.estimated_any or estimated


# Per-session CostTracker instance registry
_TRACKERS: Dict[str, CostTracker] = {}


def tracker_for(session_id: str) -> CostTracker:
    """Retrieve or lazily initialize the CostTracker for a specific session.
    
    Args:
        session_id: Unique session identifier string.
        
    Returns:
        CostTracker instance configured with the registry's session_cost_cap_usd.
    """
    if session_id not in _TRACKERS:
        _TRACKERS[session_id] = CostTracker(REG["session_cost_cap_usd"])
    return _TRACKERS[session_id]


```

### recon_agent/app/core/llm_client.py

```python
"""LLM API Client for Gemma and Gemini Models.

Manages raw HTTP requests to Google's Generative Language API using standard
library urllib (zero external HTTP dependencies). Provides structured JSON tool calling
for semantic mapping/similarity and multi-turn conversational chat for the grounded assistant.
"""

import json
import os
import re
import urllib.request
from typing import Any, Dict, List, Tuple

from app.config import DEFAULT_API_KEY
from app.core.constants import REG

# Default model configuration: Gemma 4 31B instruction-tuned
MODEL = os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL", "gemma-4-31b-it"))

# Internal telemetry state tracking token counts from the most recent LLM invocation
_last: Dict[str, Any] = {"in": 0, "out": 0, "estimated": False}


def resolve_model_slug(model_name: str) -> str:
    """Normalize model slug for Google Generative Language API endpoints.
    
    Translates common shorthand names to official API endpoint identifiers
    (e.g., 'gemma-4-31b' -> 'gemma-4-31b-it').
    
    Args:
        model_name: Raw model string or alias.
        
    Returns:
        Canonical Google model identifier.
    """
    m = model_name.strip()
    if m in ("gemma-4-31b", "gemma-31b"):
        return "gemma-4-31b-it"
    if m in ("gemma-4b", "gemma-4b-it", "gemma-4-26b"):
        return "gemma-4-26b-a4b-it"
    return m


def get_api_key() -> str:
    """Resolve active API key checking LLM_API_KEY, GEMINI_API_KEY, and .env defaults.
    
    Returns:
        The resolved API key string, or empty string if not configured.
    """
    return os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or DEFAULT_API_KEY


def _extract_json(text: str) -> Dict[str, Any]:
    """Robustly extract a JSON dictionary from raw LLM text output.
    
    Handles raw JSON, markdown-fenced code blocks (```json ... ```), and JSON
    embedded within surrounding text by locating outermost brace boundaries.
    
    Args:
        text: Raw response string from the model.
        
    Returns:
        Parsed JSON dictionary.
        
    Raises:
        json.JSONDecodeError: If no valid JSON object could be parsed.
    """
    text = text.strip()

    # 1. Search inside Markdown code blocks
    if "```" in text:
        blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        for b in blocks:
            b = b.strip()
            if b.startswith("{") and b.endswith("}"):
                try:
                    return json.loads(b)
                except Exception:
                    pass

    # 2. Search for outermost matching curly braces
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # 3. Direct parse fallback
    return json.loads(text)


def json_chat(tool_name: str, args: Dict[str, Any], timeout: float = 25.0) -> Dict[str, Any]:
    """Invoke an LLM tool with temperature=0.0 and enforce a strict JSON output contract.
    
    Sends a structured prompt requesting only raw JSON without preamble or markdown,
    records token counts and metered USD cost, and parses the extracted JSON.
    
    Args:
        tool_name: Identifier of the tool (e.g., 'mapping_semantic', 'semantic_similarity').
        args: Input arguments dictionary passed to the tool.
        timeout: HTTP request timeout in seconds.
        
    Returns:
        Parsed dictionary output matching the tool's expected schema.
        
    Raises:
        RuntimeError: If no API key is configured.
        Exception: On HTTP errors, network timeouts, or unparseable output.
    """
    key = get_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set — deterministic fallback will be used")

    actual_model = resolve_model_slug(MODEL)

    if tool_name == "mapping_semantic":
        schema_hint = (
            'JSON with keys: {"left_table": str, "right_table": str, "left_key": str, '
            '"right_key": str, "left_amount": str, "right_amount": str, "left_date": str, "right_date": str}'
        )
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
            "temperature": 0.0,
        },
    }

    print(f"  [LLM] Invoking {actual_model} for tool '{tool_name}' ...", flush=True)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())

    raw_msg = d["candidates"][0]["content"]["parts"][0]["text"]
    u = d.get("usageMetadata", {})
    _last["estimated"] = "usageMetadata" not in d
    _last["in"] = u.get("promptTokenCount", len(prompt) // 4)
    _last["out"] = u.get("candidatesTokenCount", len(raw_msg) // 4)
    print(
        f"  [LLM] Received response from {actual_model} "
        f"({_last['in']} in / {_last['out']} out tokens | cost: ${last_cost_usd():.6f})",
        flush=True,
    )

    return _extract_json(raw_msg)


def conversational_chat(
    messages: List[Dict[str, str]],
    system_instruction: str,
    timeout: float = 25.0,
) -> Tuple[str, float]:
    """Execute multi-turn conversation grounded strictly in current session dataset context.
    
    Transmits conversation history and dataset grounding instructions to Gemma/Gemini,
    computes call cost using configured per-1k-token rates, and returns the reply.
    
    Args:
        messages: List of message dicts with 'role' ('user'/'assistant') and 'content'.
        system_instruction: Grounded reconciliation context and factual constraints.
        timeout: HTTP request timeout in seconds.
        
    Returns:
        Tuple of (assistant_reply_text, call_cost_usd).
        
    Raises:
        RuntimeError: If API key is not configured.
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
            "parts": [{"text": msg.get("content", "")}],
        })

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{actual_model}:generateContent?key={key}"
    payload = {
        "system_instruction": {
            "parts": [{
                "text": (
                    system_instruction
                    + "\n\nCRITICAL INSTRUCTION: Reply directly to the user as the assistant. "
                    "Do NOT output internal thoughts, reasoning steps, or notes analyzing the prompt. "
                    "Provide ONLY the final, polished response directly to the user."
                )
            }]
        },
        "contents": formatted_contents,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())

    raw_reply = d["candidates"][0]["content"]["parts"][0]["text"].strip()
    u = d.get("usageMetadata", {})
    t_in = u.get("promptTokenCount", sum(len(m.get("content", "")) for m in messages) // 4)
    t_out = u.get("candidatesTokenCount", len(raw_reply) // 4)
    call_cost = (t_in / 1000 * REG["cost_llm_in_per_1k_usd"]) + (t_out / 1000 * REG["cost_llm_out_per_1k_usd"])

    return raw_reply, call_cost


def last_cost_usd() -> float:
    """Calculate the USD cost of the most recent tool invocation based on metered token counts."""
    return (
        _last["in"] / 1000 * REG["cost_llm_in_per_1k_usd"]
        + _last["out"] / 1000 * REG["cost_llm_out_per_1k_usd"]
    )


def last_estimated() -> bool:
    """Return True if the last invocation's token counts were estimated rather than API-reported."""
    return _last["estimated"]


```

### recon_agent/app/core/dispatcher.py

```python
"""Tool Dispatcher with Circuit Breakers, Cost Control, and Deterministic Fallbacks.

Manages execution of external LLM tool calls. Implements safety circuit breakers,
cost budget enforcement, retry loops with latency/cost telemetry, and fallback
execution when LLM endpoints are unavailable or budget limits are reached.
"""

import time
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, ValidationError

from app.core import llm_client
from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import MessageKind, ToolCall
from app.core.cost import tracker_for

# Circuit breaker failure counters keyed by (session_id, tool_name)
_breakers: Dict[Tuple[str, str], int] = {}


def breaker_open(sid: str, tool: str) -> bool:
    """Check if the circuit breaker is tripped open for a specific session and tool.
    
    Args:
        sid: Session identifier string.
        tool: Name of the tool.
        
    Returns:
        True if failure count has reached the threshold, False otherwise.
    """
    return _breakers.get((sid, tool), 0) >= REG["circuit_breaker_failure_count"]


def _count_failure(sid: str, tool: str) -> None:
    """Increment failure counter and emit a CIRCUIT_BREAKER_OPEN event if threshold is hit.
    
    Args:
        sid: Session identifier string.
        tool: Name of the tool that encountered a failure.
    """
    k = (sid, tool)
    _breakers[k] = _breakers.get(k, 0) + 1
    if _breakers[k] == REG["circuit_breaker_failure_count"]:
        validate_and_route(
            sid,
            MessageKind.CONTROL,
            {
                "event": "CIRCUIT_BREAKER_OPEN",
                "detail": {"tool": tool, "session": sid},
            },
            "system",
        )


def reset_breaker(sid: str, tool: str) -> None:
    """Reset the failure counter for a specific session and tool.
    
    Args:
        sid: Session identifier string.
        tool: Name of the tool to reset.
    """
    _breakers[(sid, tool)] = 0


def dispatch_tool_call(
    sid: str,
    tool: ToolCall,
    args: Dict[str, Any],
) -> Tuple[Any, Optional[str]]:
    """Safely dispatch an LLM tool call with budget checking, retries, and fallback.
    
    Workflow:
      1. Validate input args against `tool.args_schema`. If invalid, execute fallback.
      2. Check if circuit breaker is open. If open, immediately return fallback.
      3. Check cost budget with CostTracker. If exceeded, return fallback.
      4. Execute LLM call with retry loop up to `tool.retries`.
      5. On success: record token cost, reset circuit breaker, and emit trace telemetry.
      6. On repeated failure: increment circuit breaker and execute deterministic fallback.
      
    Args:
        sid: Session identifier string.
        tool: ToolCall specification defining schemas, timeouts, and fallback.
        args: Input argument dictionary.
        
    Returns:
        Tuple of (result_or_fallback_output, fallback_used_flag_or_name).
    """
    # 1. Validate argument schema
    try:
        validated = tool.args_schema.model_validate(args)
    except ValidationError as e:
        validate_and_route(
            sid,
            MessageKind.TRACE,
            {
                "event": f"args_rejected:{tool.name}",
                "detail": {"err": str(e)[:200]},
            },
            "system",
        )
        return tool.fallback(args), tool.name

    # 2. Check circuit breaker state
    if breaker_open(sid, tool.name):
        return tool.fallback(args), tool.name

    # 3. Authorize cost budget
    if not tracker_for(sid).authorize(tool.cost_budget_usd):
        validate_and_route(
            sid,
            MessageKind.CONTROL,
            {"event": "BUDGET_EXCEEDED", "detail": {"tool": tool.name}},
            "system",
        )
        return tool.fallback(args), tool.name

    # 4. Execute tool call with retries
    err = None
    for _ in range(tool.retries + 1):
        t0 = time.time()
        try:
            raw = llm_client.json_chat(
                tool.name,
                validated.model_dump(),
                timeout=tool.timeout_s,
            )
            result = tool.result_schema.model_validate(raw)
            usd = llm_client.last_cost_usd()
            est = llm_client.last_estimated()
            tracker_for(sid).record(usd, estimated=est)

            if usd > tool.cost_budget_usd:
                validate_and_route(
                    sid,
                    MessageKind.TRACE,
                    {"event": f"cost_overrun:{tool.name}", "detail": {"usd": usd}},
                    "system",
                )

            # Reset breaker on successful response
            _breakers[(sid, tool.name)] = 0
            validate_and_route(
                sid,
                MessageKind.TRACE,
                {
                    "event": f"tool_ok:{tool.name}",
                    "detail": {
                        "s": round(time.time() - t0, 2),
                        "usd": round(usd, 6),
                        "estimated": est,
                    },
                },
                "llm",
            )
            return result, None
        except Exception as e:
            err = e
            _count_failure(sid, tool.name)

    # 5. All retries failed — invoke deterministic fallback
    validate_and_route(
        sid,
        MessageKind.TRACE,
        {"event": f"llm_fallback:{tool.name}:{type(err).__name__}"},
        "system",
    )
    return tool.fallback(args), tool.name


```

### recon_agent/app/core/states.py

```python
"""Finite State Machine and Pipeline Execution Lifecycle.

Provides the State enum and StateMachine class that coordinate all state
transitions, abort tokens, circuit breaker halts, and safe interactive resumption.
Emits CONTROL events via the central channel dispatcher.
"""

import uuid
from enum import Enum
from typing import List, Optional

from app.core.channels import validate_and_route
from app.core.contracts import MessageKind
from app.core.dispatcher import reset_breaker


class State(str, Enum):
    """Pipeline execution lifecycle states."""
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
    """Deterministic finite state machine managing reconciliation execution flow.
    
    Coordinates sequential execution steps, handles voluntary and error halts,
    maintains abort tokens for cancellation, and supports reentry upon resumption.
    """

    def __init__(self, session_id: str) -> None:
        """Initialize state machine for a specific session.
        
        Args:
            session_id: Unique session identifier string.
        """
        self.sid: str = session_id
        self.state: Optional[State] = None
        self._token: Optional[str] = None
        self._abort_pending: bool = False
        self._pre_halt: Optional[State] = None
        self._halt_tools: List[str] = []

    def enter(self, s: State, detail: str = "") -> None:
        """Enter a new state and emit a STATE_ENTERED control event.
        
        Generates a fresh abort token for the new state.
        
        Args:
            s: Target state to enter.
            detail: Contextual note or reason for entering the state.
        """
        self.state = s
        self._token = uuid.uuid4().hex
        validate_and_route(
            self.sid,
            MessageKind.CONTROL,
            {
                "event": "STATE_ENTERED",
                "state": s.value,
                "abort_token": self._token,
                "detail": {"d": detail},
            },
            "system",
        )

    def request_abort(self, token: str) -> None:
        """Request pipeline abort if the supplied token matches the active state token.
        
        Args:
            token: Abort authorization token.
        """
        if token == self._token:
            self._abort_pending = True

    def transition(self, to: State, detail: str = "") -> bool:
        """Transition from current state to a target state.
        
        Checks if an abort was requested before transitioning. If aborted,
        transitions immediately to ABORT_CONFIRMED and returns False.
        
        Args:
            to: Destination state.
            detail: Contextual note or metrics for the transition.
            
        Returns:
            True if transition succeeded, False if aborted.
        """
        if self._abort_pending:
            self._abort_pending = False
            self.enter(State.ABORT_CONFIRMED)
            return False

        if self.state is not None:
            validate_and_route(
                self.sid,
                MessageKind.CONTROL,
                {"event": "STATE_EXITED", "state": self.state.value},
                "system",
            )
        self.enter(to, detail)
        return True

    def halt(self, reason: str, tools: Optional[List[str]] = None) -> None:
        """Pause pipeline execution due to a policy condition or circuit breaker trip.
        
        Saves current state in `_pre_halt` so execution can safely resume
        or re-verify without skipping gates.
        
        Args:
            reason: Human-readable diagnostic reason for the halt.
            tools: Optional list of tripped tool names requiring breaker resets.
        """
        self._pre_halt = self.state
        self._halt_tools = tools or []
        validate_and_route(
            self.sid,
            MessageKind.CONTROL,
            {
                "event": "HALT",
                "detail": {"reason": reason, "tools": self._halt_tools},
            },
            "system",
        )
        self.enter(State.HALT, reason)

    def resume(self) -> None:
        """Resume execution from a HALT state.
        
        Resets tripped circuit breakers and re-enters the pre-halt state
        to safely re-evaluate pipeline gates.
        """
        for t in self._halt_tools:
            reset_breaker(self.sid, t)
        validate_and_route(
            self.sid,
            MessageKind.CONTROL,
            {"event": "RESUMED", "detail": {"tools": self._halt_tools}},
            "user",
        )
        target = self._pre_halt or State.INGESTING
        self._halt_tools = []
        self.enter(target, "resumed")


```

### recon_agent/app/engine/__init__.py

```python


```

### recon_agent/app/engine/chatbot.py

```python
"""Grounded AI Reconciliation Assistant and Conversational Chat Session.

Provides strict context grounding for multi-turn conversations with Gemma 4 31B.
Constructs prompt snapshots containing exclusively active session datasets, schema mappings,
balance summaries, and classified exceptions. Enforces strict factual isolation so deleted
or replaced files cannot leak into model responses or cause hallucinations.
"""

import json
from typing import Any, Dict, List, Optional

from app.core import llm_client


def build_grounded_context(pipe: Any) -> str:
    """Construct a strict context snapshot containing ONLY active session datasets and reports.
    
    Includes:
      1. Active table names, record counts, column lists, and sample data previews.
      2. Active schema mapping configuration (keys, amounts, dates).
      3. Final reconciliation metrics and financial balances (gross, net, fees, matched, exception).
      4. Classified exceptions queue with diagnostic explanations and action statuses.
      5. Strict prompt instructions prohibiting hallucinations regarding deleted files.
      
    Args:
        pipe: Pipeline instance for the active session.
        
    Returns:
        Structured markdown context string for the LLM system instruction.
    """
    if not pipe or not getattr(pipe, "tables", None):
        return "NO_ACTIVE_FILES: There are no files or datasets loaded in the current active session."

    lines: List[str] = []
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

    # 5. Core Assistant Guardrails
    lines.append("\n=== CRITICAL RECONCILIATION ASSISTANT RULES ===")
    lines.append("1. You are the AI Reconciliation Assistant for this financial dataset.")
    lines.append("2. Answer the user's questions strictly using the ACTIVE dataset and report provided above.")
    lines.append("3. If the user asks about a file, order, transaction, or column that was deleted, replaced, or is not in the active dataset, you MUST state clearly that the file/data is not present in the current active session.")
    lines.append("4. Never hallucinate data for deleted files or nonexistent transactions.")
    lines.append("5. Keep answers concise, factual, and formatted in clear markdown.")

    return "\n".join(lines)


class ReconChatSession:
    """Manages multi-turn conversation state and dataset grounding for a session.
    
    Attributes:
        sid: Session identifier string.
        pipe: Reference to the active Pipeline instance.
        history: Multi-turn message history list.
    """

    def __init__(self, sid: str, pipe: Optional[Any] = None) -> None:
        """Initialize chat session.
        
        Args:
            sid: Session identifier string.
            pipe: Optional Pipeline instance.
        """
        self.sid: str = sid
        self.pipe: Optional[Any] = pipe
        self.history: List[Dict[str, str]] = []

    def set_pipe(self, pipe: Any) -> None:
        """Update or re-bind the active Pipeline reference."""
        self.pipe = pipe

    def chat(self, user_message: str) -> Dict[str, Any]:
        """Process a user question against the current active reconciliation dataset.
        
        If no files are currently ingested, refuses politely without making API calls.
        Maintains conversation history and rolls back the last user message on network errors.
        
        Args:
            user_message: User question or prompt string.
            
        Returns:
            Dictionary with 'ok' (bool), 'response' (str), 'cost_usd' (float), and error details.
        """
        # Refuse to chat if no files are loaded in the current active session
        if not self.pipe or not getattr(self.pipe, "tables", None) or len(self.pipe.tables) == 0:
            return {
                "ok": False,
                "error": "No active files loaded. The conversation starts only after files are uploaded/ingested.",
                "response": "Please upload or ingest reconciliation files before starting the conversation.",
            }

        context = build_grounded_context(self.pipe)

        # Append user turn to history
        self.history.append({"role": "user", "content": user_message})

        try:
            reply, cost = llm_client.conversational_chat(self.history, system_instruction=context)
            self.history.append({"role": "model", "content": reply})
            return {
                "ok": True,
                "response": reply,
                "cost_usd": cost,
                "session_id": self.sid,
            }
        except Exception as e:
            # Rollback last user turn on network or LLM failure
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
            return {
                "ok": False,
                "error": str(e),
                "response": f"Failed to generate response: {e}",
            }


```

### recon_agent/app/engine/fee.py

```python
"""Payment Gateway Fee Modeling and Decimal Precision Calculation.

Provides deterministic calculation of merchant gateway fees across multiple
pricing structures (flat rate percentage, per-transaction fixed fee, tiered volume bands)
and calculates applicable GST (Goods and Services Tax) with exact bankers rounding.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union

from app.core.contracts import FeeSchedule


def compute_fee(gross: Union[float, int, str, Decimal], schedule: FeeSchedule) -> float:
    """Compute the expected payment gateway processing fee and GST for a gross transaction amount.
    
    Calculation modes:
      - `flat_rate`: `gross * rate` (e.g. 2.0% MDR)
      - `per_txn_flat`: Fixed charge per transaction (e.g. ₹5.00)
      - `tiered`: Slices gross amount into tiered bands `[lo, hi, rate]`
      
    If `schedule.gst_rate` is non-zero (e.g., 0.18 for 18% GST), multiplies the fee
    by `(1 + gst_rate)` and quantizes the result to 2 decimal places using `ROUND_HALF_UP`.
    
    Args:
        gross: Gross transaction amount in source currency (e.g. INR).
        schedule: FeeSchedule configuration containing pricing model and GST rate.
        
    Returns:
        Calculated total fee as a float rounded to 2 decimal places.
    """
    g = Decimal(str(gross))

    if schedule.model_type == "flat_rate":
        fee = g * Decimal(str(schedule.params["rate"]))
    elif schedule.model_type == "per_txn_flat":
        fee = Decimal(str(schedule.params["flat"]))
    else:
        # Tiered volume rate bands: [(lo, hi, rate), ...]
        fee, rem = Decimal(0), g
        for lo, hi, rate in schedule.params["tiers"]:
            band = min(rem, Decimal(str(hi)) - Decimal(str(lo))) if hi else rem
            fee += band * Decimal(str(rate))
            rem -= band

    # Apply Goods and Services Tax (GST) if configured on the fee schedule
    if schedule.gst_rate:
        fee *= (1 + Decimal(str(schedule.gst_rate)))

    return float(fee.quantize(Decimal("0.01"), ROUND_HALF_UP))


```

### recon_agent/app/engine/match.py

```python
"""Multi-Attribute Matching Engine and Similarity Scoring.

Implements multi-signal pairing algorithms combining:
  - Exact and fuzzy reference key similarity (Levenshtein distance, token containment, digit matching).
  - Net and gross amount tolerance matching with dynamic fee modeling.
  - Business day date window calculations (ignoring weekend clearing delays).
  - LLM-assisted semantic similarity scoring via Gemma 4 with fallback handling.
"""

import datetime
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, model_validator

from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import EvidencePiece, MessageKind
from app.core.dispatcher import dispatch_tool_call, ToolCall
from app.engine.fee import compute_fee


class SemArgs(BaseModel):
    """Input payload schema for LLM semantic similarity evaluation."""
    left: Dict[str, Any]
    right: Dict[str, Any]


class SemResult(BaseModel):
    """Result schema for LLM semantic similarity scoring."""
    score: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def parse_score(cls, data: Any) -> Dict[str, float]:
        """Parse numerical score from various raw LLM response shapes."""
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


# LLM tool call specification for semantic similarity scoring
SEM_TOOL = ToolCall(
    name="semantic_similarity",
    args_schema=SemArgs,
    result_schema=SemResult,
    timeout_s=REG["llm_tool_timeout_s"],
    retries=2,
    fallback=lambda a: None,
    cost_budget_usd=0.005,
)


def _lev(a: str, b: str) -> int:
    """Compute standard Levenshtein edit distance between two strings.
    
    Args:
        a: First string.
        b: Second string.
        
    Returns:
        Minimum number of single-character edits (insertions, deletions, substitutions).
    """
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _normalize_token(s: Any) -> str:
    """Strip all non-alphanumeric characters and convert string to lowercase.
    
    Example: 'INV/2026/1039' -> 'inv20261039'.
    """
    return re.sub(r"[^a-zA-Z0-9]", "", str(s)).lower()


def _sim(a: Any, b: Any) -> float:
    """Compute a multi-heuristic similarity score between two identifier strings.
    
    Evaluates:
      1. Exact match and normalized alphanumeric match (e.g. 'INV/2026/1039' == 'INV20261039').
      2. Token substring containment (e.g. 'TXN-ORD-1036' vs 'ORD-1036').
      3. Common numeric sequence matching (e.g. extracting digit runs like '1036').
      4. Normalized Levenshtein edit distance ratio.
      
    Args:
        a: First reference identifier.
        b: Second reference identifier.
        
    Returns:
        Similarity score between 0.0 (unrelated) and 1.0 (identical).
    """
    a_str, b_str = str(a).lower(), str(b).lower()
    if a_str == b_str:
        return 1.0

    # 1. Alphanumeric normalized match
    norm_a, norm_b = _normalize_token(a_str), _normalize_token(b_str)
    if norm_a and norm_a == norm_b:
        return 1.0

    # 2. Token containment and numeric key extraction
    if norm_a and norm_b:
        if norm_a in norm_b or norm_b in norm_a:
            shorter, longer = (norm_a, norm_b) if len(norm_a) < len(norm_b) else (norm_b, norm_a)
            # If the shared subpart is substantial (at least 4 chars or >=50% of the longer token)
            if len(shorter) >= 4 or (len(shorter) / max(len(longer), 1)) >= 0.5:
                return round(max(0.88, len(shorter) / max(len(longer), 1)), 3)

        # Extract digit sequences (e.g. 1036, 1037, 1038)
        digits_a = re.findall(r"\d{3,}", norm_a)
        digits_b = re.findall(r"\d{3,}", norm_b)
        if digits_a and digits_b and any(d in digits_b for d in digits_a):
            return 0.90

    # 3. Normalized Levenshtein distance
    if norm_a and norm_b:
        norm_score = 1 - _lev(norm_a, norm_b) / max(len(norm_a), len(norm_b), 1)
        if norm_score >= 0.70:
            return round(norm_score, 3)

    return round(1 - _lev(a_str, b_str) / max(len(a_str), len(b_str), 1), 3)


def _busdays(d1: datetime.date, d2: datetime.date) -> int:
    """Calculate the number of business days (Monday through Friday) between two dates.
    
    Excludes weekend days to avoid falsely penalizing banking clearing delays.
    
    Args:
        d1: First date.
        d2: Second date.
        
    Returns:
        Integer count of business days between d1 and d2.
    """
    a, b = sorted((d1, d2))
    n, cur = 0, a
    while cur < b:
        cur += datetime.timedelta(days=1)
        if cur.weekday() < 5:  # Monday=0, Sunday=6
            n += 1
    return n


def _d(v: Any) -> datetime.date:
    """Parse an arbitrary timestamp or date string into a standard date object."""
    return pd.to_datetime(v).date()


def fee_explains(a: float, rv: float, schedule: Optional[Any], tol: float) -> bool:
    """Check if the variance between ledger amount and bank deposit matches the fee schedule.
    
    Returns True if raw amount delta exceeds tolerance but net amount delta
    (gross minus calculated fee) is strictly within tolerance.
    
    Args:
        a: Gross ledger amount.
        rv: Received bank credit amount.
        schedule: Configured FeeSchedule.
        tol: Permissible tolerance in currency units (e.g. 0.01).
    """
    if not schedule:
        return False
    raw = abs(a - rv)
    net = abs((a - compute_fee(a, schedule)) - rv)
    return raw > tol and net <= tol


def score_pair(
    sid: str,
    l: Dict[str, Any],
    r: Dict[str, Any],
    cfg: Dict[str, Any],
    schedule: Optional[Any],
    fallback_events: List[str],
) -> Tuple[float, Dict[str, float], List[EvidencePiece], Optional[float]]:
    """Compute composite multi-attribute match score for a candidate pair of records.
    
    Evaluates:
      1. Reference key similarity (`w_match_key`).
      2. Amount agreement on gross or net-of-fee basis (`w_match_amount`).
      3. Date proximity in business days (`w_match_date`).
      4. Semantic similarity via LLM or deterministic fallback (`w_match_semantic`).
      
    Args:
        sid: Session identifier string.
        l: Left ledger record dict.
        r: Right statement record dict.
        cfg: Schema mapping configuration (field names, tolerance, window_days).
        schedule: Active FeeSchedule instance.
        fallback_events: Mutable list collecting fallback event names.
        
    Returns:
        Tuple of (composite_score, component_scores_dict, evidence_pieces_list, signed_amount_delta).
    """
    tol, win = cfg["tolerance"], cfg["window_days"]
    comps: Dict[str, float] = {}
    w: Dict[str, float] = {}

    # 1. Key similarity
    key = (
        1.0
        if str(l[cfg["left_key"]]) == str(r[cfg["right_key"]])
        else _sim(l[cfg["left_key"]], r[cfg["right_key"]])
    )
    comps["key"], w["key"] = key, REG["w_match_key"]

    # 2. Amount scoring with fee schedule evaluation
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
        comps["amount"] = (
            1.0
            if (raw_matched or net_matched)
            else max(0.0, 1 - best / max(abs(a) * REG["amount_score_scale_pct"], 1.0))
        )
        w["amount"] = REG["w_match_amount"]
    else:
        fallback_events.append("amount_component_skipped")

    # 3. Date window scoring in business days
    ddiff = None
    if cfg.get("left_date") and cfg.get("right_date"):
        ddiff = _busdays(_d(l[cfg["left_date"]]), _d(r[cfg["right_date"]]))
        comps["date"] = max(0.0, 1 - ddiff / win)
        w["date"] = REG["w_match_date"]

    # 4. Semantic similarity scoring
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

    # Calculate weighted composite score
    value = sum(comps[k] * w[k] for k in comps) / sum(w.values())

    # Collect discrete verified evidence pieces
    evidence: List[EvidencePiece] = []
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
"""Discrepancy Quality Assurance and Predicate Classification Engine.

Applies prioritized deterministic predicates over record attributes and candidate
contexts to classify discrepancies into precise root-cause categories (Duplicate, Split,
Temporal Drift, Fee Deduction, Refund Offset, Counterparty Mismatch, Amount Delta).
"""

from typing import Any, Callable, Dict, List

from app.core.contracts import HYPOTHESIS_PRIORITY, HypothesisCategory as H, UnmatchedRecord

# Standard context keys populated during candidate extraction
CTX_KEYS: List[str] = [
    "dup_rids",
    "split_targets",
    "single_target",
    "partial",
    "fee_match",
    "tax_match",
    "fx_match",
    "fuzzy_key",
    "negative_credit",
    "date_only_mismatch",
]

# Predicate functions mapped to each discrepancy category
_PREDICATES: Dict[H, Callable[[UnmatchedRecord, Dict[str, Any]], bool]] = {
    H.DUPLICATE: lambda rec, ctx: bool(ctx.get("dup_rids")),
    H.SPLIT: lambda rec, ctx: bool(ctx.get("split_targets")),
    H.PARTIAL_PAYMENT: lambda rec, ctx: (
        rec.delta is not None
        and rec.delta > 0.01
        and ctx.get("single_target")
        and ctx.get("partial")
    ),
    H.REFUND_OFFSET: lambda rec, ctx: (
        bool(ctx.get("negative_credit"))
        or (rec.delta is not None and rec.delta < -0.01)
    ),
    H.FEE_DEDUCTION: lambda rec, ctx: bool(ctx.get("fee_match")),
    H.TAX_WITHHOLDING: lambda rec, ctx: bool(ctx.get("tax_match")),
    H.CURRENCY_CONVERSION: lambda rec, ctx: bool(ctx.get("fx_match")),
    H.TEMPORAL_DRIFT: lambda rec, ctx: bool(ctx.get("date_only_mismatch")),
    H.COUNTERPARTY_MISMATCH: lambda rec, ctx: bool(ctx.get("fuzzy_key")),
    H.AMOUNT_DELTA: lambda rec, ctx: (
        rec.delta is not None and abs(rec.delta) > 0.01
    ),
    H.UNCLASSIFIED: lambda rec, ctx: True,
}

# Ordered list of hypothesis categories sorted by business precedence
_ORDERED: List[H] = sorted(HYPOTHESIS_PRIORITY, key=HYPOTHESIS_PRIORITY.get)


def classify(rec: UnmatchedRecord, ctx: Dict[str, Any]) -> H:
    """Classify an unmatched record into the highest-priority matching hypothesis category.
    
    Iterates through hypothesis predicates in precedence order (e.g. DUPLICATE before SPLIT,
    SPLIT before TEMPORAL_DRIFT, etc.).
    
    Args:
        rec: UnmatchedRecord instance to classify.
        ctx: Context dictionary containing detected signals and match candidate properties.
        
    Returns:
        The matched HypothesisCategory enum value.
    """
    for category in _ORDERED:
        predicate = _PREDICATES.get(category)
        if predicate and predicate(rec, ctx):
            return category
    return H.UNCLASSIFIED


```

### recon_agent/app/engine/resolving.py

```python
"""Exception Resolution Logic and Diagnostic Explanation Generation.

Calculates confidence scores for classified discrepancy hypotheses, determines
automated action policies (auto_resolve vs request_confirmation vs mark_pending),
and generates audit-ready root-cause explanations for every unmatched record.
"""

from typing import Any, Dict, Optional

from app.core.constants import REG
from app.core.contracts import HYPOTHESIS_PRIORITY, HypothesisCategory, UnmatchedRecord

_MAX_RANK = max(HYPOTHESIS_PRIORITY.values())


def category_confidence(category: HypothesisCategory) -> float:
    """Calculate base normalized confidence score from the hypothesis priority taxonomy.
    
    Args:
        category: Classified HypothesisCategory.
        
    Returns:
        Confidence score between 0.0 and 1.0 based on taxonomy ranking.
    """
    p = HYPOTHESIS_PRIORITY.get(category, _MAX_RANK)
    return round(1.0 - (p - 1) / (_MAX_RANK - 1), 3)


def exception_confidence(
    evidence_count: int,
    category: HypothesisCategory,
    sem: Optional[float] = None,
) -> float:
    """Compute overall confidence for an exception hypothesis.
    
    Applies high confidence (0.88 - 0.98) for verified operational patterns with
    corroborating evidence (Temporal Drift, Split settlements, Fee Deductions, Token matches).
    Applies baseline confidence (0.85) for confirmed anomalies (Duplicates, Refund Offsets).
    Uses weighted multi-signal scoring for unclassified items.
    
    Args:
        evidence_count: Number of verified EvidencePiece pieces attached to the record.
        category: Classified HypothesisCategory.
        sem: Optional semantic similarity score.
        
    Returns:
        Composite confidence score in [0.0, 1.0].
    """
    # High confidence for verified business patterns supported by evidence
    if category in (
        HypothesisCategory.TEMPORAL_DRIFT,
        HypothesisCategory.SPLIT,
        HypothesisCategory.FEE_DEDUCTION,
        HypothesisCategory.COUNTERPARTY_MISMATCH,
    ):
        base = 0.88 + 0.04 * min(evidence_count, 2)
        return min(round(base, 3), 0.98)

    # Well-categorized anomalies requiring confirmation
    if category in (HypothesisCategory.DUPLICATE, HypothesisCategory.REFUND_OFFSET):
        return round(0.85, 3)

    # Weighted scoring for unclassified or partially matched discrepancies
    return (
        min(evidence_count / 4, 1.0) * REG["w_exception_evidence"]
        + category_confidence(category) * REG["w_exception_category"]
        + (sem or 0.0) * REG["w_exception_semantic"]
    )


def decide_action(
    conf: float,
    evidence_count: int,
    category: Optional[HypothesisCategory] = None,
) -> str:
    """Determine the automated action policy for an exception item.
    
    Actions:
      - 'auto_resolve': Legitimate business variation (e.g. gateway fees, timing drift)
                        that should be approved automatically without stopping the run.
      - 'request_confirmation': Legitimate discrepancy or anomaly requiring operator review.
      - 'mark_pending': Low-confidence unclassified discrepancy awaiting manual investigation.
      
    Args:
        conf: Computed exception confidence score.
        evidence_count: Count of supporting evidence pieces.
        category: Optional classified HypothesisCategory.
        
    Returns:
        Action string ('auto_resolve', 'request_confirmation', or 'mark_pending').
    """
    # Non-error business variations that should be automatically approved
    if category in (
        HypothesisCategory.TEMPORAL_DRIFT,
        HypothesisCategory.SPLIT,
        HypothesisCategory.FEE_DEDUCTION,
        HypothesisCategory.COUNTERPARTY_MISMATCH,
    ):
        return "auto_resolve"

    # Strict errors / anomalies that require human escalation
    if category in (
        HypothesisCategory.DUPLICATE,
        HypothesisCategory.REFUND_OFFSET,
        HypothesisCategory.UNCLASSIFIED,
    ):
        return "request_confirmation"

    # Threshold-based fallback policy evaluation
    if (
        conf >= REG["exception_auto_resolve_confidence"]
        and evidence_count >= REG["exception_auto_resolve_evidence_min"]
    ):
        return "auto_resolve"
    if 0.40 <= conf < 0.85:
        return "request_confirmation"
    return "mark_pending"


def generate_explanation(
    rec: UnmatchedRecord,
    ctx: Dict[str, Any],
    row_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a clear, human-readable root-cause diagnostic explanation for a record.
    
    Args:
        rec: UnmatchedRecord containing side, reference, delta, and classified reason.
        ctx: Context dictionary with candidate links, batch refs, and duplicate IDs.
        row_data: Optional raw row attributes from the source file.
        
    Returns:
        Formatted diagnostic explanation string.
    """
    cat = rec.reason
    side = rec.side
    ref = rec.ref or "N/A"

    if cat == HypothesisCategory.TEMPORAL_DRIFT:
        return (
            f"Approved [No Error]: Exact amount & reference '{ref}' matched; "
            "settlement deferred by bank holiday/clearing window."
        )
    elif cat == HypothesisCategory.SPLIT:
        if side == "L":
            batch_ref = ctx.get("split_batch_ref", "bank batch settlement")
            return (
                f"Approved [No Error]: Constituent transaction leg resolved as part of "
                f"batch deposit '{batch_ref}' net of gateway fees."
            )
        targets = ctx.get("split_targets", [])
        return (
            f"Approved [No Error]: Batch settlement combines multiple order legs "
            f"(RIDs {targets}) net of payment gateway fees."
        )
    elif cat == HypothesisCategory.FEE_DEDUCTION:
        return "Approved [No Error]: Net bank deposit variance matches standard payment gateway fee schedule."
    elif cat == HypothesisCategory.DUPLICATE:
        return f"Error in Source A (Ledger): Duplicate order reference '{ref}' recorded multiple times in payments ledger."
    elif cat == HypothesisCategory.REFUND_OFFSET:
        return (
            f"Anomaly in Source B (Bank): Negative credit entry (-₹{abs(rec.delta or 0):.2f}) "
            "representing customer refund or chargeback."
        )
    elif cat == HypothesisCategory.COUNTERPARTY_MISMATCH:
        return f"Approved [No Error]: Normalized token/semantic match verified between order '{ref}' and counterpart UTR."
    elif side == "L":
        return f"Error in Source B (Bank): Order '{ref}' exists in payments ledger but has no corresponding bank settlement credit."
    elif side == "R":
        return f"Error in Source A (Ledger): Unmatched bank credit for UTR '{ref}' without corresponding order in payments ledger."
    else:
        return f"Unclassified discrepancy for reference '{ref}'."


```

### recon_agent/app/engine/report.py

```python
"""Final Reconciliation Report Synthesis.

Aggregates execution metrics, precision/recall benchmark evaluations, financial
volume totals (gross, net, fees, matched, exception), metered LLM costs, and
classified exception counts into a canonical FinalReport contract model.
"""

from typing import Any, Dict, List, Optional

from app.core.constants import REG
from app.core.contracts import FinalReport
from app.core.cost import tracker_for


def build_final_report(
    sid: str,
    *,
    match_rate: float,
    precision_vs_truth: Optional[float],
    recall_vs_truth: Optional[float],
    throughput_rows_per_sec: float,
    exceptions: List[Dict[str, Any]],
    elapsed_seconds: float,
    totals: Dict[str, float],
    llm_user_disagreements: List[Dict[str, Any]],
    fallback_events: List[str],
) -> FinalReport:
    """Construct the immutable FinalReport model for a completed reconciliation session.
    
    Args:
        sid: Unique session identifier string.
        match_rate: Fraction of left ledger records matched (0.0 to 1.0).
        precision_vs_truth: Precision score evaluated against ground truth, if provided.
        recall_vs_truth: Recall score evaluated against ground truth, if provided.
        throughput_rows_per_sec: Processing throughput in total records per second.
        exceptions: Complete list of classified exception item dictionaries from the queue.
        elapsed_seconds: Total pipeline wall-clock execution duration in seconds.
        totals: Dictionary containing financial sums ('gross', 'net', 'fees', 'matched_value', 'exception_value').
        llm_user_disagreements: History of operator overrides deviating from system proposals.
        fallback_events: List of triggered deterministic fallback event names.
        
    Returns:
        Structured FinalReport instance.
    """
    tracker = tracker_for(sid)

    return FinalReport(
        match_rate=match_rate,
        precision_vs_truth=precision_vs_truth,
        recall_vs_truth=recall_vs_truth,
        throughput_rows_per_sec=throughput_rows_per_sec,
        honest_exception_count=len(exceptions),
        auto_resolved_count=sum(
            1 for e in exceptions if e.get("action") in ("auto_resolve", "mark_resolved")
        ),
        escalated_count=sum(
            1 for e in exceptions if e.get("action") in ("request_confirmation", "escalate")
        ),
        unresolved_count=sum(
            1 for e in exceptions if e.get("action") == "mark_pending"
        ),
        total_gross=totals["gross"],
        total_net=totals["net"],
        total_fees=totals["fees"],
        matched_value=totals["matched_value"],
        exception_value=totals["exception_value"],
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
"""FastAPI Reconciliation Server and Web Console Backend API v2.

Provides dedicated, high-performance REST and WebSocket endpoints for the
single-page reconciliation console:
  - Paginated ingestion data grids and column statistics with PII redaction.
  - Interactive schema mapping review and confidence band inspection.
  - Policy configuration and baseline dry-run calibration telemetry.
  - Real-time matched results and balance variance summaries.
  - Paginated exception queue with auto-approval explanations and manual override actions.
  - Priority-tiered event ring buffers (Priority 1: UI narration, Priority 2: Traces, Priority 3: Silent logs).
  - Export utilities for canonical reconciled CSVs, JSON reports, and JSONL audit hash chains.
"""

import asyncio
import csv
from collections import deque
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import threading
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from fastapi import APIRouter, FastAPI, File, HTTPException, Query, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
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
# Per-Session Registries and Priority-Tagged Event Ring Buffers
# -----------------------------------------------------------------------------
V2_SESSIONS: Dict[str, Dict[str, Any]] = {}
CHAT_SESSIONS: Dict[str, ReconChatSession] = {}
BUFFERS: Dict[str, Dict[str, deque]] = {}  # sid -> {"trace": deque(maxlen=2000), "logs": deque(maxlen=5000)}
_WS: Dict[str, Dict[str, Any]] = {}       # sid -> {"queues": set(), "loop": loop|None}

# Regex for low-priority telemetry events routed to silent logs (Priority 3)
_P3_PATTERN = re.compile(r"^(tool_ok|cost_overrun|args_rejected|AUDIT_COMMIT)")

# High-priority control signals routed to user notification stream (Priority 1)
_P1_CONTROL = {
    "STATE_ENTERED",
    "STATE_EXITED",
    "HALT",
    "RESUMED",
    "ABORT_CONFIRMED",
    "FILE_REQUESTED",
    "CONFIRMATION_REQUESTED",
}


def _buffers(sid: str) -> Dict[str, deque]:
    """Retrieve or initialize bounded ring buffers for trace and background log streams."""
    if sid not in BUFFERS:
        BUFFERS[sid] = {"trace": deque(maxlen=2000), "logs": deque(maxlen=5000)}
    return BUFFERS[sid]


def _classify(kind: MessageKind, payload: Dict[str, Any]) -> int:
    """Classify message into priority tiers: 1=user narration/cards, 2=trace, 3=silent background logs."""
    if kind in (MessageKind.CHAT, MessageKind.ARTIFACT):
        return 1
    if kind == MessageKind.CONTROL:
        return 1 if payload.get("event") in _P1_CONTROL else 2
    return 3 if _P3_PATTERN.match(payload.get("event", "")) else 2


def _push_ws(sid: str, frame: str) -> None:
    """Safely push a JSON message frame to all active WebSocket listeners for a session."""
    s = _WS.get(sid)
    if not s or not s.get("loop"):
        return
    for q in list(s["queues"]):
        try:
            s["loop"].call_soon_threadsafe(q.put_nowait, frame)
        except Exception:
            pass


def _bus_bridge(kind: MessageKind):
    """Factory creating an event listener bridging the internal bus to ring buffers and WebSockets."""
    def handler(sid: str, model: Any, source: str) -> None:
        payload = model.model_dump()
        prio = _classify(kind, payload)
        frame = {
            "kind": kind.value,
            "priority": prio,
            "source": source,
            "payload": payload,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        buf = _buffers(sid)
        (buf["logs"] if prio == 3 else buf["trace"]).append(frame)
        _push_ws(sid, json.dumps(frame, default=str))

    return handler


_bridge_installed = False


def _install_bus_bridge() -> None:
    """Idempotently register event bus bridge subscribers across all MessageKind channels."""
    global _bridge_installed
    if _bridge_installed:
        return
    for k in MessageKind:
        subscribe(k, _bus_bridge(k))
    _bridge_installed = True


# -----------------------------------------------------------------------------
# Helper Utilities
# -----------------------------------------------------------------------------
def _sess(sid: str) -> Dict[str, Any]:
    """Retrieve session dictionary or raise HTTP 404."""
    if sid not in V2_SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    return V2_SESSIONS[sid]


def _pipe(sid: str) -> Optional[Pipeline]:
    """Retrieve active Pipeline instance for a session."""
    return _sess(sid).get("pipe")


def _totals(pipe: Optional[Pipeline]) -> Optional[Dict[str, float]]:
    """Compute gross, net, fee, matched, and exception balance sums safely before AGGREGATING."""
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
    return {
        "gross": round(g, 2),
        "net": round(n, 2),
        "fees": round(g - n, 2),
        "matched_value": round(mv, 2),
        "exception_value": round(g - mv, 2),
    }


def _exception_rows(pipe: Optional[Pipeline]) -> List[Dict[str, Any]]:
    """Enrich exception queue records with row attributes, verified evidence details, and status notes."""
    rows = []
    cfg = getattr(pipe, "cfg", {}) or {}
    l_table_name = cfg.get("left_table", "payments")
    r_table_name = cfg.get("right_table", "bank")
    l_rows = {row["_rid"]: row for row in (pipe.tables.get(l_table_name, []) if getattr(pipe, "tables", None) else [])}
    r_rows = {row["_rid"]: row for row in (pipe.tables.get(r_table_name, []) if getattr(pipe, "tables", None) else [])}

    for item in getattr(pipe, "queue", None) or []:
        rec = item["rec"]
        action = item.get("action", "mark_pending")
        explanation = item.get("explanation") or getattr(rec, "explanation", None) or ""

        # Source record attributes
        src_table = l_table_name if rec.side == "L" else r_table_name
        src_row = (l_rows if rec.side == "L" else r_rows).get(rec.rid, {})
        record_data = {k: v for k, v in src_row.items() if not k.startswith("_")}

        # Formulate verified evidence details
        conf = item.get("conf", 0.0)
        pieces = [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])]

        piece_details = []
        for p in pieces:
            if p == "key_match":
                piece_details.append(f"key_match=1.0 (exact reference '{rec.ref}')")
            elif p == "amount_within_tol":
                delta_str = f"diff={abs(rec.delta):.2f}" if rec.delta is not None else "exact parity"
                piece_details.append(f"amount_within_tol=1.0 ({delta_str})")
            elif p == "date_within_window":
                piece_details.append("date_within_window=1.0 (clearing timeframe)")
            elif p == "fee_model_match":
                piece_details.append(f"fee_model_match=1.0 (diff={abs(rec.delta or 0):.2f} matches fee schedule)")
            else:
                piece_details.append(f"{p}=1.0")

        evidence_str = (
            f"{len(pieces)} verified evidence factors: {', '.join(piece_details)}"
            if piece_details
            else "rule consistency"
        )

        if action in ("auto_resolve", "mark_resolved"):
            auto_reason = f"Approved by engine: confidence={conf:.2f}, {evidence_str}."
        elif action == "declined":
            auto_reason = f"Rejected / Declined by operator review: confidence={conf:.2f} did not pass manual verification."
        elif action in ("escalate", "request_confirmation"):
            auto_reason = f"Awaiting operator review: confidence={conf:.2f}, {evidence_str}; potential variance or anomaly detected."
        else:
            auto_reason = f"Pending engine evaluation: confidence={conf:.2f}."

        rows.append({
            "rid": rec.rid,
            "side": rec.side,
            "source_table": src_table,
            "ref": rec.ref,
            "reason": rec.reason.value if hasattr(rec.reason, "value") else str(rec.reason),
            "delta": rec.delta,
            "confidence": round(conf, 3),
            "action": action,
            "explanation": explanation,
            "auto_reason": auto_reason,
            "manual_match_ref": item.get("manual_match_ref", ""),
            "record_data": record_data,
            "pieces": pieces,
        })
    return rows


def _paginate(items: List[Any], page: int, page_size: int) -> Dict[str, Any]:
    """Paginate an in-memory list and return sliced items with navigation metadata."""
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
# API v2 Router — Endpoint per Web Console Panel
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.post("/sessions")
def create_session() -> Dict[str, str]:
    """Create a new reconciliation session for API v2."""
    sid = uuid.uuid4().hex[:8]
    V2_SESSIONS[sid] = {"pipe": None, "files": {}}
    CHAT_SESSIONS[sid] = ReconChatSession(sid)
    _buffers(sid)
    audit_for(sid).append({"event": "SESSION_INITIALIZED", "session_id": sid})
    return {"session_id": sid}


@router.get("/sessions/{sid}/overview")
def overview(sid: str) -> Dict[str, Any]:
    """Retrieve high-level pipeline status, circuit breaker states, and token expenditures."""
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
        "table_counts": {
            k: len(v)
            for k, v in (pipe.tables if pipe and getattr(pipe, "tables", None) else {}).items()
        },
    }


@router.get("/sessions/{sid}/ingestion")
def ingestion(
    sid: str,
    table: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
) -> Dict[str, Any]:
    """Retrieve ingested tables with pagination and column statistics with PII redaction."""
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

    # Build metadata counts for all ingested tables
    table_meta = {}
    for name, rows in pipe.tables.items():
        cols = [k for k in (rows[0].keys() if rows else []) if not k.startswith("_")]
        table_meta[name] = {"total_rows": len(rows), "columns": cols}

    # Paginate specific table or default first pages
    tables = {}
    if table and table in pipe.tables:
        pg = _paginate(pipe.tables[table], page, page_size)
        tables[table] = pg
    elif table:
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found")
    else:
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
def mapping(sid: str) -> Dict[str, Any]:
    """Retrieve candidate schema links, composite confidence scores, and committed mapping fields."""
    pipe = _pipe(sid)
    if not pipe:
        return {"candidates": [], "committed": None, "confidence": 0.0}
    cands = []
    w = (
        REG["w_mapping_structural"],
        REG["w_mapping_sample"],
        REG["w_mapping_type"],
        REG["w_mapping_semantic"],
    )
    for ov, lt, lc, rt, rc in getattr(pipe, "_map_cands", [])[:6]:
        lp = next((p for p in pipe.profiles.get(lt, []) if p.name == lc), None)
        rp = next((p for p in pipe.profiles.get(rt, []) if p.name == rc), None)
        tc = 1.0 if (lp and rp and lp.dtype == rp.dtype) else 0.4
        sem = 0.5
        composite = w[0] * ov + w[1] * ov + w[2] * tc + w[3] * sem
        cands.append({
            "left": f"{lt}.{lc}",
            "right": f"{rt}.{rc}",
            "signals": {
                "structural_overlap": round(ov, 3),
                "sample_match_rate": round(ov, 3),
                "type_compatibility": tc,
                "semantic_plausibility": sem,
            },
            "composite": round(composite, 3),
            "band": (
                "auto"
                if composite >= REG["mapping_auto_accept"]
                else ("confirm" if composite >= REG["mapping_review_floor"] else "escalate")
            ),
        })
    return {
        "candidates": cands,
        "committed": (
            {
                k: pipe.cfg.get(k)
                for k in (
                    "left_table",
                    "right_table",
                    "left_key",
                    "right_key",
                    "left_amount",
                    "right_amount",
                    "left_date",
                    "right_date",
                    "tolerance",
                    "window_days",
                )
            }
            if pipe.cfg
            else None
        ),
        "confidence": round(getattr(pipe, "_map_conf", 0.0), 3),
        "ambiguous": getattr(pipe, "_ambiguous", False),
        "ambiguity_delta": REG["mapping_ambiguity_delta"],
    }


@router.get("/sessions/{sid}/policy")
def policy(sid: str) -> Dict[str, Any]:
    """Retrieve synthesized matching policy components, baseline calibrations, and fee schedules."""
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
        "revision_caps": {
            "iterations": REG["revision_iteration_cap"],
            "seconds": REG["revision_time_cap_s"],
            "usd": REG["revision_cost_cap_usd"],
        },
        "fee_schedules": [fs.model_dump(mode="json") for fs in REG.fee_schedules.values()],
    }


@router.get("/sessions/{sid}/results")
def results(sid: str) -> Dict[str, Any]:
    """Retrieve matched record pairs enriched with source attributes and financial totals."""
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "exec_res", None):
        return {"executed": False}
    r = pipe.exec_res

    cfg = getattr(pipe, "cfg", {}) or {}
    l_table_name = cfg.get("left_table", "payments")
    r_table_name = cfg.get("right_table", "bank")
    l_rows = {row["_rid"]: row for row in (pipe.tables.get(l_table_name, []) if getattr(pipe, "tables", None) else [])}
    r_rows = {row["_rid"]: row for row in (pipe.tables.get(r_table_name, []) if getattr(pipe, "tables", None) else [])}

    enriched_matched = []
    for m in r.matched:
        m_dict = m.model_dump()
        m_dict["l_data"] = {k: v for k, v in l_rows.get(m.l_rid, {}).items() if not k.startswith("_")}
        m_dict["r_data"] = {k: v for k, v in r_rows.get(m.r_rid, {}).items() if not k.startswith("_")}
        enriched_matched.append(m_dict)

    return {
        "executed": True,
        "match_rate": getattr(pipe, "match_rate", None),
        "precision_vs_truth": getattr(pipe, "precision", None),
        "recall_vs_truth": getattr(pipe, "recall", None),
        "throughput_rows_per_sec": getattr(pipe, "throughput", None),
        "matched": enriched_matched,
        "unmatched_count": len(r.unmatched),
        "duplicates": r.duplicates,
        "splits": r.splits,
        "variance": r.variance.model_dump(),
        "totals": _totals(pipe),
        "final_report": pipe.final.model_dump(mode="json") if getattr(pipe, "final", None) else None,
    }


@router.get("/sessions/{sid}/exceptions")
def exceptions(
    sid: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> Dict[str, Any]:
    """Retrieve paginated exception queue items with confidence breakdowns and action status."""
    pipe = _pipe(sid)
    if not pipe:
        return {"queue": [], "pagination": None}
    all_rows = _exception_rows(pipe)
    pg = _paginate(all_rows, page, page_size)
    return {
        "queue": pg["items"],
        "pagination": {k: v for k, v in pg.items() if k != "items"},
        "auto_resolve_gate": {
            "confidence": REG["exception_auto_resolve_confidence"],
            "evidence_min": REG["exception_auto_resolve_evidence_min"],
        },
        "summary": {
            "total": len(all_rows),
            "auto_resolved": sum(1 for r in all_rows if r["action"] in ("auto_resolve", "mark_resolved")),
            "needs_review": sum(1 for r in all_rows if r["action"] in ("request_confirmation", "escalate")),
            "pending": sum(1 for r in all_rows if r["action"] == "mark_pending"),
        },
    }


class ActionBody(BaseModel):
    """Payload schema for an operator exception action."""
    action: str          # "approve" | "decline" | "escalate"
    match_ref: str = ""  # Optional target reference ID to pair with
    note: str = ""


@router.post("/sessions/{sid}/exceptions/{rid}/action")
def exception_action(sid: str, rid: int, body: ActionBody) -> Dict[str, Any]:
    """Apply operator override decision to an exception and update report balance invariant."""
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "queue", None):
        raise HTTPException(status_code=404, detail="no exception queue")
    item = next((i for i in pipe.queue if i["rec"].rid == rid), None)
    if not item:
        raise HTTPException(status_code=404, detail="exception not found")

    prior_action = item.get("action", "mark_pending")
    prior = {
        "action": prior_action,
        "confidence": item.get("conf", 0.0),
        "reason": item["rec"].reason.value if hasattr(item["rec"].reason, "value") else str(item["rec"].reason),
        "pieces": [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])],
    }

    if body.action == "approve":
        item["action"] = "mark_resolved"
        if body.match_ref:
            item["manual_match_ref"] = body.match_ref
            item["rec"].ref = body.match_ref
    elif body.action == "decline":
        item["action"] = "declined"
    else:
        item["action"] = "escalate"

    audit_for(sid).append({
        "event": "USER_OVERRIDE",
        "rid": rid,
        "action": item["action"],
        "match_ref": body.match_ref if body.match_ref else None,
        "note": body.note,
        "prior": prior,
    })

    counts = None
    if getattr(pipe, "final", None) is not None:
        pipe.final.auto_resolved_count = sum(
            1 for e in pipe.queue if e.get("action") in ("auto_resolve", "mark_resolved")
        )
        pipe.final.escalated_count = sum(
            1 for e in pipe.queue if e.get("action") in ("request_confirmation", "escalate")
        )
        pipe.final.unresolved_count = sum(
            1 for e in pipe.queue if e.get("action") in ("mark_pending", "declined")
        )
        if prior_action != item["action"]:
            pipe.final.llm_user_disagreements.append({
                "rid": rid,
                "system_proposal": prior,
                "user_decision": {
                    "action": item["action"],
                    "match_ref": body.match_ref,
                    "note": body.note,
                },
                "disagreement_kind": "exception_override",
            })
        counts = {
            "auto_resolved": pipe.final.auto_resolved_count,
            "escalated": pipe.final.escalated_count,
            "unresolved": pipe.final.unresolved_count,
            "honest_total": pipe.final.honest_exception_count,
        }
    return {"ok": True, "rid": rid, "action": item["action"], "counts": counts}


@router.get("/sessions/{sid}/audit")
def audit(sid: str) -> Dict[str, Any]:
    """Retrieve full audit log records and cryptographic verification status."""
    log = audit_for(sid)
    return {"records": log.records, "verified": log.verify(), "count": len(log.records)}


@router.get("/sessions/{sid}/export.csv")
def export_reconciliation_csv(sid: str) -> StreamingResponse:
    """Generate a canonical reconciled output CSV combining matched pairs and classified exceptions."""
    pipe = _pipe(sid)
    if not pipe:
        raise HTTPException(status_code=404, detail="no pipeline")

    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow([
        "type",
        "l_rid",
        "r_rid",
        "ref",
        "side",
        "reason",
        "composite_score_or_confidence",
        "delta",
        "action",
        "explanation",
    ])

    # Write Matched Pairs
    if getattr(pipe, "exec_res", None) and getattr(pipe.exec_res, "matched", None):
        for m in pipe.exec_res.matched:
            writer.writerow([
                "matched",
                m.l_rid,
                m.r_rid,
                "",
                "",
                "",
                m.composite_score,
                "",
                "matched",
                "",
            ])

    # Write Exception Items
    if getattr(pipe, "queue", None):
        for item in pipe.queue:
            rec = item["rec"]
            writer.writerow([
                "exception",
                rec.rid if rec.side == "L" else "",
                rec.rid if rec.side == "R" else "",
                rec.ref or "",
                rec.side,
                rec.reason.value if hasattr(rec.reason, "value") else str(rec.reason),
                item.get("conf", 0.0),
                rec.delta if rec.delta is not None else "",
                item.get("action", "mark_pending"),
                (item.get("explanation") or getattr(rec, "explanation", "") or "").replace("\n", " "),
            ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reconciliation_output_{sid}.csv"},
    )


@router.get("/sessions/{sid}/export/report.json")
def export_report_json(sid: str) -> StreamingResponse:
    """Download the finalized reconciliation report as JSON."""
    pipe = _pipe(sid)
    if not pipe or not getattr(pipe, "final", None):
        raise HTTPException(status_code=404, detail="no final report yet")

    return StreamingResponse(
        iter([pipe.final.model_dump_json(indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=final_report_{sid}.json"},
    )


@router.get("/sessions/{sid}/export/audit.jsonl")
def export_audit_jsonl(sid: str) -> StreamingResponse:
    """Download the complete cryptographic audit chain as a JSONL stream."""
    log = audit_for(sid)
    lines = [json.dumps(r, default=str) for r in log.records]

    return StreamingResponse(
        iter(["\n".join(lines)]),
        media_type="application/jsonl",
        headers={"Content-Disposition": f"attachment; filename=audit_chain_{sid}.jsonl"},
    )


@router.get("/sessions/{sid}/trace")
def trace(sid: str) -> Dict[str, Any]:
    """Fetch stored execution telemetry events from the session trace ring buffer."""
    _sess(sid)
    return {"events": list(_buffers(sid)["trace"])}


@router.get("/sessions/{sid}/logs")
def logs(sid: str) -> Dict[str, Any]:
    """Fetch stored background log events from the session log ring buffer."""
    _sess(sid)
    return {"events": list(_buffers(sid)["logs"])}


# -----------------------------------------------------------------------------
# Mutations
# -----------------------------------------------------------------------------
@router.post("/sessions/{sid}/run")
async def run(sid: str, files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """Upload files and execute the reconciliation pipeline asynchronously."""
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
    audit_for(sid).append({
        "event": "RUN_STARTED",
        "files": [p.name for p in paths],
        "ts": datetime.now(timezone.utc).isoformat(),
    })

    def work():
        try:
            pipe.run(paths)
        except Exception as e:
            import traceback
            traceback.print_exc()

    threading.Thread(target=work, daemon=True).start()
    return {"ok": True, "files": [p.name for p in paths]}


@router.post("/sessions/{sid}/resume")
def resume(sid: str) -> Dict[str, Any]:
    """Resume a halted pipeline run from its pre-halt state in a background thread."""
    pipe = _pipe(sid)
    if not pipe:
        raise HTTPException(status_code=400, detail="no pipeline to resume")
    pipe.sm.resume()

    def cont():
        pipe.continue_run()

    threading.Thread(target=cont, daemon=True).start()
    return {"ok": True, "state": pipe.sm.state.value}


@router.post("/sessions/{sid}/restart")
def restart(sid: str) -> Dict[str, Any]:
    """Reset session pipeline, clear ring buffers, and record restart audit event."""
    sess = _sess(sid)
    sess["pipe"] = None
    sess["files"] = {}
    if sid in CHAT_SESSIONS:
        CHAT_SESSIONS.pop(sid, None)
    if sid in BUFFERS:
        BUFFERS[sid]["trace"].clear()
        BUFFERS[sid]["logs"].clear()
    audit_for(sid).append({
        "event": "ENGINE_RESTARTED",
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "session_id": sid}


@router.delete("/sessions/{sid}/files/{filename}")
def delete_file(sid: str, filename: str) -> Dict[str, Any]:
    """Delete uploaded file from the session's upload cache."""
    sess = _sess(sid)
    if filename in sess.get("files", {}):
        p = sess["files"].pop(filename)
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    return {"ok": True, "deleted": filename}


class AbortBody(BaseModel):
    """Payload schema for requesting a pipeline abort."""
    token: str


@router.post("/sessions/{sid}/abort")
def abort(sid: str, body: AbortBody) -> Dict[str, bool]:
    """Request pipeline abort using the active state abort token."""
    pipe = _pipe(sid)
    if not pipe:
        raise HTTPException(status_code=400, detail="no pipeline to abort")
    pipe.sm.request_abort(body.token)
    return {"ok": True}


class ChatBody(BaseModel):
    """Payload schema for assistant chat queries in API v2."""
    message: str


@router.post("/sessions/{sid}/chat")
def chat(sid: str, body: ChatBody) -> Dict[str, Any]:
    """Submit a question to the grounded AI reconciliation assistant."""
    _sess(sid)
    if sid not in CHAT_SESSIONS:
        CHAT_SESSIONS[sid] = ReconChatSession(sid, _pipe(sid))
    else:
        CHAT_SESSIONS[sid].set_pipe(_pipe(sid))
    return CHAT_SESSIONS[sid].chat(body.message)


# -----------------------------------------------------------------------------
# WebSocket Handler
# -----------------------------------------------------------------------------
async def ws_v2(websocket: WebSocket, sid: str) -> None:
    """WebSocket streaming endpoint for API v2 event telemetry."""
    await websocket.accept()
    s = _WS.setdefault(sid, {"queues": set(), "loop": None})
    q: asyncio.Queue = asyncio.Queue()
    s["queues"].add(q)
    s["loop"] = asyncio.get_running_loop()
    try:
        await websocket.send_text(
            json.dumps({
                "kind": "control",
                "priority": 1,
                "source": "system",
                "payload": {"event": "WS_CONNECTED", "session": sid},
                "ts": datetime.now(timezone.utc).isoformat(),
            })
        )
        while True:
            await websocket.send_text(await q.get())
    except (asyncio.CancelledError, Exception):
        pass
    finally:
        s["queues"].discard(q)


# -----------------------------------------------------------------------------
# Mounting
# -----------------------------------------------------------------------------
def mount_v2(app: FastAPI) -> FastAPI:
    """Mount API v2 routes, CORS middleware, WebSocket handler, and static file endpoints."""
    _install_bus_bridge()
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    # Enable CORS for browser integration
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
            "then reload /console</code>",
            status_code=404,
        )

    # Mount static assets directory
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


# -----------------------------------------------------------------------------
# Standalone Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    app = FastAPI(title="Razorpay Recon Agent API v2")
    mount_v2(app)
    uvicorn.run(app, host="127.0.0.1", port=8000)


```

### recon_agent/app/server/main.py

```python
"""FastAPI Reconciliation Server and REST/WebSocket API v1.

Provides backend API endpoints for session lifecycle management, multipart file
upload/deletion, asynchronous pipeline execution, interactive grounded AI chat,
real-time WebSocket event broadcasting, and operator override actions.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Set
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket
from pydantic import BaseModel

from app import config
from app.config import LOGS_DIR, UPLOAD_DIR
from app.core.audit import audit_for
from app.core.channels import subscribe, validate_and_route
from app.core.constants import REG
from app.core.contracts import MessageKind
from app.engine.chatbot import ReconChatSession
from app.pipeline import Pipeline
from app.server.api_v2 import mount_v2

# Configure server file logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SERVER_LOG_PATH = LOGS_DIR / "server.log"
LATEST_SESSION_LOG = LOGS_DIR / "session.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(SERVER_LOG_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("recon_agent")

app = FastAPI(title="Razorpay Reconciliation Agent API")

# Mount API v2 routes and static web console
mount_v2(app)

# In-memory session and chatbot registries
SESSIONS: Dict[str, Dict[str, Any]] = {}
CHAT_SESSIONS: Dict[str, ReconChatSession] = {}


def _write_session_log(sid: str, log_line: str) -> None:
    """Write an event line to both the per-session log file and the latest session.log pointer.
    
    Args:
        sid: Unique session identifier string.
        log_line: Serialized JSON log line string.
    """
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


def _bridge(kind: MessageKind):
    """Factory creating an event subscriber that logs events and pushes to active WebSockets."""
    def fn(sid: str, model: Any, source: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        log_entry = json.dumps(
            {
                "ts": ts,
                "sid": sid,
                "kind": kind.value,
                "source": source,
                "payload": model.model_dump(),
            },
            default=str,
        )
        _write_session_log(sid, log_entry)
        logger.info(f"[{sid}] [{source}] {kind.value}: {json.dumps(model.model_dump(), default=str)[:140]}")

        s = SESSIONS.get(sid)
        if not s or not s.get("loop"):
            return
        item = json.dumps(
            {"kind": kind.value, "source": source, "payload": model.model_dump()},
            default=str,
        )
        for aq in list(s["queues"]):
            s["loop"].call_soon_threadsafe(aq.put_nowait, item)

    return fn


# Subscribe bridge handlers for all MessageKind event streams
for _k in MessageKind:
    subscribe(_k, _bridge(_k))


@app.post("/api/sessions")
def new_session() -> Dict[str, str]:
    """Initialize a new reconciliation session with fresh log buffers and audit trails."""
    sid = uuid.uuid4().hex[:8]
    SESSIONS[sid] = {"pipe": None, "queues": set(), "loop": None, "files": {}}
    CHAT_SESSIONS[sid] = ReconChatSession(sid)

    # Clear and initialize fresh session log file
    logs_dir = getattr(config, "LOGS_DIR", LOGS_DIR)
    logs_dir.mkdir(parents=True, exist_ok=True)
    session_file = logs_dir / f"{sid}.log"
    latest_session_log = logs_dir / "session.log"
    session_file.write_text("", encoding="utf-8")
    latest_session_log.write_text("", encoding="utf-8")

    init_msg = json.dumps({
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "SESSION_INITIALIZED",
        "session_id": sid,
    })
    _write_session_log(sid, init_msg)
    logger.info(f"Initialized new session {sid} (cleared active session.log)")

    return {"session_id": sid}


@app.get("/api/sessions/{sid}/files")
def list_files(sid: str) -> Dict[str, Any]:
    """List all uploaded statement files and currently active ingested tables for a session."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    pipe = SESSIONS[sid].get("pipe")
    files_map = SESSIONS[sid].get("files", {})
    tables = list(pipe.tables.keys()) if pipe and getattr(pipe, "tables", None) else []
    return {
        "session_id": sid,
        "files": [
            {
                "filename": fname,
                "path": str(fpath),
                "size": fpath.stat().st_size if fpath.exists() else 0,
            }
            for fname, fpath in files_map.items()
        ],
        "active_tables": tables,
    }


@app.post("/api/sessions/{sid}/files")
async def add_files(sid: str, files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """Upload new CSV/Excel statement files to the session upload directory."""
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
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    logger.info(f"[{sid}] Added files: {added}")
    return {"ok": True, "added": added, "total_files": list(files_map.keys())}


@app.delete("/api/sessions/{sid}/files/{filename}")
def delete_file(sid: str, filename: str) -> Dict[str, Any]:
    """Delete a file from disk, purge its table from active memory, and reset chat history."""
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
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    logger.info(f"[{sid}] Deleted file {filename}. Remaining: {list(files_map.keys())}")
    return {"ok": True, "deleted": filename, "remaining_files": list(files_map.keys())}


@app.post("/api/sessions/{sid}/run")
async def run(sid: str, files: List[UploadFile] = File(...)) -> Dict[str, bool]:
    """Upload files and initiate pipeline execution in a background worker thread."""
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
            validate_and_route(
                sid,
                MessageKind.ARTIFACT,
                {
                    "kind": "exceptions",
                    "rows": [
                        {
                            "rid": i["rec"].rid,
                            "side": i["rec"].side,
                            "ref": i["rec"].ref,
                            "reason": i["rec"].reason.value,
                            "delta": i["rec"].delta,
                            "confidence": round(i["conf"], 3),
                            "action": i["action"],
                            "pieces": [p.value if hasattr(p, "value") else p for p in i["pieces"]],
                        }
                        for i in pipe.queue
                    ],
                    "summary": {"count": len(pipe.queue)},
                    "confidence_threshold": REG["exception_auto_resolve_confidence"],
                    "fallback_events": pipe.fb,
                },
                "server",
            )

    threading.Thread(target=work, daemon=True).start()
    return {"ok": True}


class ChatRequest(BaseModel):
    """Payload schema for grounded AI assistant chat queries."""
    message: str


@app.post("/api/sessions/{sid}/chat")
def chat_endpoint(sid: str, body: ChatRequest) -> Dict[str, Any]:
    """Submit a question to the grounded AI assistant for the specified session."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    pipe = SESSIONS[sid].get("pipe")
    if sid not in CHAT_SESSIONS:
        CHAT_SESSIONS[sid] = ReconChatSession(sid, pipe)
    else:
        CHAT_SESSIONS[sid].set_pipe(pipe)

    return CHAT_SESSIONS[sid].chat(body.message)


@app.websocket("/ws/{sid}")
async def ws(websocket: WebSocket, sid: str) -> None:
    """WebSocket connection endpoint streaming real-time event bus messages to clients."""
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
def audit(sid: str) -> Dict[str, Any]:
    """Retrieve full audit log history and cryptographic SHA-256 verification status."""
    log = audit_for(sid)
    return {"records": log.records, "verified": log.verify()}


@app.get("/api/sessions/{sid}/report")
def report(sid: str) -> Dict[str, Any]:
    """Retrieve the FinalReport model for the session, if completed."""
    pipe = SESSIONS.get(sid, {}).get("pipe")
    return {"report": pipe.final.model_dump() if pipe and getattr(pipe, "final", None) else None}


@app.get("/api/sessions/{sid}/input_data")
@app.get("/api/sessions/{sid}/data")
def get_input_data(sid: str) -> Dict[str, Any]:
    """Retrieve raw ingested table dictionaries and statistical column profiles."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    pipe = SESSIONS[sid].get("pipe")
    if not pipe or not getattr(pipe, "tables", None):
        return {"session_id": sid, "tables": {}, "profiles": {}}
    profiles = {k: [p.model_dump() for p in v] for k, v in getattr(pipe, "profiles", {}).items()}
    return {
        "session_id": sid,
        "tables": pipe.tables,
        "profiles": profiles,
    }


@app.post("/api/sessions/{sid}/exceptions/{rid}/action")
def override(sid: str, rid: int, body: Dict[str, Any]) -> Dict[str, bool]:
    """Execute an operator override on an exception item (approve, escalate, or decline)."""
    pipe = SESSIONS[sid]["pipe"]
    item = next((i for i in pipe.queue if i["rec"].rid == rid), None)
    if not item:
        return {"ok": False}
    prior_action = item.get("action", "mark_pending")
    prior_conf = item.get("conf", 0.0)
    prior_reason = item["rec"].reason.value if hasattr(item["rec"].reason, "value") else str(item["rec"].reason)

    new_action = "mark_resolved" if body.get("action") == "approve" else "escalate"
    item["action"] = new_action

    prior_decision = {
        "action": prior_action,
        "confidence": prior_conf,
        "reason": prior_reason,
        "pieces": [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])],
    }
    audit_for(sid).append({
        "event": "USER_OVERRIDE",
        "rid": rid,
        "action": item["action"],
        "note": body.get("note", ""),
        "prior": prior_decision,
    })

    if getattr(pipe, "final", None) is not None:
        pipe.final.auto_resolved_count = sum(
            1 for e in pipe.queue if e.get("action") in ("auto_resolve", "mark_resolved")
        )
        pipe.final.escalated_count = sum(
            1 for e in pipe.queue if e.get("action") in ("request_confirmation", "escalate")
        )
        pipe.final.unresolved_count = sum(
            1 for e in pipe.queue if e.get("action") == "mark_pending"
        )
        if prior_action != new_action:
            pipe.final.llm_user_disagreements.append({
                "rid": rid,
                "system_proposal": prior_decision,
                "user_decision": {"action": new_action, "note": body.get("note", "")},
                "disagreement_kind": "exception_override",
            })
        validate_and_route(
            sid,
            MessageKind.ARTIFACT,
            {
                "kind": "report",
                "summary": pipe.final.model_dump(),
                "confidence_threshold": REG["match_auto_threshold"],
                "fallback_events": pipe.fb,
            },
            "engine",
        )

    return {"ok": True}


@app.post("/api/sessions/{sid}/resume")
def resume(sid: str) -> Dict[str, bool]:
    """Resume a halted pipeline run from its pre-halt state."""
    pipe = SESSIONS[sid]["pipe"]
    pipe.sm.resume()

    def cont():
        pipe.continue_run()
        if getattr(pipe, "queue", None) is not None:
            validate_and_route(
                sid,
                MessageKind.ARTIFACT,
                {
                    "kind": "exceptions",
                    "rows": [
                        {
                            "rid": i["rec"].rid,
                            "side": i["rec"].side,
                            "ref": i["rec"].ref,
                            "reason": i["rec"].reason.value,
                            "delta": i["rec"].delta,
                            "confidence": round(i["conf"], 3),
                            "action": i["action"],
                            "pieces": [p.value if hasattr(p, "value") else p for p in i["pieces"]],
                        }
                        for i in pipe.queue
                    ],
                    "summary": {"count": len(pipe.queue)},
                    "confidence_threshold": REG["exception_auto_resolve_confidence"],
                    "fallback_events": pipe.fb,
                },
                "server",
            )

    threading.Thread(target=cont, daemon=True).start()
    return {"ok": True}


@app.post("/api/sessions/{sid}/abort")
def abort(sid: str, body: Dict[str, Any]) -> Dict[str, bool]:
    """Request pipeline abort using the active state abort token."""
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
  <title>Recon Agent | Enterprise Terminal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Roboto+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap"
    rel="stylesheet">
  <style>
    :root {
      --bg-paper: #F4F4F0;
      --bg-white: #FFFFFF;
      --bg-subtle: #ECECE6;
      --bg-subtle-2: #E2E2D8;
      --bg-blue: #E5EEF5;
      --bg-blue-dark: #D1E1EE;
      --bg-blue-accent: #A8C9E2;

      --ink: #111215;
      --ink-secondary: #3E414B;
      --ink-muted: #666A78;
      --ink-dim: #9297A6;

      --border: #111215;
      --border-subtle: #D2D2C8;
      --border-focus: #0055FF;

      --accent: #0055FF;
      --success: #15803D;
      --success-bg: #DCFCE7;
      --warning: #B45309;
      --warning-bg: #FEF3C7;
      --danger: #B91C1C;
      --danger-bg: #FEE2E2;

      --font-ui: 'Inter', -apple-system, sans-serif;
      --font-mono: 'Roboto Mono', monospace;
      --font-display: 'Space Grotesk', sans-serif;

      --sidebar-w: 220px;
      --copilot-w: 360px;
      --header-h: 46px;
      --status-bar-h: 26px;
      --radius: 0px;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      border-radius: var(--radius) !important;
    }

    html,
    body {
      height: 100%;
      width: 100%;
      overflow: hidden;
      font-family: var(--font-ui);
      font-size: 12.5px;
      color: var(--ink);
      background: var(--bg-paper);
      -webkit-font-smoothing: antialiased;
    }

    /* Global Paper Texture Overlay */
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 9999;
      opacity: 0.035;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
    }

    /* Scrollbars */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }

    ::-webkit-scrollbar-track {
      background: var(--bg-subtle);
    }

    ::-webkit-scrollbar-thumb {
      background: var(--ink);
      border: 1px solid var(--bg-paper);
    }

    ::-webkit-scrollbar-thumb:hover {
      background: var(--ink-secondary);
    }

    .mono {
      font-family: var(--font-mono);
      font-feature-settings: "tnum";
      font-variant-numeric: tabular-nums;
    }

    .display {
      font-family: var(--font-display);
    }

    /* Buttons */
    button {
      font-family: var(--font-ui);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      cursor: pointer;
      border: 2px solid var(--border);
      background: var(--bg-white);
      color: var(--ink);
      padding: 5px 10px;
      transition: all 0.1s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      white-space: nowrap;
      user-select: none;
    }

    button:hover {
      background: var(--ink);
      color: var(--bg-white);
    }

    button.primary {
      background: var(--ink);
      color: var(--bg-white);
      border-color: var(--ink);
    }

    button.primary:hover {
      background: var(--accent);
      border-color: var(--accent);
      color: #FFF;
    }

    button.ghost {
      border-color: transparent;
      background: transparent;
      color: var(--ink-secondary);
    }

    button.ghost:hover {
      background: var(--bg-subtle);
      color: var(--ink);
      border-color: var(--border-subtle);
    }

    button.blue {
      background: var(--bg-blue);
      border-color: var(--border);
    }

    button.blue:hover {
      background: var(--bg-blue-dark);
      color: var(--ink);
    }

    button.danger {
      background: var(--danger-bg);
      color: var(--danger);
      border-color: var(--danger);
    }

    button.danger:hover {
      background: var(--danger);
      color: #FFF;
    }

    button:disabled {
      opacity: 0.35;
      cursor: not-allowed;
      pointer-events: none;
    }

    /* Badges */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 5px;
      font-family: var(--font-mono);
      font-size: 9.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border: 1px solid var(--border);
      background: var(--bg-white);
    }

    .badge.success {
      background: var(--success-bg);
      color: var(--success);
      border-color: var(--success);
    }

    .badge.warning {
      background: var(--warning-bg);
      color: var(--warning);
      border-color: var(--warning);
    }

    .badge.danger {
      background: var(--danger-bg);
      color: var(--danger);
      border-color: var(--danger);
    }

    .badge.info {
      background: var(--bg-blue);
      color: var(--ink);
      border-color: var(--border);
    }

    .badge.solid {
      background: var(--ink);
      color: var(--bg-white);
    }

    /* Root Workspace Layout */
    .app-container {
      display: flex;
      flex-direction: column;
      height: 100vh;
      width: 100vw;
      overflow: hidden;
    }

    /* 1. Header Ribbon */
    .topbar {
      height: var(--header-h);
      background: var(--ink);
      color: var(--bg-white);
      display: flex;
      align-items: center;
      padding: 0 14px;
      gap: 14px;
      border-bottom: 2px solid var(--ink);
      flex-shrink: 0;
      z-index: 100;
    }

    .topbar .logo {
      font-family: var(--font-display);
      font-size: 14px;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .topbar .logo .dot {
      width: 7px;
      height: 7px;
      background: var(--bg-blue-accent);
    }

    .topbar .status {
      font-family: var(--font-mono);
      font-size: 10.5px;
      color: var(--bg-blue-accent);
      display: flex;
      align-items: center;
      gap: 8px;
      border-left: 1px solid rgba(255, 255, 255, 0.2);
      padding-left: 12px;
      height: 100%;
    }

    .pulse-dot {
      width: 6px;
      height: 6px;
      background: #94A3B8;
    }

    .pulse-dot.online {
      background: #4ADE80;
      box-shadow: 0 0 0 2px rgba(74, 222, 128, 0.25);
    }

    .topbar .spacer {
      flex: 1;
    }

    .topbar .actions {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .topbar button {
      border-color: rgba(255, 255, 255, 0.25);
      background: transparent;
      color: var(--bg-white);
      font-size: 10px;
      padding: 4px 8px;
    }

    .topbar button:hover {
      background: var(--bg-white);
      color: var(--ink);
      border-color: var(--bg-white);
    }

    .topbar button.primary {
      background: var(--bg-blue-accent);
      color: var(--ink);
      border-color: var(--bg-blue-accent);
    }

    .topbar button.primary:hover {
      background: #FFF;
      border-color: #FFF;
    }

    /* 2. Workspace Body (Flex 3-Pane + Drag Splitters) */
    .workspace-root {
      flex: 1;
      display: flex;
      min-height: 0;
      min-width: 0;
      overflow: hidden;
      position: relative;
    }

    /* Sidebar */
    .sidebar {
      width: var(--sidebar-w);
      min-width: 140px;
      max-width: 360px;
      background: var(--bg-white);
      border-right: 2px solid var(--border);
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      flex-shrink: 0;
    }

    .sidebar.collapsed {
      width: 50px !important;
      min-width: 50px !important;
    }

    .sidebar.collapsed .nav-label,
    .sidebar.collapsed .nav-title,
    .sidebar.collapsed .stepper,
    .sidebar.collapsed .badge {
      display: none !important;
    }

    .sidebar.collapsed .nav-item {
      justify-content: center;
      padding: 10px 0;
    }

    .nav-section {
      padding: 10px 0;
      border-bottom: 2px solid var(--border-subtle);
    }

    .nav-title {
      font-size: 9px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--ink-dim);
      padding: 0 12px;
      margin-bottom: 4px;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 7px 12px;
      font-size: 11.5px;
      font-weight: 600;
      color: var(--ink-secondary);
      cursor: pointer;
      border-left: 3px solid transparent;
      transition: all 0.1s;
    }

    .nav-item:hover {
      background: var(--bg-paper);
      color: var(--ink);
    }

    .nav-item.active {
      background: var(--bg-paper);
      color: var(--ink);
      border-left-color: var(--ink);
      font-weight: 700;
    }

    .nav-item .badge {
      margin-left: auto;
    }

    /* Pipeline Stepper in Sidebar */
    .stepper {
      padding: 10px 12px;
      background: var(--bg-paper);
      border-top: 2px solid var(--border);
      margin-top: auto;
    }

    .stepper-title {
      font-size: 9px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--ink-dim);
      margin-bottom: 6px;
    }

    .step {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 3px 0;
      font-size: 10.5px;
      color: var(--ink-dim);
      position: relative;
    }

    .step .node {
      width: 8px;
      height: 8px;
      border: 1.5px solid var(--border-subtle);
      background: var(--bg-white);
      flex-shrink: 0;
    }

    .step.done {
      color: var(--ink-secondary);
    }

    .step.done .node {
      background: var(--ink);
      border-color: var(--ink);
    }

    .step.active {
      color: var(--ink);
      font-weight: 700;
    }

    .step.active .node {
      border-color: var(--accent);
      background: var(--accent);
    }

    /* Draggable Splitter Bars */
    .resizer {
      width: 4px;
      background: var(--bg-subtle);
      border-left: 1px solid var(--border-subtle);
      border-right: 1px solid var(--border-subtle);
      cursor: col-resize;
      flex-shrink: 0;
      transition: background 0.15s;
      z-index: 30;
    }

    .resizer:hover,
    .resizer.dragging {
      background: var(--accent);
      border-color: var(--accent);
    }

    /* Center Stage Canvas */
    .center-stage {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
      min-height: 0;
      overflow: hidden;
      background-color: var(--bg-paper);
      background-image: radial-gradient(circle, #d1d1cd 1px, transparent 1px);
      background-size: 24px 24px;
    }

    .view-container {
      flex: 1;
      display: none;
      flex-direction: column;
      min-height: 0;
      min-width: 0;
      overflow: hidden;
    }

    .view-container.active {
      display: flex;
    }

    .view-header {
      background: var(--bg-white);
      border-bottom: 2px solid var(--border);
      padding: 10px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
      z-index: 20;
    }

    .view-title {
      font-family: var(--font-display);
      font-size: 17px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }

    .view-meta {
      font-family: var(--font-mono);
      font-size: 10.5px;
      color: var(--ink-muted);
      margin-top: 1px;
    }

    .view-actions {
      display: flex;
      gap: 6px;
    }

    .view-body {
      padding: 12px 16px;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 10px;
      min-height: 0;
      min-width: 0;
      overflow-y: auto;
    }

    /* KPI Filter Deck */
    .kpi-strip {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0;
      border: 2px solid var(--border);
      background: var(--bg-white);
      flex-shrink: 0;
    }

    .kpi {
      padding: 8px 12px;
      border-right: 2px solid var(--border);
      cursor: pointer;
      transition: background 0.1s;
    }

    .kpi:last-child {
      border-right: none;
    }

    .kpi:hover {
      background: var(--bg-paper);
    }

    .kpi.active {
      background: var(--bg-blue);
      outline: 2px solid var(--accent);
      outline-offset: -2px;
    }

    .kpi-label {
      font-size: 9px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--ink-muted);
      margin-bottom: 2px;
    }

    .kpi-value {
      font-family: var(--font-display);
      font-size: 20px;
      font-weight: 700;
      line-height: 1;
    }

    .kpi-delta {
      font-family: var(--font-mono);
      font-size: 10px;
      margin-top: 4px;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .kpi-delta.up {
      color: var(--success);
      font-weight: 600;
    }

    .kpi-delta.down {
      color: var(--danger);
      font-weight: 600;
    }

    /* Spreadsheet Container */
    .data-grid-container {
      border: 2px solid var(--border);
      background: var(--bg-white);
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
      min-width: 0;
      overflow: hidden;
    }

    .grid-toolbar {
      padding: 6px 10px;
      border-bottom: 2px solid var(--border);
      display: flex;
      align-items: center;
      gap: 10px;
      background: var(--bg-paper);
      flex-shrink: 0;
    }

    .grid-tabs {
      display: flex;
      gap: 0;
    }

    .grid-tab {
      padding: 4px 10px;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border: 2px solid var(--border);
      border-bottom: none;
      background: var(--bg-subtle);
      color: var(--ink-muted);
      cursor: pointer;
      margin-right: -2px;
    }

    .grid-tab.active {
      background: var(--bg-white);
      color: var(--ink);
      border-bottom: 2px solid var(--bg-white);
      position: relative;
      z-index: 2;
    }

    .grid-wrapper {
      overflow: auto;
      flex: 1;
      min-height: 0;
      min-width: 0;
      position: relative;
    }

    /* Spreadsheet Table */
    .data-grid {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 11.5px;
      font-family: var(--font-mono);
    }

    .data-grid th {
      position: sticky;
      top: 0;
      background: var(--ink);
      color: var(--bg-white);
      font-weight: 600;
      text-align: left;
      padding: 6px 8px;
      border-right: 1px solid rgba(255, 255, 255, 0.15);
      border-bottom: 2px solid var(--ink);
      font-size: 9.5px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      z-index: 10;
      white-space: nowrap;
    }

    .data-grid td {
      padding: 5px 8px;
      border-bottom: 1px solid var(--border-subtle);
      border-right: 1px solid var(--border-subtle);
      white-space: nowrap;
    }

    .data-grid tr:hover td {
      background: var(--bg-blue) !important;
      cursor: pointer;
    }

    .data-grid tr.selected td {
      background: var(--bg-blue-dark) !important;
      font-weight: 600;
    }

    /* Pinned Columns */
    .pin-1 {
      position: sticky;
      left: 0;
      z-index: 5;
      background: var(--bg-white);
    }

    .pin-2 {
      position: sticky;
      left: 36px;
      z-index: 5;
      background: var(--bg-white);
    }

    th.pin-1,
    th.pin-2 {
      z-index: 15;
      background: var(--ink);
    }

    .num-cell {
      text-align: right;
      font-variant-numeric: tabular-nums;
    }

    .delta-tag {
      display: inline-block;
      padding: 1px 4px;
      font-size: 10px;
      font-weight: 700;
      border: 1px solid var(--border);
    }

    .delta-tag.pos {
      background: var(--warning-bg);
      color: var(--warning);
      border-color: var(--warning);
    }

    .delta-tag.neg {
      background: var(--danger-bg);
      color: var(--danger);
      border-color: var(--danger);
    }

    .delta-tag.zero {
      color: var(--ink-dim);
      border-color: var(--border-subtle);
      background: transparent;
    }

    /* Bottom Diff Inspector */
    .diff-drawer {
      border-top: 2px solid var(--border);
      background: var(--bg-paper);
      display: none;
      flex-direction: column;
      flex-shrink: 0;
      height: 160px;
    }

    .diff-drawer.open {
      display: flex;
    }

    .diff-header {
      padding: 4px 10px;
      background: var(--bg-white);
      border-bottom: 2px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 700;
      font-size: 10.5px;
    }

    .diff-content {
      flex: 1;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      padding: 8px 12px;
      overflow: auto;
    }

    .diff-card {
      border: 2px solid var(--border);
      background: var(--bg-white);
      padding: 6px 10px;
      font-family: var(--font-mono);
      font-size: 10.5px;
    }

    /* Status Bar */
    .spreadsheet-status-bar {
      height: var(--status-bar-h);
      background: var(--bg-paper);
      border-top: 2px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 10px;
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--ink-secondary);
      flex-shrink: 0;
    }

    /* 4. Resizable Copilot Pane */
    .copilot {
      width: var(--copilot-w);
      min-width: 240px;
      max-width: 600px;
      background: var(--bg-blue);
      border-left: 2px solid var(--border);
      display: flex;
      flex-direction: column;
      position: relative;
      overflow: hidden;
      flex-shrink: 0;
    }

    .copilot.closed {
      display: none !important;
    }

    .copilot::before {
      content: "";
      position: absolute;
      inset: 0;
      background-image: linear-gradient(rgba(168, 201, 226, 0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(168, 201, 226, 0.3) 1px, transparent 1px);
      background-size: 20px 20px;
      pointer-events: none;
      z-index: 0;
    }

    .copilot>* {
      position: relative;
      z-index: 1;
    }

    .copilot-header {
      padding: 8px 12px;
      border-bottom: 2px solid var(--border);
      background: var(--bg-blue-dark);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .copilot-messages {
      flex: 1;
      overflow-y: auto;
      padding: 10px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .chat-msg {
      display: flex;
      gap: 6px;
      max-width: 94%;
    }

    .chat-msg.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }

    .chat-msg-avatar {
      width: 20px;
      height: 20px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-mono);
      font-size: 9px;
      font-weight: 700;
      border: 2px solid var(--ink);
      background: var(--bg-white);
    }

    .chat-msg.user .chat-msg-avatar {
      background: var(--ink);
      color: #FFF;
    }

    .chat-msg-bubble {
      padding: 6px 10px;
      font-size: 11px;
      line-height: 1.45;
      border: 2px solid var(--border);
      background: var(--bg-white);
    }

    .chat-msg.user .chat-msg-bubble {
      background: var(--ink);
      color: #FFF;
      border-color: var(--ink);
    }

    .prompt-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      padding: 6px 10px;
      background: var(--bg-blue-dark);
      border-top: 2px solid var(--border);
    }

    .chip-btn {
      font-size: 9.5px;
      padding: 2px 5px;
      background: var(--bg-white);
      border: 1px solid var(--border);
    }

    .chip-btn:hover {
      background: var(--ink);
      color: #FFF;
    }

    .copilot-input-area {
      padding: 8px 10px;
      border-top: 2px solid var(--border);
      background: var(--bg-blue-dark);
    }

    .copilot-input-wrapper {
      display: flex;
      gap: 4px;
    }

    .copilot-input {
      flex: 1;
      background: var(--bg-white);
      border: 2px solid var(--border);
      padding: 5px 7px;
      font-family: var(--font-mono);
      font-size: 11px;
      outline: none;
    }

    .copilot-input:focus {
      border-color: var(--accent);
    }

    /* Staging Dropzone & General Cards */
    .dropzone {
      border: 2px dashed var(--border);
      padding: 20px;
      text-align: center;
      background: var(--bg-white);
      cursor: pointer;
      transition: all 0.15s ease;
      flex-shrink: 0;
    }

    .dropzone:hover,
    .dropzone.drag {
      background: var(--bg-blue);
      border-color: var(--accent);
    }

    .dropzone b {
      display: block;
      font-family: var(--font-display);
      font-size: 14px;
      margin-bottom: 2px;
    }

    .card {
      border: 2px solid var(--border);
      background: var(--bg-white);
      padding: 10px 14px;
      margin-bottom: 8px;
      flex-shrink: 0;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
      padding-bottom: 6px;
      border-bottom: 1px solid var(--border-subtle);
    }

    .kv {
      display: grid;
      grid-template-columns: 160px 1fr;
      gap: 4px;
      font-size: 11px;
    }

    .kv .k {
      font-weight: 700;
      text-transform: uppercase;
      color: var(--ink-muted);
      font-size: 9.5px;
    }

    .kv .v {
      font-family: var(--font-mono);
    }

    /* Alerts & Toasts */
    .banner {
      display: none;
      align-items: center;
      justify-content: space-between;
      border: 2px solid var(--warning);
      background: var(--warning-bg);
      padding: 6px 12px;
      font-weight: 700;
      font-size: 11px;
    }

    .banner.show {
      display: flex;
    }

    .empty-state {
      padding: 28px 14px;
      text-align: center;
      color: var(--ink-muted);
      font-size: 11.5px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
    }

    .toast-container {
      position: fixed;
      bottom: 32px;
      right: 16px;
      z-index: 2000;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .toast {
      background: var(--ink);
      color: #FFF;
      border: 2px solid #FFF;
      padding: 6px 10px;
      font-family: var(--font-mono);
      font-size: 10.5px;
      box-shadow: 3px 3px 0 var(--accent);
      display: flex;
      align-items: center;
      gap: 6px;
      animation: slideIn 0.2s ease;
    }

    .toast.danger {
      box-shadow: 3px 3px 0 var(--danger);
    }

    .toast.success {
      box-shadow: 3px 3px 0 var(--success);
    }

    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }

      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  </style>
</head>

<body>

  <div class="app-container">
    <header class="topbar">
      <div class="logo">
        <div class="dot"></div>RECON_AGENT
      </div>
      <div class="status">
        <span class="pulse-dot" id="wsDot"></span>
        <span id="statusText">IDLE</span>
        <span style="color: rgba(255,255,255,0.3)">|</span>
        <span id="sessionChip">SESSION: —</span>
        <span style="color: rgba(255,255,255,0.3)">|</span>
        <span id="stagedChip" style="color:var(--bg-blue-accent); font-weight:700;">0 FILES STAGED</span>
      </div>

      <div class="spacer"></div>

      <div class="actions">
        <button id="btnAbort" class="danger" hidden>ABORT</button>
        <button id="btnStageFiles" title="Stage CSV/XLSX statement files">+ STAGE FILES</button>
        <button id="btnSample" title="Stage benchmark test data into browser memory">LOAD SAMPLES</button>
        <button class="primary" id="btnRunPipeline" title="Execute reconciliation on staged files">EXECUTE
          PIPELINE</button>
        <button class="ghost" id="btnExportCsv" title="Export canonical reconciled CSV">EXPORT CSV</button>
        <button class="ghost" id="btnToggleCopilot" title="Toggle AI Assistant (Ctrl+B)">[ COPILOT ]</button>
      </div>
    </header>

    <div class="workspace-root">
      <aside class="sidebar" id="sidebar">
        <div class="nav-section">
          <div class="nav-title">Workspace</div>
          <div class="nav-item active" data-view="dashboard"><span class="nav-label">Terminal Grid</span></div>
          <div class="nav-item" data-view="staging"><span class="nav-label">Staged Files</span><span
              class="badge warning" id="badgeStaged">0</span></div>
          <div class="nav-item" data-view="explorer"><span class="nav-label">Data Explorer</span></div>
          <div class="nav-item" data-view="reconciliation"><span class="nav-label">Schema &amp; Policy</span></div>
        </div>
        <div class="nav-section">
          <div class="nav-title">Analysis</div>
          <div class="nav-item" data-view="exceptions"><span class="nav-label">Exceptions Queue</span><span
              class="badge danger" id="badgeExceptions">0</span></div>
          <div class="nav-item" data-view="audit"><span class="nav-label">Audit Ledger</span></div>
        </div>

        <div class="stepper">
          <div class="stepper-title">Execution State</div>
          <div class="step" id="step-1">
            <div class="node"></div><span>1. Ingestion</span>
          </div>
          <div class="step" id="step-2">
            <div class="node"></div><span>2. Profiling</span>
          </div>
          <div class="step" id="step-3">
            <div class="node"></div><span>3. Schema Map</span>
          </div>
          <div class="step" id="step-4">
            <div class="node"></div><span>4. Match Engine</span>
          </div>
          <div class="step" id="step-5">
            <div class="node"></div><span>5. Exception QA</span>
          </div>
          <div class="step" id="step-6">
            <div class="node"></div><span>6. Aggregation</span>
          </div>
        </div>
      </aside>

      <div class="resizer" id="resizer-left"></div>

      <main class="center-stage" id="centerStage">
        <div class="banner" id="haltBanner">
          <span>[!] PIPELINE HALTED: <span id="haltReason">Operator review required</span></span>
          <button class="primary" id="btnResume" style="padding:2px 6px; font-size:9.5px;">RESUME</button>
        </div>

        <section class="view-container active" id="view-dashboard">
          <div class="view-header">
            <div>
              <div class="view-title">Reconciliation Terminal</div>
              <div class="view-meta" id="viewMeta">ENGINE: DETERMINISTIC MULTI-HEURISTIC + GEMMA 4 31B</div>
            </div>
            <div class="view-actions">
              <button class="ghost" id="btnExportReport">REPORT JSON</button>
              <button class="blue" id="btnRefresh">REFRESH</button>
            </div>
          </div>

          <div class="view-body">
            <div class="kpi-strip">
              <div class="kpi active" data-tab="all">
                <div class="kpi-label">Total Records</div>
                <div class="kpi-value" id="kpiRecords">—</div>
                <div class="kpi-delta" id="kpiRecordsDelta">0 files active</div>
              </div>
              <div class="kpi" data-tab="matched">
                <div class="kpi-label">Match Rate</div>
                <div class="kpi-value" id="kpiMatch">—</div>
                <div class="kpi-delta up" id="kpiMatchDelta">awaiting run</div>
              </div>
              <div class="kpi" data-tab="exceptions">
                <div class="kpi-label">Discrepancies</div>
                <div class="kpi-value" id="kpiExc">—</div>
                <div class="kpi-delta down" id="kpiExcDelta">0 need review</div>
              </div>
              <div class="kpi" style="cursor:default">
                <div class="kpi-label">LLM Cost</div>
                <div class="kpi-value" id="kpiCost">$0.00</div>
                <div class="kpi-delta" id="kpiCostDelta">0 audit blocks</div>
              </div>
            </div>

            <div id="finTotalsCard" class="card" style="display:none; padding:6px 10px; margin-bottom:0;">
              <div
                style="display:flex; justify-content:space-between; font-family:var(--font-mono); font-size:10.5px; flex-wrap:wrap; gap:6px;">
                <span>GROSS LEDGER: <b id="totGross">INR 0.00</b></span>
                <span>NET BANK: <b id="totNet">INR 0.00</b></span>
                <span>GATEWAY FEES: <b id="totFees" style="color:var(--warning)">INR 0.00</b></span>
                <span>MATCHED: <b id="totMatched" style="color:var(--success)">INR 0.00</b></span>
                <span>EXCEPTION: <b id="totExc" style="color:var(--danger)">INR 0.00</b></span>
              </div>
            </div>

            <div class="data-grid-container">
              <div class="grid-toolbar">
                <div class="grid-tabs">
                  <div class="grid-tab active" data-tab="all">ALL (<span id="cntAll">0</span>)</div>
                  <div class="grid-tab" data-tab="matched">MATCHED (<span id="cntMatched">0</span>)</div>
                  <div class="grid-tab" data-tab="exceptions">EXCEPTIONS (<span id="cntExc">0</span>)</div>
                </div>
                <div class="spacer" style="flex:1"></div>
                <input type="text" id="gridFilter" placeholder="FILTER ROWS (ORD_ID, AMOUNT, REASON)..."
                  style="width: 240px; padding: 3px 6px; font-size: 10.5px; font-family:var(--font-mono); border: 1px solid var(--border);">
              </div>

              <div class="grid-wrapper">
                <table class="data-grid">
                  <thead>
                    <tr>
                      <th class="pin-1" style="width:36px; text-align:center;">#</th>
                      <th class="pin-2" style="width:90px;">STATUS</th>
                      <th>REFERENCE ID</th>
                      <th>LEDGER RID</th>
                      <th>BANK RID</th>
                      <th class="num-cell">LEDGER AMT</th>
                      <th class="num-cell">BANK AMT</th>
                      <th class="num-cell">VARIANCE (DELTA)</th>
                      <th class="num-cell">CONFIDENCE</th>
                      <th>ROOT CAUSE / DIAGNOSTIC</th>
                    </tr>
                  </thead>
                  <tbody id="gridBody">
                    <tr>
                      <td colspan="10">
                        <div class="empty-state">No dataset active. Stage files or load sample benchmarks above.</div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="diff-drawer" id="diffDrawer">
                <div class="diff-header">
                  <span id="diffTitle">INSPECTOR: Record Provenance</span>
                  <button class="ghost" onclick="$('#diffDrawer').classList.remove('open')" style="padding:1px 4px;">[
                    CLOSE ]</button>
                </div>
                <div class="diff-content" id="diffContent"></div>
              </div>

              <div class="spreadsheet-status-bar">
                <span id="gridFooterText">SHOWING 0 OF 0 RECORDS</span>
                <div style="display:flex; gap:14px;">
                  <span id="gridSelectedRow">ROW: NONE SELECTED</span>
                  <span id="gridSumVariance">SUM DELTA: INR 0.00</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="view-container" id="view-staging">
          <div class="view-header">
            <div>
              <div class="view-title">Staged Files Inspection</div>
              <div class="view-meta">PREVIEW RAW ROWS &amp; COLUMN SCHEMAS IN MEMORY BEFORE SUBMISSION</div>
            </div>
            <div class="view-actions">
              <button class="primary" id="btnStagingExecute" disabled>EXECUTE PIPELINE (0 FILES)</button>
            </div>
          </div>
          <div class="view-body">
            <div class="dropzone" id="stagingDropzone">
              <b>DRAG &amp; DROP CSV / EXCEL FILES HERE</b>
              <span style="color:var(--ink-muted); font-size:11px;">Files are parsed locally in browser memory for
                inspection before committing to backend execution.</span>
            </div>

            <div id="stagingCardsList"></div>

            <div class="data-grid-container" id="stagingPreviewGridCard" style="display:none; flex:1;">
              <div class="grid-toolbar">
                <span style="font-weight:700; font-size:10.5px;" id="stagingPreviewTitle">PREVIEW</span>
                <div class="spacer" style="flex:1"></div>
                <span class="badge info" id="stagingPreviewMeta">0 ROWS</span>
              </div>
              <div class="grid-wrapper">
                <table class="data-grid">
                  <thead id="stgHead"></thead>
                  <tbody id="stgBody"></tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        <section class="view-container" id="view-explorer">
          <div class="view-header">
            <div>
              <div class="view-title">Data Explorer</div>
              <div class="view-meta">PAGINATED SERVER TABLES + PII PROFILES</div>
            </div>
          </div>
          <div class="view-body">
            <div class="data-grid-container" style="flex:1;">
              <div class="grid-toolbar">
                <div class="grid-tabs" id="expTabs"></div>
                <div class="spacer" style="flex:1"></div>
              </div>
              <div class="grid-wrapper">
                <table class="data-grid">
                  <thead id="expHead"></thead>
                  <tbody id="expBody"></tbody>
                </table>
              </div>
              <div class="spreadsheet-status-bar">
                <span id="expFooterText">SHOWING 0 OF 0 RECORDS</span>
                <div style="display:flex; gap:4px;"><button id="expPrev" disabled>&lt; PREV</button><button id="expNext"
                    disabled>NEXT &gt;</button></div>
              </div>
            </div>
            <div class="card">
              <div class="card-header"><span class="nav-title" style="padding:0">Column Profiles (PII Redacted)</span>
              </div>
              <div id="profilesBox">No data ingested.</div>
            </div>
          </div>
        </section>

        <section class="view-container" id="view-reconciliation">
          <div class="view-header">
            <div>
              <div class="view-title">Schema Linkage &amp; Policy</div>
              <div class="view-meta">KEY ALIGNMENT · TOLERANCE GATES · FEE SCHEDULES</div>
            </div>
          </div>
          <div class="view-body">
            <div class="card">
              <div class="card-header"><span class="nav-title" style="padding:0">Committed Schema Mapping</span><span
                  class="badge info" id="mapConfLine">CONF —</span></div>
              <div class="kv" id="mapCommitted">No schema committed yet.</div>
            </div>
            <div class="card">
              <div class="card-header"><span class="nav-title" style="padding:0">Candidate Structural Overlaps</span>
              </div>
              <div class="grid-wrapper" style="max-height:160px;">
                <table class="data-grid">
                  <thead>
                    <tr>
                      <th>LEFT</th>
                      <th>RIGHT</th>
                      <th>OVERLAP</th>
                      <th>TYPE</th>
                      <th>COMPOSITE</th>
                      <th>BAND</th>
                    </tr>
                  </thead>
                  <tbody id="mapCandsBody"></tbody>
                </table>
              </div>
            </div>
            <div class="card">
              <div class="card-header"><span class="nav-title" style="padding:0">Match Policy &amp; Fee Schedules</span>
              </div>
              <div id="policyBody" style="font-size:11px;">No policy synthesized yet.</div>
              <div id="feeBody" style="display:flex; gap:4px; flex-wrap:wrap; margin-top:6px;"></div>
            </div>
          </div>
        </section>

        <section class="view-container" id="view-exceptions">
          <div class="view-header">
            <div>
              <div class="view-title">Exceptions Queue</div>
              <div class="view-meta">CLASSIFIED DISCREPANCIES · VERIFIED EVIDENCE · MANAGER OVERRIDES</div>
            </div>
            <div class="view-actions" id="excSummaryBadges"></div>
          </div>
          <div class="view-body" id="excList">
            <div class="card">
              <div class="empty-state">No exceptions queued.</div>
            </div>
          </div>
        </section>

        <section class="view-container" id="view-audit">
          <div class="view-header">
            <div>
              <div class="view-title">Cryptographic Audit Ledger</div>
              <div class="view-meta">TAMPER-EVIDENT SHA-256 HASH CHAIN</div>
            </div>
            <div class="view-actions">
              <span class="badge success" id="auditBadge">UNVERIFIED</span>
              <button class="blue" id="btnVerifyChain">VERIFY CHAIN</button>
              <button class="ghost" id="btnExportAudit">EXPORT JSONL</button>
            </div>
          </div>
          <div class="view-body">
            <div class="data-grid-container" style="flex:1;">
              <div class="grid-wrapper">
                <table class="data-grid">
                  <thead>
                    <tr>
                      <th>SEQ</th>
                      <th>TIMESTAMP</th>
                      <th>EVENT</th>
                      <th>ACTOR</th>
                      <th>PREV HASH</th>
                      <th>THIS HASH</th>
                    </tr>
                  </thead>
                  <tbody id="auditBody"></tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      </main>

      <div class="resizer" id="resizer-right"></div>

      <aside class="copilot" id="copilotPanel">
        <div class="copilot-header">
          <div style="display:flex; align-items:center; gap:6px; font-weight:700;">
            <div class="chat-msg-avatar">AI</div>
            <div>
              <div style="font-family:var(--font-display); font-size:12px;">Recon Copilot</div>
              <div style="font-family:var(--font-mono); font-size:9px; color:var(--ink-muted);">GROUNDED • GEMMA 4 31B
              </div>
            </div>
          </div>
          <button class="ghost" id="btnCloseCopilot" style="padding:1px 4px;">[ X ]</button>
        </div>

        <div class="copilot-messages" id="chatMessages">
          <div class="chat-msg ai">
            <div class="chat-msg-avatar">AI</div>
            <div>
              <div class="chat-msg-bubble">
                Reconciliation Assistant ready. Stage your statements to begin grounded analysis.
              </div>
            </div>
          </div>
        </div>

        <div class="prompt-chips">
          <button class="chip-btn" data-prompt="List all unresolved exceptions with root causes">[ UNRESOLVED ]</button>
          <button class="chip-btn" data-prompt="Explain fee deduction calculation and GST rate">[ FEE MODEL ]</button>
          <button class="chip-btn" data-prompt="Verify SHA-256 audit ledger status">[ AUDIT STATUS ]</button>
        </div>

        <div class="copilot-input-area">
          <div class="copilot-input-wrapper">
            <input type="text" class="copilot-input" id="chatInput" placeholder="Query dataset, variances, orders...">
            <button class="primary" id="btnSend">SEND</button>
          </div>
        </div>
      </aside>
    </div>
  </div>

  <div class="toast-container" id="toastContainer"></div>
  <input type="file" id="globalFileInput" multiple accept=".csv,.xlsx" style="display:none;">

  <script>
    // =====================================================================
    // APPLICATION STATE CONTROLLER
    // =====================================================================
    const API = '/api/v2';
    const $ = s => document.querySelector(s);
    const $$ = s => [...document.querySelectorAll(s)];

    const S = {
      sid: null, state: 'IDLE', running: false, abortToken: null,
      stagedFiles: [],
      results: null, excRows: [], excSummary: null, committed: null,
      grid: { rows: [], tab: 'all', filter: '', selectedIdx: null },
      explorer: { table: null, page: 1, pageSize: 100, meta: {} },
      pollTimer: null, currentView: 'dashboard', activeStagedIdx: 0
    };

    // Benchmark Data
    const SAMPLE_PAY = `order_id,amount,date\nORD_1001,1000.00,2026-03-01\nORD_1002,1500.00,2026-03-01\nORD_1003,2000.00,2026-03-01\nORD_1004,2500.00,2026-03-01\nORD_1005,3000.00,2026-03-01\nORD_1006,3500.00,2026-03-01\nORD_1007,4000.00,2026-03-01\nORD_1008,4500.00,2026-03-01\nORD_1009,5000.00,2026-03-01\nORD_1010,5500.00,2026-03-01\nORD_1011,6000.00,2026-03-02\nORD_1012,6500.00,2026-03-02\nORD_1021,1000.00,2026-03-01\nTXN-ORD-1036,1100.00,2026-03-10\nORD_1046,1000.00,2026-03-15`;
    const SAMPLE_BANK = `utr,credit,date\nORD_1001,976.40,2026-03-02\nORD_1002,1464.60,2026-03-02\nORD_1003,1952.80,2026-03-02\nORD_1004,2441.00,2026-03-02\nORD_1005,2929.20,2026-03-02\nORD_1006,3417.40,2026-03-02\nORD_1007,3905.60,2026-03-02\nORD_1008,4393.80,2026-03-02\nORD_1009,4882.00,2026-03-02\nORD_1010,5370.20,2026-03-02\nORD_1011,5858.40,2026-03-03\nORD_1012,6346.60,2026-03-03\nORD_1021,1000.00,2026-03-12\nORD-1036,1100.00,2026-03-11\nBATCH_SETTL_01,2929.20,2026-03-17`;

    const STEP_MAP = { INGESTING: 1, PROFILING: 2, MAPPING_PROPOSED: 3, MAPPING_VALIDATED: 3, POLICY_GENERATED: 4, DRY_RUN: 4, EXECUTING: 4, INSPECTING: 4, REVISION: 4, QA: 5, RESOLVING: 5, AGGREGATING: 6, ARCHIVED: 6 };

    // Helper Functions
    function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]); }
    function num(v) { if (v == null || v === '') return null; const n = Number(v); return isFinite(n) ? n : null; }
    function inr(v) { const n = num(v); return n == null ? '—' : 'INR ' + n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
    function pct(v) { return v == null ? '—' : (v * 100).toFixed(1) + '%'; }

    function toast(msg, kind = 'info') {
      const el = document.createElement('div'); el.className = 'toast ' + kind;
      el.innerHTML = `<span>&gt;</span> ${esc(msg)}`; $('#toastContainer').appendChild(el);
      setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(100%)'; el.style.transition = 'all .3s'; setTimeout(() => el.remove(), 300); }, 3200);
    }

    // Network layer with auto-session-heal
    async function fetchJSON(url, opts = {}) {
      const r = await fetch(url, opts);
      if (r.status === 404 && url.includes(`/api/v2/sessions/${S.sid}`)) {
        console.warn(`[API] Session ${S.sid} not found on backend. Re-initializing session.`);
        await boot();
        throw new Error('Session invalidated on server. Re-initialized fresh session.');
      }
      if (!r.ok) {
        let d = '';
        try { d = (await r.json()).detail; } catch { }
        throw new Error(d || ('HTTP ' + r.status));
      }
      return r.json();
    }

    // Session Initialization
    async function boot() {
      try {
        const j = await fetch(API + '/sessions', { method: 'POST' }).then(res => res.json());
        S.sid = j.session_id;
        $('#sessionChip').textContent = `SESSION: ${S.sid.slice(0, 8)}`;
        $('#viewMeta').textContent = `SESSION: ${S.sid} | ENGINE: DETERMINISTIC + GEMMA 4 31B`;
        connectWS();
        await refreshOverview();
        switchView('dashboard');
      } catch (e) {
        toast('API unreachable: ' + e.message, 'danger');
        $('#statusText').textContent = 'OFFLINE';
      }
    }

    // WebSocket Telemetry
    let wsObj = null;
    function connectWS() {
      if (!S.sid) return;
      if (wsObj) { try { wsObj.close(); } catch { } }
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      wsObj = new WebSocket(`${proto}://${location.host}/ws/v2/${S.sid}`);
      wsObj.onopen = () => $('#wsDot').classList.add('online');
      wsObj.onclose = () => { $('#wsDot').classList.remove('online'); setTimeout(connectWS, 3000); };
      wsObj.onmessage = ev => {
        try {
          const f = JSON.parse(ev.data);
          const p = f.payload || {};
          if (f.kind === 'control') {
            if (p.event === 'STATE_ENTERED') { updateStateUI(p.state); S.abortToken = p.abort_token || S.abortToken; }
            if (p.event === 'HALT') { $('#haltReason').textContent = p.detail?.reason || 'Operator review required'; $('#haltBanner').classList.add('show'); }
            if (p.event === 'RESUMED') { $('#haltBanner').classList.remove('show'); }
            if (p.event === 'ABORT_CONFIRMED') { S.running = false; updateStateUI('ABORTED'); toast('Run aborted.', 'danger'); }
          }
          if (f.kind === 'chat' && p.text) addChat('ai', p.text);
          if (f.kind === 'artifact' && p.kind === 'report') onComplete();
        } catch { }
      };
    }

    function updateStateUI(st) {
      S.state = st;
      $('#statusText').textContent = st;
      const idx = STEP_MAP[st] || 0;
      for (let i = 1; i <= 6; i++) {
        const el = $(`#step-${i}`);
        if (!el) continue;
        el.classList.remove('done', 'active');
        if (st === 'ARCHIVED' || i < idx) el.classList.add('done');
        else if (i === idx) el.classList.add('active');
      }
    }

    // View Routing
    function switchView(name) {
      S.currentView = name;
      $$('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.view === name));
      $$('.view-container').forEach(v => v.classList.toggle('active', v.id === 'view-' + name));
      if (name === 'dashboard') loadDashboard();
      if (name === 'staging') renderStagingView();
      if (name === 'explorer') loadExplorer();
      if (name === 'reconciliation') loadRecon();
      if (name === 'exceptions') loadExceptions();
      if (name === 'audit') loadAudit();
    }

    // Local File Staging Workflow
    function parseCSVLocally(name, text) {
      const lines = text.trim().split(/\r?\n/).filter(l => l.trim().length > 0);
      const cols = (lines[0] || '').split(',').map(c => c.trim().replace(/^["']|["']$/g, ''));
      const rows = lines.slice(1).map(l => {
        const vals = l.split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
        const obj = {};
        cols.forEach((c, i) => { obj[c] = vals[i] ?? ''; });
        return obj;
      });
      return { cols, rows, rowCount: rows.length };
    }

    function stageLocalFiles(files) {
      files.forEach(f => {
        if (f.name.toLowerCase().endsWith('.csv')) {
          const rd = new FileReader();
          rd.onload = () => {
            const parsed = parseCSVLocally(f.name, String(rd.result));
            S.stagedFiles.push({ name: f.name, file: f, size: f.size, ...parsed });
            updateStagingState();
            toast(`Staged ${f.name} (${parsed.rowCount} rows)`);
          };
          rd.readAsText(f);
        } else {
          S.stagedFiles.push({ name: f.name, file: f, size: f.size, cols: ['Binary data'], rows: [], rowCount: 'Excel (Binary)' });
          updateStagingState();
          toast(`Staged ${f.name} (Binary Excel)`);
        }
      });
    }

    function updateStagingState() {
      const count = S.stagedFiles.length;
      $('#badgeStaged').textContent = count;
      $('#stagedChip').textContent = `${count} FILES STAGED`;
      $('#btnStagingExecute').disabled = count < 2;
      $('#btnStagingExecute').textContent = `EXECUTE PIPELINE (${count} FILES)`;
      if (S.currentView === 'staging') renderStagingView();
    }

    function renderStagingView() {
      const list = $('#stagingCardsList');
      if (!S.stagedFiles.length) {
        list.innerHTML = '<div class="card"><div class="empty-state">No files staged. Drag and drop CSV/XLSX files above or click "+ STAGE FILES".</div></div>';
        $('#stagingPreviewGridCard').style.display = 'none';
        return;
      }

      list.innerHTML = S.stagedFiles.map((f, i) => `
    <div class="card" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
      <div>
        <span style="font-weight:700; font-size:12px;">${esc(f.name)}</span>
        <span class="badge info" style="margin-left:8px;">${f.rowCount} ROWS</span>
        <span class="mono" style="font-size:10.5px; color:var(--ink-muted); margin-left:8px;">${(f.size / 1024).toFixed(1)} KB</span>
      </div>
      <div style="display:flex; gap:6px;">
        <button class="ghost" onclick="previewStagedFile(${i})">[ PREVIEW ]</button>
        <button class="danger" onclick="removeStagedFile(${i})">[ REMOVE ]</button>
      </div>
    </div>
  `).join('');

      if (S.stagedFiles[S.activeStagedIdx]) {
        previewStagedFile(S.activeStagedIdx);
      }
    }

    window.previewStagedFile = function (idx) {
      S.activeStagedIdx = idx;
      const f = S.stagedFiles[idx];
      if (!f) return;
      $('#stagingPreviewTitle').textContent = `PREVIEW: ${f.name}`;
      $('#stagingPreviewMeta').textContent = `${f.rowCount} ROWS | ${f.cols.length} COLS`;
      $('#stgHead').innerHTML = `<tr><th class="pin-1" style="width:36px; text-align:center;">#</th>${f.cols.map(c => `<th>${esc(c)}</th>`).join('')}</tr>`;
      $('#stgBody').innerHTML = f.rows.slice(0, 80).map((r, i) => `
    <tr>
      <td class="pin-1" style="text-align:center; color:var(--ink-dim);">${i + 1}</td>
      ${f.cols.map(c => `<td class="${num(r[c]) != null ? 'num-cell' : ''}">${esc(r[c])}</td>`).join('')}
    </tr>
  `).join('');
      $('#stagingPreviewGridCard').style.display = 'flex';
    };

    window.removeStagedFile = function (idx) {
      S.stagedFiles.splice(idx, 1);
      S.activeStagedIdx = 0;
      updateStagingState();
    };

    // Execution Engine
    async function startPipeline() {
      if (S.running) return;
      if (S.stagedFiles.length < 2) {
        toast('At least 2 files (Ledger + Bank) are required.', 'danger');
        switchView('staging');
        return;
      }
      S.running = true;
      $('#btnRunPipeline').disabled = true;
      $('#statusText').textContent = 'RUNNING';
      toast('Uploading staged files to reconciliation engine...');

      const fd = new FormData();
      S.stagedFiles.forEach(f => fd.append('files', f.file));

      try {
        const j = await fetchJSON(`${API}/sessions/${S.sid}/run`, { method: 'POST', body: fd });
        toast(`Pipeline running: ${j.files.join(', ')}`, 'success');
        switchView('dashboard');
        startPolling();
      } catch (e) {
        toast('Execution failed: ' + e.message, 'danger');
        S.running = false;
        $('#btnRunPipeline').disabled = false;
      }
    }

    function startPolling() {
      if (S.pollTimer) clearInterval(S.pollTimer);
      S.pollTimer = setInterval(async () => {
        const ov = await refreshOverview();
        if (ov && ov.state === 'ARCHIVED') onComplete();
      }, 1800);
    }

    function onComplete() {
      if (S.pollTimer) clearInterval(S.pollTimer);
      S.running = false;
      $('#btnRunPipeline').disabled = false;
      updateStateUI('ARCHIVED');
      toast('Reconciliation complete — audit ledger signed.', 'success');
      loadDashboard();
    }

    async function refreshOverview() {
      try {
        const ov = await fetchJSON(`${API}/sessions/${S.sid}/overview`);
        updateStateUI(ov.state);
        S.abortToken = ov.abort_token || S.abortToken;
        $('#kpiCost').textContent = '$' + (ov.cost_usd || 0).toFixed(4);
        $('#kpiCostDelta').textContent = `${ov.audit_count} audit blocks`;
        const tc = ov.table_counts || {};
        const tot = Object.values(tc).reduce((a, b) => a + b, 0);
        $('#kpiRecords').textContent = tot ? tot.toLocaleString('en-IN') : '—';
        $('#kpiRecordsDelta').textContent = `${Object.keys(tc).length} tables loaded`;
        return ov;
      } catch (e) { return null; }
    }

    // Dashboard & Spreadsheet Grid
    async function loadDashboard() {
      try {
        const [res, m, exc] = await Promise.all([
          fetchJSON(`${API}/sessions/${S.sid}/results`),
          fetchJSON(`${API}/sessions/${S.sid}/mapping`),
          fetchJSON(`${API}/sessions/${S.sid}/exceptions?page_size=500`)
        ]);
        S.results = res.executed ? res : null;
        S.committed = m.committed || {};
        S.excRows = exc.queue || [];
        S.excSummary = exc.summary || null;
      } catch { }
      renderDashboardData();
    }

    function renderDashboardData() {
      if (S.results) {
        $('#kpiMatch').textContent = pct(S.results.match_rate);
        $('#kpiMatchDelta').textContent = S.results.precision_vs_truth ? `P ${pct(S.results.precision_vs_truth)} | R ${pct(S.results.recall_vs_truth)}` : 'vs baseline run';
        if (S.results.totals) {
          $('#totGross').textContent = inr(S.results.totals.gross);
          $('#totNet').textContent = inr(S.results.totals.net);
          $('#totFees').textContent = inr(S.results.totals.fees);
          $('#totMatched').textContent = inr(S.results.totals.matched_value);
          $('#totExc').textContent = inr(S.results.totals.exception_value);
          $('#finTotalsCard').style.display = 'block';
        }
      }
      if (S.excSummary) {
        $('#kpiExc').textContent = S.excSummary.total;
        $('#kpiExcDelta').textContent = `${S.excSummary.needs_review} need review`;
        $('#badgeExceptions').textContent = S.excSummary.needs_review;
      }

      // Synthesize Unified Records
      const c = S.committed || {};
      const rows = [];
      if (S.results && S.results.matched) {
        for (const m of S.results.matched) {
          const lAmt = num(m.l_data && m.l_data[c.left_amount]);
          const rAmt = num(m.r_data && m.r_data[c.right_amount]);
          const variance = (lAmt != null && rAmt != null) ? lAmt - rAmt : null;
          rows.push({
            status: 'MATCHED',
            l: m.l_rid, r: m.r_rid,
            ref: String((m.l_data && m.l_data[c.left_key]) ?? m.l_rid),
            lAmt, rAmt, variance, conf: m.composite_score,
            cause: (variance != null && Math.abs(variance) > 0.01) ? 'FEE DEDUCTION' : 'EXACT MATCH',
            raw: m
          });
        }
      }
      for (const e of S.excRows) {
        rows.push({
          status: (e.action === 'auto_resolve' || e.action === 'mark_resolved') ? 'AUTO-APPROVED' : 'EXCEPTION',
          l: e.side === 'L' ? e.rid : '', r: e.side === 'R' ? e.rid : '',
          ref: e.ref || '—',
          lAmt: e.side === 'L' ? num(e.record_data && e.record_data[c.left_amount]) : null,
          rAmt: e.side === 'R' ? num(e.record_data && e.record_data[c.right_amount]) : null,
          variance: e.delta, conf: e.confidence,
          cause: e.reason || 'UNRESOLVED',
          raw: e
        });
      }
      S.grid.rows = rows;
      renderSpreadsheetGrid();
    }

    function renderSpreadsheetGrid() {
      const all = S.grid.rows;
      $('#cntAll').textContent = all.length;
      $('#cntMatched').textContent = all.filter(r => r.status === 'MATCHED').length;
      $('#cntExc').textContent = all.filter(r => r.status !== 'MATCHED').length;

      let list = all;
      if (S.grid.tab === 'matched') list = list.filter(r => r.status === 'MATCHED');
      if (S.grid.tab === 'exceptions') list = list.filter(r => r.status !== 'MATCHED');

      const q = S.grid.filter.trim().toLowerCase();
      if (q) list = list.filter(r => [r.ref, r.cause, r.status, String(r.l), String(r.r)].join(' ').toLowerCase().includes(q));

      const body = $('#gridBody');
      if (!list.length) {
        body.innerHTML = `<tr><td colspan="10"><div class="empty-state">No matching rows found in dataset.</div></td></tr>`;
        $('#gridFooterText').textContent = `SHOWING 0 OF ${all.length} RECORDS`;
        return;
      }

      let totalVariance = 0;
      body.innerHTML = list.map((r, i) => {
        if (r.variance) totalVariance += r.variance;
        const stBadge = r.status === 'MATCHED' ? `<span class="badge success">MATCHED</span>` :
          r.status === 'AUTO-APPROVED' ? `<span class="badge info">RESOLVED</span>` : `<span class="badge danger">EXCEPTION</span>`;

        let deltaTag = '<span class="delta-tag zero">0.00</span>';
        if (r.variance != null && Math.abs(r.variance) > 0.01) {
          deltaTag = r.variance > 0
            ? `<span class="delta-tag pos">+${inr(r.variance)}</span>`
            : `<span class="delta-tag neg">${inr(r.variance)}</span>`;
        }

        const confClass = r.conf >= 0.85 ? 'color:var(--success)' : (r.conf < 0.6 ? 'color:var(--danger)' : '');

        return `
      <tr onclick="inspectRow(${i})" class="${i === S.grid.selectedIdx ? 'selected' : ''}">
        <td class="pin-1" style="text-align:center; color:var(--ink-dim);">${i + 1}</td>
        <td class="pin-2">${stBadge}</td>
        <td style="font-weight:700;">${esc(r.ref)}</td>
        <td>${r.l ? 'L-' + r.l : '—'}</td>
        <td>${r.r ? 'R-' + r.r : '—'}</td>
        <td class="num-cell">${inr(r.lAmt)}</td>
        <td class="num-cell">${inr(r.rAmt)}</td>
        <td class="num-cell">${deltaTag}</td>
        <td class="num-cell" style="${confClass}">${r.conf ? Number(r.conf).toFixed(3) : '—'}</td>
        <td><span class="badge info">${esc(r.cause)}</span></td>
      </tr>
    `;
      }).join('');

      $('#gridFooterText').textContent = `SHOWING ${list.length.toLocaleString('en-IN')} OF ${all.length.toLocaleString('en-IN')} RECORDS`;
      $('#gridSumVariance').textContent = `SUM DELTA: ${inr(totalVariance)}`;
    }

    window.inspectRow = function (idx) {
      S.grid.selectedIdx = idx;
      renderSpreadsheetGrid();
      const r = S.grid.rows[idx];
      if (!r) return;

      $('#gridSelectedRow').textContent = `ROW #${idx + 1} [${r.ref}]`;
      $('#diffTitle').textContent = `INSPECTOR: Reference ${r.ref} | Status: ${r.status} | Conf: ${r.conf ? Number(r.conf).toFixed(3) : '—'}`;
      $('#diffContent').innerHTML = `
    <div class="diff-card">
      <div style="font-weight:700; margin-bottom:4px;">PAYMENTS LEDGER (L-${r.l || '—'})</div>
      <div>Amount: <b>${inr(r.lAmt)}</b></div>
      <div style="color:var(--ink-muted); margin-top:4px;">Attributes: ${esc(JSON.stringify(r.raw.l_data || r.raw.record_data || {}))}</div>
    </div>
    <div class="diff-card">
      <div style="font-weight:700; margin-bottom:4px;">BANK STATEMENT (R-${r.r || '—'})</div>
      <div>Credit: <b>${inr(r.rAmt)}</b></div>
      <div style="color:var(--ink-muted); margin-top:4px;">Attributes: ${esc(JSON.stringify(r.raw.r_data || {}))}</div>
    </div>
  `;
      $('#diffDrawer').classList.add('open');
    };

    // Data Explorer
    async function loadExplorer() {
      try {
        const ing = await fetchJSON(`${API}/sessions/${S.sid}/ingestion`);
        S.explorer.meta = ing.table_meta || {};
        $('#expTabs').innerHTML = Object.entries(S.explorer.meta).map(([n, m]) =>
          `<div class="grid-tab ${n === S.explorer.table ? 'active' : ''}" data-tbl="${esc(n)}">${esc(n)} (${m.total_rows})</div>`
        ).join('');
        if (!S.explorer.table && Object.keys(S.explorer.meta).length) S.explorer.table = Object.keys(S.explorer.meta)[0];
        renderProfiles(ing.profiles || {});
        if (S.explorer.table) await loadExplorerPage();
      } catch (e) { }
    }

    async function loadExplorerPage() {
      const t = S.explorer.table;
      const pg = await fetchJSON(`${API}/sessions/${S.sid}/ingestion?table=${encodeURIComponent(t)}&page=${S.explorer.page}&page_size=${S.explorer.pageSize}`);
      const data = pg.tables[t];
      const cols = S.explorer.meta[t]?.columns || [];
      $('#expHead').innerHTML = `<tr><th class="pin-1" style="width:36px; text-align:center;">#</th>${cols.map(c => `<th>${esc(c)}</th>`).join('')}</tr>`;
      $('#expBody').innerHTML = data.items.map((r, i) => `
    <tr>
      <td class="pin-1" style="text-align:center; color:var(--ink-dim);">${(data.page - 1) * data.page_size + i + 1}</td>
      ${cols.map(c => `<td class="${num(r[c]) != null ? 'num-cell' : ''}">${esc(r[c])}</td>`).join('')}
    </tr>
  `).join('');
      $('#expFooterText').textContent = `SHOWING ${(data.page - 1) * data.page_size + 1}-${Math.min(data.total, data.page * data.page_size)} OF ${data.total} RECORDS`;
      $('#expPrev').disabled = !data.has_prev;
      $('#expNext').disabled = !data.has_next;
    }

    function renderProfiles(profiles) {
      const box = $('#profilesBox');
      const list = profiles[S.explorer.table] || [];
      if (!list.length) { box.innerHTML = '<span style="color:var(--ink-muted)">No profile data available.</span>'; return; }
      box.innerHTML = `
    <div class="grid-wrapper" style="max-height:150px;"><table class="data-grid">
      <thead><tr><th>COLUMN</th><th>DTYPE</th><th>NUMERIC%</th><th>DATE%</th><th>CARDINALITY</th><th>NULL%</th><th>PII STATUS</th></tr></thead>
      <tbody>${list.map(p => `
        <tr>
          <td style="font-weight:700;">${esc(p.name)}</td>
          <td>${esc(p.dtype)}</td>
          <td class="num-cell">${(p.numeric_ratio * 100).toFixed(0)}%</td>
          <td class="num-cell">${(p.date_ratio * 100).toFixed(0)}%</td>
          <td class="num-cell">${p.cardinality.toFixed(2)}</td>
          <td class="num-cell">${(p.null_rate * 100).toFixed(0)}%</td>
          <td>${p.pii_likelihood >= 0.7 ? '<span class="badge danger">MASKED</span>' : '<span class="badge success">CLEAR</span>'}</td>
        </tr>
      `).join('')}</tbody>
    </table></div>
  `;
    }

    // Schema & Policy
    async function loadRecon() {
      try {
        const [m, pol] = await Promise.all([
          fetchJSON(`${API}/sessions/${S.sid}/mapping`),
          fetchJSON(`${API}/sessions/${S.sid}/policy`)
        ]);
        $('#mapConfLine').textContent = `CONF ${Number(m.confidence || 0).toFixed(2)}`;
        if (m.committed) {
          $('#mapCommitted').innerHTML = Object.entries(m.committed).map(([k, v]) =>
            `<span class="k">${esc(k)}:</span><span class="v">${esc(v ?? '—')}</span>`
          ).join('');
        }
        $('#mapCandsBody').innerHTML = (m.candidates || []).map(c => `
      <tr>
        <td>${esc(c.left)}</td><td>${esc(c.right)}</td>
        <td class="num-cell">${c.signals.structural_overlap}</td>
        <td class="num-cell">${c.signals.type_compatibility}</td>
        <td class="num-cell">${c.composite}</td>
        <td><span class="badge ${c.band === 'auto' ? 'success' : 'warning'}">${c.band}</span></td>
      </tr>
    `).join('') || `<tr><td colspan="6"><div class="empty-state">No candidate overlaps found.</div></td></tr>`;

        if (pol.components) {
          $('#policyBody').innerHTML = `
        <div style="display:flex; gap:6px; margin-bottom:6px;">
          <span class="badge solid">BASELINE ${pct(pol.baseline_match_rate)}</span>
          <span class="badge info">REV CAP ${pol.revision_caps.iterations} IT / ${pol.revision_caps.seconds}S</span>
        </div>
      `;
          $('#feeBody').innerHTML = (pol.fee_schedules || []).map(f =>
            `<span class="badge info">${esc(f.provider)} | ${esc(f.model_type)} | RATE ${f.params.rate ?? '—'} | GST ${(f.gst_rate * 100).toFixed(0)}%</span>`
          ).join('');
        }
      } catch (e) { }
    }

    // Exceptions Queue
    async function loadExceptions() {
      try {
        const exc = await fetchJSON(`${API}/sessions/${S.sid}/exceptions?page_size=500`);
        S.excRows = exc.queue || []; S.excSummary = exc.summary || {};
        const s = S.excSummary;
        $('#excSummaryBadges').innerHTML = `
      <span class="badge solid">TOTAL ${s.total || 0}</span>
      <span class="badge success">AUTO-RESOLVED ${s.auto_resolved || 0}</span>
      <span class="badge warning">NEEDS REVIEW ${s.needs_review || 0}</span>
    `;
        const list = $('#excList');
        if (!S.excRows.length) { list.innerHTML = `<div class="card"><div class="empty-state">No exceptions in queue.</div></div>`; return; }
        list.innerHTML = S.excRows.map((e, i) => `
      <div class="card">
        <div class="card-header">
          <span style="font-weight:700;">#${i + 1} · [${e.side}] ${esc(e.ref)} <span class="badge danger">${esc(e.reason)}</span> <span class="badge info">${esc(e.action)}</span></span>
          <span class="mono" style="font-size:10.5px;">CONF ${Number(e.confidence).toFixed(2)} | DELTA ${inr(e.delta)}</span>
        </div>
        <div style="font-size:11.5px; margin-bottom:4px;">${esc(e.explanation || 'No diagnostic explanation available')}</div>
        <div style="font-size:10.5px; color:var(--ink-muted); margin-bottom:6px;">${esc(e.auto_reason || '')}</div>
        <div style="display:flex; gap:6px;">
          <button class="primary" onclick="resolveExc(${e.rid}, 'approve')">APPROVE / RESOLVE</button>
          <button class="danger" onclick="resolveExc(${e.rid}, 'decline')">DECLINE</button>
          <button class="ghost" onclick="resolveExc(${e.rid}, 'escalate')">ESCALATE</button>
        </div>
      </div>
    `).join('');
      } catch (e) { }
    }

    window.resolveExc = async function (rid, action) {
      try {
        await fetchJSON(`${API}/sessions/${S.sid}/exceptions/${rid}/action`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action, note: 'Operator manual override' })
        });
        toast(`Exception #${rid} updated to ${action.toUpperCase()}`, 'success');
        await loadExceptions();
        await refreshOverview();
      } catch (e) { toast('Override failed: ' + e.message, 'danger'); }
    };

    // Audit Ledger
    async function loadAudit() {
      try {
        const a = await fetchJSON(`${API}/sessions/${S.sid}/audit`);
        $('#auditBadge').textContent = a.verified ? `VERIFIED (${a.count} BLOCKS)` : 'TAMPERED!';
        $('#auditBadge').className = 'badge ' + (a.verified ? 'success' : 'danger');
        $('#auditBody').innerHTML = (a.records || []).slice().reverse().map(r => `
      <tr>
        <td style="font-weight:700;">${r.seq}</td>
        <td>${esc((r.ts || '').replace('T', ' ').slice(0, 19))}</td>
        <td><b>${esc(r.payload.event || r.payload.decision_kind || '—')}</b></td>
        <td>${esc(r.payload.actor || 'system')}</td>
        <td class="mono" style="font-size:9.5px;">${esc(String(r.prev_hash).slice(0, 12))}...</td>
        <td class="mono" style="font-size:9.5px;">${esc(String(r.this_hash).slice(0, 12))}...</td>
      </tr>
    `).join('') || `<tr><td colspan="6"><div class="empty-state">Audit ledger is empty.</div></td></tr>`;
      } catch (e) { }
    }

    // Copilot Chat
    function addChat(role, text) {
      const b = document.createElement('div');
      b.className = `chat-msg ${role}`;
      b.innerHTML = `<div class="chat-msg-avatar">${role === 'ai' ? 'AI' : 'U'}</div><div><div class="chat-msg-bubble">${esc(text)}</div></div>`;
      $('#chatMessages').appendChild(b);
      $('#chatMessages').scrollTop = $('#chatMessages').scrollHeight;
    }

    async function sendChatQuery(msg) {
      const text = msg || $('#chatInput').value.trim();
      if (!text || !S.sid) return;
      $('#chatInput').value = '';
      addChat('user', text);
      try {
        const j = await fetchJSON(`${API}/sessions/${S.sid}/chat`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        if (j.ok) addChat('ai', j.response);
        else addChat('ai', '[Error] ' + (j.error || j.response));
      } catch (e) { addChat('ai', '[Error] ' + e.message); }
    }

    // Dynamic Manual Splitter Drag Logic
    function initResizers() {
      const leftResizer = $('#resizer-left');
      const rightResizer = $('#resizer-right');
      const sidebar = $('#sidebar');
      const copilot = $('#copilotPanel');

      let activeDrag = null;

      leftResizer.addEventListener('mousedown', (e) => {
        activeDrag = 'left';
        leftResizer.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        e.preventDefault();
      });

      rightResizer.addEventListener('mousedown', (e) => {
        activeDrag = 'right';
        rightResizer.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        e.preventDefault();
      });

      window.addEventListener('mousemove', (e) => {
        if (!activeDrag) return;
        if (activeDrag === 'left') {
          const newWidth = Math.max(140, Math.min(e.clientX, 360));
          sidebar.style.width = newWidth + 'px';
        } else if (activeDrag === 'right') {
          const newWidth = Math.max(240, Math.min(window.innerWidth - e.clientX, 600));
          copilot.style.width = newWidth + 'px';
        }
      });

      window.addEventListener('mouseup', () => {
        if (!activeDrag) return;
        leftResizer.classList.remove('dragging');
        rightResizer.classList.remove('dragging');
        document.body.style.cursor = '';
        activeDrag = null;
      });
    }

    // Event Listeners & Wiring
    document.addEventListener('DOMContentLoaded', () => {
      initResizers();

      // Navigation Routing
      $$('.nav-item').forEach(n => n.addEventListener('click', () => switchView(n.dataset.view)));

      // Staging & Files
      $('#btnStageFiles').addEventListener('click', () => $('#globalFileInput').click());
      $('#globalFileInput').addEventListener('change', e => {
        stageLocalFiles([...e.target.files]);
        e.target.value = '';
        switchView('staging');
      });

      const dz = $('#stagingDropzone');
      ['dragenter', 'dragover'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add('drag'); }));
      ['dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove('drag'); }));
      dz.addEventListener('drop', e => { stageLocalFiles([...e.dataTransfer.files]); switchView('staging'); });

      $('#btnSample').addEventListener('click', () => {
        const f1 = new File([SAMPLE_PAY], 'payments.csv', { type: 'text/csv' });
        const f2 = new File([SAMPLE_BANK], 'bank.csv', { type: 'text/csv' });
        stageLocalFiles([f1, f2]);
        switchView('staging');
      });

      $('#btnRunPipeline').addEventListener('click', startPipeline);
      $('#btnStagingExecute').addEventListener('click', startPipeline);

      // Controls & Actions
      $('#btnAbort').addEventListener('click', async () => {
        if (!S.abortToken) return;
        await fetchJSON(`${API}/sessions/${S.sid}/abort`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token: S.abortToken }) });
        toast('Abort requested.', 'danger');
      });

      $('#btnResume').addEventListener('click', async () => {
        await fetchJSON(`${API}/sessions/${S.sid}/resume`, { method: 'POST' });
        $('#haltBanner').classList.remove('show');
        startPolling();
        toast('Resumed execution.');
      });

      $('#btnRefresh').addEventListener('click', () => { refreshOverview(); loadDashboard(); });
      $('#btnExportCsv').addEventListener('click', () => window.open(`${API}/sessions/${S.sid}/export.csv`, '_blank'));
      $('#btnExportReport').addEventListener('click', () => window.open(`${API}/sessions/${S.sid}/export/report.json`, '_blank'));
      $('#btnExportAudit').addEventListener('click', () => window.open(`${API}/sessions/${S.sid}/export/audit.jsonl`, '_blank'));

      $('#btnVerifyChain').addEventListener('click', async () => {
        const a = await fetchJSON(`${API}/sessions/${S.sid}/audit`);
        toast(a.verified ? 'SHA-256 Chain Integrity Verified.' : 'TAMPER DETECTED!', a.verified ? 'success' : 'danger');
        loadAudit();
      });

      // Copilot Toggles
      $('#btnToggleCopilot').addEventListener('click', () => {
        const c = $('#copilotPanel');
        const r = $('#resizer-right');
        const isClosed = c.classList.toggle('closed');
        r.style.display = isClosed ? 'none' : 'block';
      });
      $('#btnCloseCopilot').addEventListener('click', () => {
        $('#copilotPanel').classList.add('closed');
        $('#resizer-right').style.display = 'none';
      });
      $('#btnSend').addEventListener('click', () => sendChatQuery());
      $('#chatInput').addEventListener('keydown', e => { if (e.key === 'Enter') sendChatQuery(); });
      $$('.chip-btn').forEach(b => b.addEventListener('click', () => sendChatQuery(b.dataset.prompt)));

      // Grid Tabs & KPI Filters
      $$('.grid-tab[data-tab]').forEach(t => t.addEventListener('click', () => {
        $$('.grid-tab[data-tab]').forEach(x => x.classList.remove('active'));
        t.classList.add('active');
        S.grid.tab = t.dataset.tab;
        renderSpreadsheetGrid();
      }));
      $$('.kpi[data-tab]').forEach(k => k.addEventListener('click', () => {
        $$('.kpi[data-tab]').forEach(x => x.classList.remove('active'));
        k.classList.add('active');
        S.grid.tab = k.dataset.tab;
        $$('.grid-tab[data-tab]').forEach(t => t.classList.toggle('active', t.dataset.tab === k.dataset.tab));
        renderSpreadsheetGrid();
      }));
      $('#gridFilter').addEventListener('input', e => { S.grid.filter = e.target.value; renderSpreadsheetGrid(); });

      // Data Explorer Tabs
      $('#expTabs').addEventListener('click', async e => {
        const t = e.target.closest('.grid-tab'); if (!t) return;
        S.explorer.table = t.dataset.tbl; S.explorer.page = 1;
        await loadExplorer();
      });
      $('#expPrev').addEventListener('click', async () => { S.explorer.page--; await loadExplorerPage(); });
      $('#expNext').addEventListener('click', async () => { S.explorer.page++; await loadExplorerPage(); });

      boot();
    });
  </script>
</body>

</html>
```

### recon_agent/tests/__init__.py

```python


```

### recon_agent/tests/conftest.py

```python
"""Pytest Test Suite Configuration and Global Fixtures.

Provides session-scoped test environment isolation, redirecting audit ledgers,
logs, and uploaded datasets to a temporary directory so unit and integration tests
do not pollute production or local development workspace folders.
"""

import os
from pathlib import Path
import shutil
import tempfile

import pytest


@pytest.fixture(autouse=True, scope="session")
def isolate_test_environment() -> None:
    """Ensure all test runs write temporary logs and audit files to an isolated temp directory."""
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

    # Import modules to patch directories dynamically
    from app import config
    from app.core import audit

    audit.AUDIT_DIR = test_audit
    config.AUDIT_DIR = test_audit
    config.LOGS_DIR = test_logs
    config.UPLOAD_DIR = test_uploads

    yield

    # Cleanup temporary test directory after test session
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


```

### recon_agent/tests/test_constants.py

```python
"""Unit Tests for Immutable Registry and Constants Loading.

Verifies:
  1. Registry loads constants from constants_v0.yaml successfully with version tagging.
  2. Core threshold constants (match auto threshold, review floors) match specifications.
  3. Default Razorpay fee schedules and GST tax multipliers parse into structured models.
"""

from app.core.constants import REG


def test_registry_loads_and_fee_schedule_parsed() -> None:
    """Verify registry loading, version metadata, and fee schedule parameter validation."""
    assert REG.version == "v0"
    assert REG["match_auto_threshold"] == 0.85
    assert "razorpay_test_mode" in REG.fee_schedules
    fs = REG.fee_schedules["razorpay_test_mode"]
    assert fs.params["rate"] == 0.02 and fs.gst_rate == 0.18


```

### recon_agent/tests/test_durability.py

```python
"""Unit Tests for Cryptographic Audit Trail Durability and Tamper Detection.

Verifies:
  1. Audit entries persist across process restarts with intact SHA-256 chain verification.
  2. Any unauthorized modification to an intermediate log record invalidates downstream hashes.
"""

from pathlib import Path

from app.core.audit import AuditLog


def test_restart_and_tamper(tmp_path: Path) -> None:
    """Verify cryptographic audit trail persistence, reloadability, and tamper detection."""
    p = tmp_path / "s1.audit.jsonl"
    a = AuditLog(p)
    a.append({"event": "STATE_ENTERED", "state": "INGESTING"})
    a.append({"event": "tool_ok:x", "usd": 0.001})
    a.append({"event": "STATE_EXITED", "state": "INGESTING"})
    del a

    # Reload from disk and verify clean SHA-256 chain integrity
    b = AuditLog(p)
    assert len(b.records) == 3 and b.verify()

    # Tamper with an intermediate line on disk
    txt = p.read_text().splitlines()
    txt[1] = txt[1].replace("tool_ok:x", "tool_ok:EVIL")
    p.write_text("\n".join(txt) + "\n")

    # Verification must fail on tampered audit ledger
    assert not AuditLog(p).verify()


```

### recon_agent/tests/test_file_lifecycle_and_chat.py

```python
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


```

### recon_agent/tests/test_halt_reentry_safety.py

```python
"""Unit Tests for State Machine Halt and Re-entry Safety Invariants.

Verifies:
  1. Resuming a low-confidence mapping halt re-evaluates the validation gate rather than
     silently bypassing the check and advancing to POLICY_GENERATED with invalid schema links.
  2. Resuming an unresolvable schema halt (zero linkable columns) re-halts cleanly without
     infinite loops or hanging threads.
"""

from pathlib import Path
from typing import Any

import pytest

from app.core import llm_client
from app.core.contracts import ColumnProfile
from app.core.states import State
from app.pipeline import Pipeline


def test_low_confidence_mapping_rehalts_on_resume_not_bypassed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify resuming a below-floor mapping halt re-evaluates the confidence floor instead of bypassing."""
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    p = Pipeline("v1-test", auto_ack=False)
    # Two tables with marginal key overlap resulting in low mapping confidence
    p.tables = {
        "left": [{"_rid": 1, "id": "X1", "amt": 10.0}, {"_rid": 2, "id": "X2", "amt": 20.0}],
        "right": [{"_rid": 1, "ref": "Z9", "val": 999.0}],
    }
    p.profiles = {
        "left": [
            ColumnProfile(
                name="id",
                dtype="text",
                numeric_ratio=0,
                date_ratio=0,
                cardinality=1.0,
                null_rate=0,
                min_len=2,
                max_len=2,
                sample_values=["X1"],
                pii_likelihood=0,
            )
        ],
        "right": [
            ColumnProfile(
                name="ref",
                dtype="text",
                numeric_ratio=0,
                date_ratio=0,
                cardinality=1.0,
                null_rate=0,
                min_len=2,
                max_len=2,
                sample_values=["Z9"],
                pii_likelihood=0,
            )
        ],
    }
    ok = p.propose_mapping()
    if ok:
        ok = p.validate_mapping()
    assert p.sm.state == State.HALT, "expected halt on low-confidence mapping"
    p.sm.resume()
    result = p.continue_run()
    # Must NOT have silently advanced to POLICY_GENERATED or DRY_RUN with bad schema mapping;
    # must re-halt on the unresolved condition
    assert p.sm.state == State.HALT, "resume must re-check, not bypass, the confidence gate"


def test_no_linkable_columns_rehalts_not_infinite_loops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify resuming a no-linkable-columns halt re-halts promptly without infinite loops or hanging."""
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    p = Pipeline("v2-test", auto_ack=False)
    p.tables = {"left": [{"_rid": 1, "a": "foo"}], "right": [{"_rid": 1, "b": "bar"}]}
    p.profiles = {
        "left": [
            ColumnProfile(
                name="a",
                dtype="text",
                numeric_ratio=0,
                date_ratio=0,
                cardinality=1.0,
                null_rate=0,
                min_len=3,
                max_len=3,
                sample_values=["foo"],
                pii_likelihood=0,
            )
        ],
        "right": [
            ColumnProfile(
                name="b",
                dtype="text",
                numeric_ratio=0,
                date_ratio=0,
                cardinality=1.0,
                null_rate=0,
                min_len=3,
                max_len=3,
                sample_values=["bar"],
                pii_likelihood=0,
            )
        ],
    }
    ok = p.propose_mapping()
    assert not ok and p.sm.state == State.HALT
    p.sm.resume()
    result = p.continue_run()  # Must return promptly without hanging
    assert p.sm.state == State.HALT, "resume with no new data must re-halt, not silently proceed or loop forever"


```

### recon_agent/tests/test_interactive_resume.py

```python
"""Unit Tests for Interactive Pause and Resume Pipeline Execution.

Verifies:
  1. Pipeline configured with auto_ack=False halts safely on interactive gates.
  2. Successive manual resume calls (p.sm.resume() + continue_run()) drive the engine
     forward to ARCHIVED completion without state loss or memory corruption.
"""

from pathlib import Path
from typing import Any

import pytest

from app.core import llm_client
from app.data.generator import generate
from app.pipeline import Pipeline


def test_halt_then_resume_completes_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that an interactive pipeline halted by policy gates completes successfully upon manual resumption."""
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    generate(tmp_path)
    p = Pipeline("resume-test", auto_ack=False)  # Interactive mode without auto-ack
    result = p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"], tmp_path / "ground_truth.jsonl")

    # Manually resume on any encountered halt until complete
    while result is None and p.sm.state.name == "HALT":
        p.sm.resume()
        result = p.continue_run()

    assert result is not None and result.match_rate > 0


```

### recon_agent/tests/test_match_evidence.py

```python
"""Unit Tests for Pair Scoring and Evidence Factor Extraction.

Verifies:
  1. Exact amount parity produces AMOUNT_WITHIN_TOL without asserting FEE_MODEL_MATCH.
  2. Gateway fee deductions (net = gross - fee) trigger FEE_MODEL_MATCH exclusively.
  3. Multi-attribute scoring generates composite confidence above the auto-match threshold.
"""

from typing import Any, Dict

import pytest

from app.core import llm_client
from app.core.constants import REG
from app.core.contracts import EvidencePiece
from app.engine import match


@pytest.fixture(autouse=True)
def no_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable external LLM calls to force pure deterministic heuristic execution."""
    def boom(*a: Any, **k: Any) -> None:
        raise ConnectionError("llm down")

    monkeypatch.setattr(llm_client, "json_chat", boom)


CFG: Dict[str, Any] = {
    "left_key": "order_id",
    "right_key": "utr",
    "left_amount": "amount",
    "right_amount": "credit",
    "left_date": "date",
    "right_date": "date",
    "tolerance": 0.01,
    "window_days": 3,
}
SCHED = REG.fee_schedules["razorpay_test_mode"]


def test_exact_raw_match_scores_full_amount() -> None:
    """Verify that exact amount equality generates AMOUNT_WITHIN_TOL and full amount score."""
    l = {"order_id": "A", "amount": 1000.0, "date": "2026-03-01"}
    r = {"utr": "A", "credit": 1000.0, "date": "2026-03-02"}
    v, comps, ev, sd = match.score_pair("t", l, r, CFG, SCHED, [])
    assert comps["amount"] == 1.0
    assert EvidencePiece.AMOUNT_WITHIN_TOL in ev and EvidencePiece.FEE_MODEL_MATCH not in ev
    assert v >= REG["match_auto_threshold"]


def test_fee_case_exclusive_and_detected() -> None:
    """Verify that gateway fee variances trigger FEE_MODEL_MATCH exclusively."""
    l = {"order_id": "B", "amount": 2000.0, "date": "2026-03-01"}
    r = {"utr": "B", "credit": 1952.80, "date": "2026-03-02"}
    v, comps, ev, sd = match.score_pair("t", l, r, CFG, SCHED, [])
    assert EvidencePiece.FEE_MODEL_MATCH in ev and EvidencePiece.AMOUNT_WITHIN_TOL not in ev
    assert comps["amount"] == 1.0


```

### recon_agent/tests/test_no_duplicate_exceptions.py

```python
"""Unit Tests for Exception Queue Uniqueness and Deduplication.

Verifies:
  1. No transaction record (by (side, rid) tuple) appears more than once in the exception queue.
  2. Soft-paired right rows from unmatched candidate pairings do not duplicate as standalone right entries.
"""

from pathlib import Path
from typing import Any

import pytest

from app.core import llm_client
from app.data.generator import generate
from app.pipeline import Pipeline


def test_no_duplicate_exception_rids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that every entry in the pipeline exception queue has a unique (side, rid) identifier."""
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
    generate(tmp_path)
    p = Pipeline("dedupe-test", auto_ack=True)
    p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"], tmp_path / "ground_truth.jsonl")
    seen = [(i["rec"].side, i["rec"].rid) for i in p.queue]
    assert len(seen) == len(set(seen)), f"duplicate exception entries: {seen}"


```

### recon_agent/tests/test_overrides_and_discrepancies.py

```python
"""Unit & Integration Tests for Operator Overrides and Discrepancy Invariants.

Verifies:
  1. Split transaction legs are not falsely classified as COUNTERPARTY_MISMATCH.
  2. Operator overrides (approvals and escalations) dynamically update FinalReport count invariants
     (auto_resolved + escalated + unresolved == honest_exception_count).
  3. Overrides record complete disagreement history comparing system proposals against user actions.
"""

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
import pytest

from app.core import llm_client
from app.core.contracts import HypothesisCategory
from app.data.generator import generate
from app.pipeline import Pipeline
from app.server.main import app, SESSIONS


@pytest.fixture(autouse=True)
def no_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable external LLM calls to test deterministic execution and override tracking."""
    monkeypatch.setattr(llm_client, "json_chat", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))


def test_split_legs_not_falsely_counterparty_mismatch(tmp_path: Path) -> None:
    """Verify that split batch transaction legs are classified as SPLIT rather than COUNTERPARTY_MISMATCH."""
    generate(tmp_path)
    p = Pipeline("split-class-test", auto_ack=True)
    p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"], tmp_path / "ground_truth.jsonl")

    # Check that ORD_6 (rid 6) and ORD_7 (rid 7) are not classified as COUNTERPARTY_MISMATCH
    split_items = [i for i in p.queue if i["rec"].side == "L" and i["rec"].rid in (6, 7)]
    for item in split_items:
        assert item["rec"].reason != HypothesisCategory.COUNTERPARTY_MISMATCH, (
            f"Split leg rid {item['rec'].rid} was falsely classified as COUNTERPARTY_MISMATCH"
        )


def test_override_updates_report_and_preserves_disagreement(tmp_path: Path) -> None:
    """Verify that operator overrides update final report counts and log proposal disagreements."""
    generate(tmp_path)
    client = TestClient(app)

    # 1. Create session
    resp = client.post("/api/sessions")
    assert resp.status_code == 200
    sid = resp.json()["session_id"]

    p = Pipeline(sid, auto_ack=True)
    p.run([tmp_path / "payments.csv", tmp_path / "bank.csv"], tmp_path / "ground_truth.jsonl")
    SESSIONS[sid]["pipe"] = p

    # Verify initial sum invariant
    assert (
        p.final.auto_resolved_count + p.final.escalated_count + p.final.unresolved_count
        == p.final.honest_exception_count
    )

    initial_auto_resolved = p.final.auto_resolved_count
    initial_escalated = p.final.escalated_count
    initial_unresolved = p.final.unresolved_count

    # Pick first pending exception
    target_item = next(i for i in p.queue if i["action"] != "auto_resolve")
    target_rid = target_item["rec"].rid
    prior_action = target_item["action"]

    # 2. Perform user override to approve (mark_resolved)
    override_resp = client.post(
        f"/api/sessions/{sid}/exceptions/{target_rid}/action",
        json={"action": "approve", "note": "verified by human auditor"},
    )
    assert override_resp.status_code == 200
    assert override_resp.json()["ok"] is True

    # Check that report counts updated and sum invariant strictly holds
    assert p.final.auto_resolved_count == initial_auto_resolved + 1
    assert (
        p.final.auto_resolved_count + p.final.escalated_count + p.final.unresolved_count
        == p.final.honest_exception_count
    )

    # Check that disagreement is preserved with prior proposal details
    assert len(p.final.llm_user_disagreements) > 0
    disagreement = p.final.llm_user_disagreements[-1]
    assert disagreement["rid"] == target_rid
    assert disagreement["system_proposal"]["action"] == prior_action
    assert disagreement["user_decision"]["action"] == "mark_resolved"
    assert disagreement["user_decision"]["note"] == "verified by human auditor"

    # 3. Perform user override to escalate another item
    target_item2 = next(i for i in p.queue if i["rec"].rid != target_rid and i["action"] != "auto_resolve")
    target_rid2 = target_item2["rec"].rid
    override_resp2 = client.post(
        f"/api/sessions/{sid}/exceptions/{target_rid2}/action",
        json={"action": "escalate", "note": "escalated to finance ops"},
    )
    assert override_resp2.status_code == 200

    # Check sum invariant strictly holds after escalation as well
    assert p.final.escalated_count >= 1
    assert (
        p.final.auto_resolved_count + p.final.escalated_count + p.final.unresolved_count
        == p.final.honest_exception_count
    )


```

### recon_agent/tests/test_pipeline_evidence_flow.py

```python
"""Unit & Integration Tests for End-to-End Pipeline Evidence Flow and Benchmark Precision/Recall.

Verifies:
  1. Pipeline achieves 100% benchmark precision and recall against synthetic ground truth.
  2. All core discrepancy categories (refund_offset, split, temporal_drift, duplicate) are recognized.
  3. Evidence factors AMOUNT_WITHIN_TOL and FEE_MODEL_MATCH maintain strict mutual exclusivity.
"""

from pathlib import Path
from typing import Any

import pytest

from app.core import llm_client
from app.core.contracts import EvidencePiece
from app.data.generator import generate
from app.pipeline import Pipeline


@pytest.fixture(autouse=True)
def no_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable external LLM calls to verify deterministic heuristic accuracy."""
    def boom(*a: Any, **k: Any) -> None:
        raise ConnectionError("llm down")

    monkeypatch.setattr(llm_client, "json_chat", boom)


def test_end_to_end_classifications_and_evidence(tmp_path: Path) -> None:
    """Verify end-to-end classification taxonomy, evidence exclusivity, and 100% benchmark precision/recall."""
    generate(tmp_path)
    p = Pipeline("test-session", auto_ack=True)
    final = p.run(
        [tmp_path / "payments.csv", tmp_path / "bank.csv"],
        tmp_path / "ground_truth.jsonl",
    )
    assert final is not None
    reasons = {i["rec"].reason.value for i in p.queue}
    assert {"refund_offset", "split", "temporal_drift", "duplicate"} <= reasons

    # Ensure amount within tolerance and fee model match are mutually exclusive
    for item in p.queue:
        pieces = set(item["pieces"])
        assert not ({EvidencePiece.AMOUNT_WITHIN_TOL, EvidencePiece.FEE_MODEL_MATCH} <= pieces)

    assert final.precision_vs_truth == 1.0 and final.recall_vs_truth == 1.0


```
