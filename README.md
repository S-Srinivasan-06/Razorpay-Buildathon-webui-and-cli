# Razorpay Autonomous Financial Reconciliation Agent

[![CI Pipeline](https://github.com/S-Srinivasan-06/Razorpay-Buildathon-webui-and-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/S-Srinivasan-06/Razorpay-Buildathon-webui-and-cli/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-41%20passed-brightgreen.svg)](razorpay-recon/tests/)

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
cd razorpay-recon
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
python src/main.py src/assets/sample_datasets/payments.csv src/assets/sample_datasets/bank.csv
```

---

### 2. UrbanNest / MegaDist Supply Chain Ecosystem *(5 Files)*
> Full multi-partner supply chain reconciliation across 5 counterparties.

```
Purchase Orders ──▶ Invoices ──▶ Razorpay X Ledger ──▶ Bank Settlements
 (UrbanNest)      (MegaDist)     (Financing Hub)      (HDFC & ICICI)
```

| File | Rows | Role | Counterparty |
|------|------|------|--------------|
| `urban_nest_po.csv` | 100 | Buyer Purchase Orders | UrbanNest Retail |
| `megadist_invoice.csv` | 100 | Supplier Tax Invoices | MegaDist Supplies |
| `razorpay_x_ledger.csv` | 100 | Financing & Payout Hub | Razorpay X |
| `hdfc_corporate_statement.csv` | 51 | Primary Settlement Bank | HDFC Bank |
| `icici_current_statement.csv` | 50 | Secondary Settlement Bank | ICICI Bank |

**10 injected enterprise discrepancies covering all failure modes:**
1. PO gross amount inflated +₹500 (Invoice rows 4–6)
2. Duplicate PO IDs reused (PO rows 97–100)
3. Orders stuck in `PENDING` approval (PO rows 1–3)
4. Invoice reference typos (`PO-` vs `PO-I-`) (Invoice rows 91–95)
5. Missing invoice linkage / dropped by gateway (Razorpay rows 96–100)
6. Fee rate overcharge 2.5% vs 1.5% contract (Razorpay rows 16–20)
7. Failed settlement transaction status (Razorpay rows 11–15)
8. Same UTR credited twice across cycles (HDFC row 50)
9. Net deposit shortfall / bank charge variance (ICICI row 45)
10. Settlement temporal drift T+5 vs T+1 SLA (ICICI rows 26–30)

```bash
# CLI equivalent (5-way reconciliation)
python src/main.py \
  src/assets/sample_datasets/supply_chain_ecosystem/razorpay_x_ledger.csv \
  src/assets/sample_datasets/supply_chain_ecosystem/hdfc_corporate_statement.csv \
  src/assets/sample_datasets/supply_chain_ecosystem/icici_current_statement.csv \
  src/assets/sample_datasets/supply_chain_ecosystem/urban_nest_po.csv \
  src/assets/sample_datasets/supply_chain_ecosystem/megadist_invoice.csv
```

---

### 3. Banana Multi-Way 3-File Benchmark *(Merchant → Gateway → Bank)*

```bash
python src/main.py \
  src/assets/sample_datasets/banana_multiway_3file/merchant_sales.csv \
  src/assets/sample_datasets/banana_multiway_3file/gateway_settlements.csv \
  src/assets/sample_datasets/banana_multiway_3file/bank_statement.csv
```

---

## 🏗️ Architecture & Core Innovations

```
                               ┌───────────────────────────┐
                               │   Single-Page Web UI      │
                               │  (Vue/Tailwind-free SPA)  │
                               └─────────────┬─────────────┘
                                             │ REST API v2 + WebSocket
                               ┌─────────────▼─────────────┐
                               │     FastAPI Server        │
                               │   (src/app/server/)       │
                               └─────────────┬─────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               │                             │                             │
    ┌──────────▼──────────┐       ┌──────────▼──────────┐       ┌──────────▼──────────┐
    │  Matching Engine    │       │ Multi-Way Chaining  │       │  Grounded AI Chat   │
    │  - Deterministic    │       │  - Cash Conservation│       │  - Zero PII Leak    │
    │  - Exact & Fuzzy    │       │  - Double-Entry     │       │  - 2-Step Gate      │
    │  - Fee/Tax Split    │       │    Journal Ledger   │       │  - Real Data Only   │
    └─────────────────────┘       └─────────────────────┘       └─────────────────────┘
               │                             │                             │
               └─────────────────────────────┼─────────────────────────────┘
                                             │
                               ┌─────────────▼─────────────┐
                               │ Cryptographic Audit Trail │
                               │  SHA-256 Hash Chaining    │
                               │   (Append-Only Ledger)    │
                               └───────────────────────────┘
```

1. **Deterministic 3-Stage Pipeline**: Exact match $\to$ Fee/tax-aware approximate match $\to$ Discrepancy isolation with temporal sliding window ($T \pm 3$ business days).
2. **Mathematical Cash Conservation**: Every transaction must satisfy:
   $$\text{Settled Amount} = \text{Gross Amount} - \text{MDR Fee} - \text{GST (18\%)} - \text{TDS (1\%)} \pm \Delta_{\text{tolerance}}$$
3. **Double-Entry Journal Generation**: Generates GAAP-compliant debits and credits for all settlements, gateway fees, GST liability, and shortfalls.
4. **Grounded AI with Confirmation Gate**: Conversational assistant strictly grounded on active session data. Any action affecting rules or data requires explicit two-step user confirmation before execution.
5. **Cryptographic SHA-256 Audit Trail**: Every decision, state transition, and human override is signed into a tamper-evident hash-chained log.
6. **PII Masking by Design**: PAN, Aadhaar, phone numbers, and emails are hashed/masked *before* any text leaves the boundary.

---

## 📁 Repository Structure

```
.
├── README.md                           # This file (GitHub landing page)
├── .gitignore                          # Git ignore rules (zero session bloat)
├── how_to_run.txt                      # Comprehensive command reference
└── razorpay-recon/                     # Core application package
    ├── Dockerfile                      # Multi-stage container definition
    ├── docker-compose.yml              # 1-click Docker launch
    ├── requirements.txt                # Python dependencies
    ├── pytest.ini                      # Pytest runner configuration
    ├── .env.example                    # Environment template
    ├── src/
    │   ├── main.py                     # Unified CLI / Server entrypoint
    │   ├── app/
    │   │   ├── core/                   # State machine, SHA-256 audit, PII masking, LLM
    │   │   ├── engine/                 # Matching engine, fee/tax rules, multiway chaining
    │   │   ├── server/                 # FastAPI REST API v2 & WebSocket endpoints
    │   │   └── data/                   # Ecosystem & benchmark generators
    │   ├── assets/sample_datasets/     # Bundled demo CSVs & benchmark truth files
    │   │   ├── payments.csv            # 2-file demo payments
    │   │   ├── bank.csv                # 2-file demo bank statement
    │   │   ├── ground_truth.jsonl      # Evaluation ground truth
    │   │   ├── banana_multiway_3file/  # 3-file benchmark datasets
    │   │   └── supply_chain_ecosystem/ # 5-file enterprise supply chain datasets
    │   └── static/index.html           # Dark-mode Single-Page Application UI
    ├── tests/                          # 42 Automated test suites
    │   ├── unit/                       # Unit tests (constants, durability, matching)
    │   ├── integration/                # Integration tests (audit, pipeline, fixes)
    │   └── e2e/                        # End-to-end tests (REST API, 5-way ecosystem)
    └── docs/                           # Technical documentation
        ├── ARCHITECTURE.md             # System design & component contracts
        ├── SECURITY_AND_AUDIT.md       # SHA-256 audit trail & PII policy
        └── HARDENING_POST_MORTEM.md    # Production hardening post-mortem
```

---

## 🧪 Testing & Verification

The test suite covers unit, integration, and full end-to-end multi-way pipelines with **zero external dependencies**:

```bash
cd razorpay-recon
pytest tests/ -v
```

```
collected 42 items
41 passed, 1 skipped, 1 warning in ~40s
```

*(1 skipped test requires optional httpx2 async client).*

---

## 🛡️ License

Built for the **Razorpay AI Buildathon 2026**.
