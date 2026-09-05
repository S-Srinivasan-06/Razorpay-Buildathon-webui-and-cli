# Razorpay Autonomous Financial Reconciliation Agent

[![CI Pipeline](https://github.com/S-Srinivasan-06/Razorpay-Buildathon-webui-and-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/S-Srinivasan-06/Razorpay-Buildathon-webui-and-cli/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-41%20passed-brightgreen.svg)](tests/)

> **Enterprise-Grade Autonomous Financial Reconciliation Engine** featuring Multi-Way 5-Legged Supply Chain Chaining, Mathematical Cash Conservation Invariants, Cryptographic SHA-256 Audit Trails, and Grounded AI Intelligence powered by **Gemma 4 31B**.

---

## ⚡ Quick Start (Zero Friction)

### Option A: Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/S-Srinivasan-06/Razorpay-Buildathon-webui-and-cli.git
cd Razorpay-Buildathon-webui-and-cli/razorpay-recon

# 2. Configure environment (optional — deterministic offline mode needs no keys)
cp .env.example .env

# 3. Launch
docker-compose up --build
```

Open **http://localhost:8000** — the full Web Console is ready.

---

### Option B: Local Python

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Add GEMINI_API_KEY for AI features (optional)
python src/main.py --server --host 127.0.0.1 --port 8000
```

---

## 🖥️ Bundled Demo Datasets

Two demo suites are included and can be loaded with **one click** from the Web Console ("Load Sample Data" button):

### 1. Banana Supply & Inventory Demo *(2 Files)*
> Quick 2-file pairwise reconciliation — perfect for onboarding.

| File | Rows | Description |
|------|------|-------------|
| `payments.csv` | 100 | Dispatch orders — Flipkart & Zomato channels |
| `bank.csv` | 80 | Bank credits — HDFC Bank & ICICI Bank |

**30 injected discrepancies:** 10 duplicate orders · 10 value/price errors · 10 missing bank credits

```bash
# CLI equivalent
python src/main.py src/assets/sample_datasets/payments.csv \
                   src/assets/sample_datasets/bank.csv
```

---

### 2. UrbanNest — MegaDist Supply Chain Ecosystem *(5 Files)*
> Full B2B supply chain financing demo — UrbanNest (buyer) → MegaDist (supplier) via Razorpay X → HDFC + ICICI settlement.

| File | Rows | Role |
|------|------|------|
| `supply_chain_ecosystem/urban_nest_po.csv` | 100 | Buyer's Purchase Orders |
| `supply_chain_ecosystem/megadist_invoice.csv` | 100 | Supplier's Invoices |
| `supply_chain_ecosystem/razorpay_x_ledger.csv` | 100 | Razorpay X Financing Hub |
| `supply_chain_ecosystem/hdfc_corporate_statement.csv` | 51 | HDFC Bank (odd txns + 1 duplicate) |
| `supply_chain_ecosystem/icici_current_statement.csv` | 50 | ICICI Bank (even txns) |

**10 injected discrepancies** covering all major reconciliation failure modes:

| # | Discrepancy | Location |
|---|-------------|----------|
| 1 | PO amount inflated by ₹500 | PO rows 4–6 |
| 2 | Duplicate PO IDs (re-invoiced) | PO rows 97–100 |
| 3 | PENDING approval status | PO rows 1–3 |
| 4 | Invoice `ref_po_id` typos | Invoice rows 91–95 |
| 5 | `linked_invoice` = null (dropped) | Razorpay rows 96–100 |
| 6 | Fee rate 2.5% instead of 1.5% | Razorpay rows 16–20 |
| 7 | Transaction status = FAILED | Razorpay rows 11–15 |
| 8 | Same UTR credited twice | HDFC row 50 |
| 9 | ₹50 bank processing fee shortfall | ICICI row 45 |
| 10 | Settlement T+5 instead of T+1 | ICICI rows 26–30 |

```bash
# Run Multi-Way Chaining from the Web Console → "Run Multi-Way" tab
# Or load via API:
# POST /api/v2/sessions/{sid}/load_sample?dataset=supply_chain
```

---

## 🏛️ Architecture Highlights

| Pillar | Implementation | Reference |
|--------|---------------|-----------|
| **7-Step Autonomous Pipeline** | FSM: Ingesting → Profiling → Mapping → Policy → Matching → QA → Aggregating | [`src/app/pipeline.py`](src/app/pipeline.py) |
| **SHA-256 Audit Trail** | Forward-chained tamper-evident ledger + Merkle Root seal | [`src/app/core/audit.py`](src/app/core/audit.py) |
| **Multi-Way 5-Leg Chaining** | PO ↔ Invoice ↔ Razorpay Hub ↔ HDFC ↔ ICICI with cash conservation | [`src/app/engine/multiway.py`](src/app/engine/multiway.py) |
| **Grounded AI Assistant** | Gemma 4 31B chatbot strictly grounded in session tables | [`src/app/engine/chatbot.py`](src/app/engine/chatbot.py) |
| **Dynamic Fee & Tax Rules** | Priority segment rules with GST splits and `row_range_pct` | [`src/app/engine/rule_compiler.py`](src/app/engine/rule_compiler.py) |
| **Deterministic Matching** | Exact key + fuzzy token + T+0..T+7 drift + subset-sum split | [`src/app/engine/matching.py`](src/app/engine/matching.py) |
| **PII Masking** | PAN, phone, email, account number redaction before LLM | [`src/app/core/masking.py`](src/app/core/masking.py) |

---

## 📂 Repository Structure

```text
razorpay-recon/
├── .github/workflows/ci.yml          # Multi-Python CI (3.10, 3.11, 3.12)
├── docs/
│   ├── ARCHITECTURE.md               # 14-state FSM, Event Bus, Domain Design
│   ├── SECURITY_AND_AUDIT.md         # SHA-256 Merkle proofs, PII redaction
│   └── HARDENING_POST_MORTEM.md      # 17-bug post-mortem & invariant proofs
├── src/
│   ├── app/
│   │   ├── core/                     # FSM, Audit, Contracts, Masking, LLM client
│   │   ├── engine/                   # Matching, Fee, Multiway, Rules, QA, Chatbot
│   │   ├── server/                   # FastAPI REST API v2 + WebSocket telemetry
│   │   ├── data/                     # Ecosystem & benchmark dataset generators
│   │   ├── config.py                 # Filesystem path & environment resolution
│   │   └── pipeline.py               # 7-step autonomous orchestrator
│   ├── assets/
│   │   └── sample_datasets/
│   │       ├── payments.csv          # Banana demo — dispatch orders
│   │       ├── bank.csv              # Banana demo — bank credits
│   │       ├── ground_truth.jsonl    # Banana demo — match ground truth
│   │       └── supply_chain_ecosystem/
│   │           ├── urban_nest_po.csv
│   │           ├── megadist_invoice.csv
│   │           ├── razorpay_x_ledger.csv
│   │           ├── hdfc_corporate_statement.csv
│   │           └── icici_current_statement.csv
│   ├── static/index.html             # Single-Page Web Console UI
│   ├── constants_v0.yaml             # Governance thresholds & fee schedules
│   └── main.py                       # Unified CLI + Web Console entry point
├── tests/
│   ├── unit/                         # Contracts, FSM halts, YAML registry
│   ├── integration/                  # Audit chains, multiway invariants, rules
│   ├── e2e/                          # FastAPI TestClient + enterprise simulations
│   └── conftest.py                   # Auto-redirects logs/uploads to tmp
├── data/                             # Runtime-only (gitignored contents)
│   ├── uploads/.gitkeep              # Session-uploaded CSVs (created at runtime)
│   ├── audit/.gitkeep                # Per-session audit JSONL files
│   ├── logs/.gitkeep                 # Per-session run logs
│   └── outputs/.gitkeep             # Reconciliation report exports
├── .env.example                      # Config template (copy to .env)
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```

---

## 🔧 CLI Usage

```bash
# 2-file pairwise reconciliation
python src/main.py src/assets/sample_datasets/payments.csv \
                   src/assets/sample_datasets/bank.csv

# Deterministic offline mode (no LLM calls, sub-second)
python src/main.py payments.csv bank.csv --deterministic

# Benchmark against ground truth (precision + recall)
python src/main.py payments.csv bank.csv \
                   --truth src/assets/sample_datasets/ground_truth.jsonl

# Launch interactive AI assistant after reconciliation
python src/main.py payments.csv bank.csv --chat

# Structured JSON output for ERP ingestion
python src/main.py payments.csv bank.csv --json
```

---

## 🌐 Web Console Features

| Feature | Description |
|---------|-------------|
| **Staging Area** | Drag-drop CSV/Excel or one-click load demo suites |
| **7-Step Stepper** | Live progress via WebSocket — watch each pipeline stage |
| **Exception Queue** | Classify & override: `temporal_drift`, `fee_variance`, `duplicate`, `missing`, `value_error` |
| **Fee & Tax Rules** | Build segment rules with `row_range_pct`, `column_equals`, GST splits |
| **Multi-Way Dashboard** | Cash position aging (T+1, T+7+), double-entry journal, CSV export |
| **AI Assistant** | Grounded chatbot — ask about variances, distributions, anomalies |
| **Resume / Restart** | Resume a halted pipeline or restart fresh from ARCHIVED state |
| **Export** | JSON report, audit JSONL download |

---

## 🧪 Test Suite

```bash
pytest tests/ -v
```

```
41 passed, 1 skipped in ~37s
```

Tests cover: state machine halts · rule compiler anchoring · multiway invariants · journal GST splits · chat confirmation gates · 5-file enterprise ecosystem · audit chain durability · PII masking · duplicate exception detection.

---

## 📖 Documentation

- [System Architecture & Blueprint](docs/ARCHITECTURE.md)
- [Security, Audit Trails & Compliance](docs/SECURITY_AND_AUDIT.md)
- [Hardening Post-Mortem & Invariant Proofs](docs/HARDENING_POST_MORTEM.md)