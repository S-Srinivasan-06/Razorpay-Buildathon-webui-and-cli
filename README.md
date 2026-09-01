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
ORD_1001,1000.00,2026-03-01
ORD_1002,1500.00,2026-03-01
ORD_1003,2000.00,2026-03-01
ORD_1004,2500.00,2026-03-01
ORD_1005,3000.00,2026-03-01
ORD_1006,3500.00,2026-03-01
ORD_1007,4000.00,2026-03-01
```

### 2. `sample_data/bank.csv` (Source B: Bank Statement)
```csv
utr,credit,date
ORD_1001,976.40,2026-03-02
ORD_1002,1464.60,2026-03-02
ORD_1003,1952.80,2026-03-02
ORD_1004,2441.00,2026-03-02
ORD_1005,2929.20,2026-03-02
ORD_1006,3417.40,2026-03-02
ORD_1007,3905.60,2026-03-02
```

### 3. `sample_data/ground_truth.jsonl` (Benchmark Mapping)
```jsonl
{"l_rid": 1, "r_rid": 1, "class": "fee_deduction"}
{"l_rid": 2, "r_rid": 2, "class": "fee_deduction"}
{"l_rid": 3, "r_rid": 3, "class": "fee_deduction"}
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