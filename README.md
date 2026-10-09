# CaFinIQ — Production Bank Statement Intelligence & Financial Analysis Platform

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Backend](https://img.shields.io/badge/FastAPI-0.136-blue.svg)]()
[![Frontend](https://img.shields.io/badge/React-18_TS-indigo.svg)]()
[![ICAI Compliance](https://img.shields.io/badge/Audit_Standards-ICAI_Ready-emerald.svg)]()
[![License](https://img.shields.io/badge/license-Proprietary-slate.svg)]()

> **Engineered specifically for Chartered Accountants (CAs), tax auditors, accounting firms, and finance teams in India.**

Transform complex, highly variable Indian bank statement PDFs into **validated, searchable, auditable, and reconcilable financial datasets**.

---

## 1. Key Capabilities

* **Multi-Bank Statement Parser Adapters**:
  * Native adapters for **SBI**, **HDFC Bank**, **ICICI Bank**, **Axis Bank**, **Kotak Mahindra Bank**, and an adaptive **Generic Indian Bank Parser** with semantic column detection.
* **Dual Processing Pipeline**:
  * **Digital / Text PDFs**: High-performance extraction via PyMuPDF (`fitz`) and `pdfplumber` bounding-box grid reconstruction.
  * **Scanned / Image PDFs**: Automated orientation correction, deskew, and ONNX-powered RapidOCR with word-level bounding-box clustering.
* **Strict Balance Continuity & Mathematical Invariants**:
  * Step-by-step continuity verification:
    $$\text{Balance}_t = \text{Balance}_{t-1} + \text{Credit}_t - \text{Debit}_t$$
  * Statement-level invariant:
    $$\text{Closing Balance} = \text{Opening Balance} + \sum \text{Credits} - \sum \text{Debits}$$
  * Zero-float policy: All currency and balances are computed with Python `Decimal` (accounting precision).
* **Narration Intelligence & NLP**:
  * Automatic detection of Indian payment modes (**UPI**, **NEFT**, **RTGS**, **IMPS**, **ATM**, **POS**, **CHEQUE**, **CASH**, **NACH**, **ECS**).
  * UPI ID / VPA extraction (`merchant@okhdfcbank`), Cheque serial numbers, UTR/RRN references.
  * Automated CA tax classification: **GST Payments**, **TDS Deductions**, **Advance Tax**, **Self-Assessment Tax**.
* **Audit Lineage & Forensic Traceability**:
  * Every extracted transaction preserves its physical source page number, row position, and untouched raw source string.
* **Professional 7-Sheet CA Excel Workbook Export**:
  * **Sheet 1**: Transactions (Formatted currency, autofilters, frozen headers, total formula cells).
  * **Sheet 2**: Executive Summary (Key KPIs, Opening/Closing balance, net movement).
  * **Sheet 3**: Monthly Analysis (Indian Financial Year Apr–Mar sequence).
  * **Sheet 4**: Payment Modes (Volume distribution & percentage share).
  * **Sheet 5**: Categories & Tax Breakdown.
  * **Sheet 6**: Balance Reconciliation & Broken Step Log.
  * **Sheet 7**: Review Required (Exceptions & Low Confidence items).
* **Human-in-the-Loop Review Queue**:
  * Exceptions flagged for CA approval: low OCR confidence (<90%), balance continuity breaks, duplicate suspicions, round-number spikes.
* **Natural Language Query Assistant**:
  * "Ask Your Bank Statement" interface converting natural questions into safe structured filters without arbitrary SQL injection.

---

## 2. System Architecture

```
PDF Statement (Digital or Scanned)
       │
       ▼
[Extraction Pipeline]
├── Digital Inspection (PyMuPDF)
├── OCR Fallback (RapidOCR ONNX)
├── Grid Table Detection (pdfplumber)
└── Bank Adapter Selection (SBI / HDFC / ICICI / Axis / Kotak / Generic)
       │
       ▼
[Normalization & NLP]
├── Indian Date Formatting (DD/MM/YYYY, DD-Mon-YYYY)
├── Indian Currency & Lakh Cleansing (₹, Cr/Dr, Commas)
└── Narration Parser (UPI VPAs, Modes, Tax Challans)
       │
       ▼
[Financial Validation Engine]
├── Step-by-Step Balance Continuity Verification
├── Closing Balance Invariant Checking
├── Anomaly & Duplicate Detection
└── Multi-Factor Confidence Scoring (0.00 – 1.00)
       │
       ▼
[Structured Relational Database (PostgreSQL / SQLite)]
       │
  ┌────┴───────────────────────────┐
  ▼                                ▼
[Virtual Spreadsheet UI]   [Export & Reporting]
├── Multi-Filtering & Sort ├── 7-Sheet CA Excel (openpyxl)
├── Inline Auditing & Edit ├── Canonical CSV
└── Audit Lineage Proof    └── Automated Reconciliation
```

---

## 3. Quick Start (Local Development)

### Prerequisites
* **Python 3.11+**
* **Node.js 18+** & **npm**

### Step 1: Clone & Run Locally
```bash
# Navigate to project root
cd C:\Users\DELL\Desktop\banksatamentconvertor

# Launch full-stack application (FastAPI + React UI)
python run_dev.py
```

Open your browser at:
* **Web Application**: `http://localhost:8000`
* **Interactive OpenAPI Docs**: `http://localhost:8000/docs`

### Step 2: Default Seed CA Login
The application automatically seeds a demo CA practice on first run:
* **Email**: `ca@mehtaca.com`
* **Password**: `AuditPassword123!`
* **Firm**: *K. R. Mehta & Associates, Chartered Accountants*

---

## 4. Running Tests

Execute the comprehensive automated test suite:
```bash
cd backend

# Run all 13 unit tests + end-to-end PDF integration test
python -m unittest discover tests
```

---

## 5. Docker Deployment

Launch full-stack application with PostgreSQL via Docker Compose:
```bash
docker-compose up --build -d
```
Access the application on `http://localhost:8000`.

---

## 6. Directory Structure

```
banksatamentconvertor/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST API endpoints (auth, clients, statements, review, exports)
│   │   ├── calculations/    # Exact Decimal mathematical engine & query assistant
│   │   ├── core/            # Database engine, PBKDF2 security, secure storage manager
│   │   ├── exports/         # 7-sheet openpyxl Excel & CSV generators
│   │   ├── extraction/      # PDF pipeline, OCR engine, table detector, bank parsers
│   │   │   └── parsers/     # SBI, HDFC, ICICI, Axis, Kotak, and Generic adapters
│   │   ├── models/          # Normalized SQLAlchemy 2.0 relational models
│   │   ├── schemas/         # Strict Pydantic v2 domain schemas
│   │   ├── validation/      # Balance continuity validator & anomaly detector
│   │   └── workers/         # Background job coordinator & progress tracker
│   ├── sample_statements/   # Synthetic Indian bank statement test PDFs
│   ├── tests/               # Unit and end-to-end PDF integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios client bindings with JWT interceptor
│   │   ├── components/      # Navbar, Sidebar, Upload modal, Assistant drawer
│   │   ├── pages/           # Dashboard, Clients, Statements, Transactions, Analytics, Recon, Review, Audit
│   │   ├── types/           # Canonical TypeScript interfaces
│   │   └── utils/           # Indian currency & date formatters
│   ├── package.json
│   └── vite.config.ts
├── storage/                 # Secure document and export artifact storage
├── Dockerfile               # Multi-stage production container
├── docker-compose.yml       # Production Compose with PostgreSQL
├── run_dev.py               # Local server launcher
└── README.md
```

---

## 7. ICAI Accounting & Audit Standard Compliance
* **Data Lineage Guarantee**: Original document rows are stored alongside normalized values.
* **Audit Trail Immutability**: All modifications preserve the user identity, old value, new value, and documented reason.
* **Data Privacy**: Bank account numbers are masked by default (`XXXXXX1234`).
