# Razorpay Autonomous Financial Reconciliation Agent

[![CI Pipeline](https://github.com/S-Srinivasan-06/Razorpay-Buildathon-webui-and-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/S-Srinivasan-06/Razorpay-Buildathon-webui-and-cli/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

> **Enterprise-Grade Autonomous Financial Reconciliation Engine** featuring Multi-Way 3-Legged Settlement Chaining, Mathematical Cash Conservation Invariants, Cryptographic SHA-256 Audit Trails, and Grounded AI Intelligence powered by **Gemma 4 31B**.

---

## ⚡ 1-Click Deployment (Zero Friction)

### Option A: Docker Compose (Recommended)

Spin up the entire application stack—including the FastAPI backend, priority WebSocket event bus, and Single-Page Web UI—with a single command:

```bash
# 1. Clone the repository
git clone https://github.com/S-Srinivasan-06/Razorpay-Buildathon-webui-and-cli.git
cd Razorpay-Buildathon-webui-and-cli

# 2. Configure environment variables (optional for local/offline mode)
cp .env.example .env

# 3. Launch via Docker Compose
docker-compose up --build
```

Open your browser and navigate to:
```
http://localhost:8000
```
*(All audit logs and uploaded datasets persist across container restarts via the `recon_data` volume).*

---

### Option B: Local Python Environment

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install pinned dependencies
pip install -r requirements.txt

# 3. Configure your environment
cp .env.example .env
# Edit .env to add your GEMINI_API_KEY (optional: pure offline deterministic mode requires no keys)

# 4. Start the Web Console Server
python src/main.py --server --host 127.0.0.1 --port 8000
```

---

## 🏛️ Core Architectural Highlights

| Pillar | Technical Implementation | File Reference |
| :--- | :--- | :--- |
| **Autonomous 7-Step Pipeline** | Sequential finite state orchestration: Ingesting $\to$ Schema Profiling $\to$ Semantic Mapping $\to$ Policy Synthesis $\to$ Multi-Attribute Matching $\to$ Exception Classification $\to$ Financial Aggregation. | [`src/app/pipeline.py`](src/app/pipeline.py) |
| **Cryptographic SHA-256 Audit Trail** | Tamper-evident, forward-chained ledger where every event links to `parent_hash`. Final reports are cryptographically sealed with a balanced Merkle Root proof. | [`src/app/core/audit.py`](src/app/core/audit.py) |
| **Multi-Way 3-Legged Chaining** | Resolves three-dataset transitive settlements across **Merchant Orders $\leftrightarrow$ Payment Gateway Hub $\leftrightarrow$ Bank Statement Credits** with strict cash conservation invariants. | [`src/app/engine/multiway.py`](src/app/engine/multiway.py) |
| **Grounded AI Assistant** | Multi-turn conversational chatbot strictly grounded in session tables. Computes exact ticket-size distributions, variances, and standard deviations without refusals. | [`src/app/engine/chatbot.py`](src/app/engine/chatbot.py) |
| **Dynamic Fee & Segment Rules** | Priority-ordered segment rules matching by row ranges (`row_range_pct`), transaction categories (`column_equals`), or custom schedules with GST splits. | [`src/app/engine/rule_compiler.py`](src/app/engine/rule_compiler.py) |
| **Deterministic Multi-Heuristic Engine** | Sub-second matching combining exact key linkage, fuzzy token similarity, temporal calendar drift windows ($T+0 \dots T+7$), and subset-sum split settlement solving. | [`src/app/engine/matching.py`](src/app/engine/matching.py) |
| **Privacy & PII Masking** | Redaction engine scrubbing PAN cards, phone numbers, emails, and account numbers prior to LLM reasoning and WebSocket broadcast. | [`src/app/core/masking.py`](src/app/core/masking.py) |

---

## 📂 Production Repository Structure

```text
razorpay-recon/
├── .github/workflows/
│   └── ci.yml                     # Multi-Python (3.10, 3.11, 3.12) automated CI pipeline
├── docs/                          # Comprehensive technical documentation suite
│   ├── ARCHITECTURE.md            # Domain-driven architecture, 14-state FSM, and Event Bus
│   ├── SECURITY_AND_AUDIT.md      # SHA-256 Merkle proofs, PII redaction, and confirmation gates
│   └── HARDENING_POST_MORTEM.md   # Post-mortem analysis of 17 audited bugs and invariant proofs
├── src/                           # Core application package
│   ├── app/
│   │   ├── core/                  # Infrastructure (FSM, Audit, Contracts, Masking, LLM)
│   │   ├── engine/                # Financial domain math (Matching, Fee, Multiway, Rules)
│   │   ├── server/                # FastAPI application, REST API v2, WebSocket telemetry
│   │   ├── data/                  # Synthetic ecosystem & benchmark data generators
│   │   ├── config.py              # Resilient filesystem path and environment resolution
│   │   └── pipeline.py            # The 7-step autonomous orchestrator
│   ├── assets/
│   │   └── sample_datasets/       # Bundled benchmark datasets (basic, clean, 3-file, enterprise)
│   ├── static/                    # Single-Page Web Console UI (index.html)
│   ├── constants_v0.yaml          # Governance thresholds and default fee schedules
│   └── main.py                    # Unified CLI and Web Console server entry point
├── tests/                         # Comprehensive isolated test suite (38 tests)
│   ├── unit/                      # Contracts, state machine halts, and YAML registry tests
│   ├── integration/               # Audit chains, multi-way invariants, and rule compilers
│   ├── e2e/                       # FastAPI TestClient and 5-file enterprise simulations
│   └── conftest.py                # Global test isolation fixture (auto-redirects logs to tmp)
├── .dockerignore                  # Docker build exclusions (tests, docs, and git)
├── .env.example                   # Single source of truth for configuration variables
├── .gitignore                     # Production exclusions (data/, secrets, and bytecode)
├── Dockerfile                     # Multi-stage lightweight build (builder -> runner)
├── docker-compose.yml             # 1-click containerized deployment with volume persistence
├── pytest.ini                     # Pytest configuration with pythonpath = src
├── requirements.txt               # Pinned production dependencies
└── README.md                      # Project overview, quickstart, and technical guide
```

---

## 🖥️ Command-Line Interface (CLI) Usage

The unified entry point `src/main.py` provides high-throughput reconciliation directly in your terminal:

```bash
# 1. Standard two-file reconciliation (payments vs bank)
python src/main.py src/assets/sample_datasets/payments.csv src/assets/sample_datasets/bank.csv

# 2. Pure offline deterministic mode (Zero-LLM calls, sub-second execution)
python src/main.py src/assets/sample_datasets/payments.csv src/assets/sample_datasets/bank.csv --deterministic

# 3. Precision & Recall benchmark evaluation against ground truth
python src/main.py src/assets/sample_datasets/payments.csv src/assets/sample_datasets/bank.csv --truth src/assets/sample_datasets/ground_truth.jsonl

# 4. Launch interactive grounded AI assistant REPL after reconciliation
python src/main.py src/assets/sample_datasets/payments.csv src/assets/sample_datasets/bank.csv --chat

# 5. Output structured JSON for downstream enterprise ERP ingestion
python src/main.py src/assets/sample_datasets/payments.csv src/assets/sample_datasets/bank.csv --json
```

---

## 🌐 Interactive Web Console Features

Navigate to `http://localhost:8000` to interact with the full web console:

1. **Staging Area & Bundled Suites**: Drag-and-drop CSV/Excel files or load bundled enterprise ecosystems with 1 click:
   - *Standard Demo*: 57 payments vs 51 bank records.
   - *Clean Demo*: 100% matched baseline.
   - *3-File Benchmark*: Merchant Sales $\leftrightarrow$ Gateway Hub $\leftrightarrow$ Bank Statement.
   - *5-File Enterprise Ecosystem*: Zomato + Flipkart $\leftrightarrow$ Razorpay Hub $\leftrightarrow$ ICICI + HDFC.
2. **Real-Time 7-Step Stepper**: Live progress updates streamed via prioritized WebSockets.
3. **Dynamic Segment Rules Manager**: Configure multi-tier fee rates (e.g. first 40% at 2%, next 60% at 1.5%) and tax rules.
4. **Exception Resolution Queue**: Interactive classification badges (`temporal_drift`, `fee_variance`, `refund_offset`, `unmatched`) with human manager overrides (Approve / Reject).
5. **Multi-Way Cash Position Dashboard**: View in-transit aging schedules (T+1, T+2, T+7+) and double-entry General Ledger journal entries with one-click CSV export.
6. **Grounded AI Financial Assistant**: Ask complex statistical or accounting questions with zero refusal and automated confirmation gates for policy changes.

---

## 🧪 Comprehensive Test Suite

Run the full automated test suite covering unit tests, integration invariants, and end-to-end API flows:

```bash
pytest tests/ -v
```

```text
============================= test session starts =============================
tests/unit/test_constants.py::test_registry_loads_and_fee_schedule_parsed PASSED [ 84%]
tests/unit/test_durability.py::test_restart_and_tamper PASSED            [ 86%]
tests/unit/test_halt_reentry_safety.py::test_halt_safety PASSED          [ 92%]
tests/integration/test_audit_remediation.py::test_multiway_chaining PASSED [ 28%]
tests/integration/test_bug_audit_fixes.py::test_audit_fixes PASSED       [ 57%]
tests/e2e/test_enterprise_and_rules_e2e.py::test_5file_enterprise PASSED [ 13%]
tests/e2e/test_file_lifecycle_and_chat.py::test_chat_statistics PASSED  [ 23%]
======================== 37 passed, 1 skipped in 35.18s ========================
```

---

## 📖 In-Depth Documentation Links

- [System Architecture & Blueprint](docs/ARCHITECTURE.md)
- [Security, Audit Trails & Compliance](docs/SECURITY_AND_AUDIT.md)
- [Hardening Post-Mortem & Invariant Proofs](docs/HARDENING_POST_MORTEM.md)