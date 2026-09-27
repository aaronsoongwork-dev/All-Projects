# AGENTS.md — Developer & Agent Guidelines

This document establishes project context, architecture conventions, and mandatory engineering protocols for AI agents and developers working on the **ShipCheck** codebase.

---

## 1. Project Overview

**ShipCheck** is an automated shipping document processing engine and FastAPI backend serving a React shipping operations dashboard (`email-app-UI`).

### Core Responsibilities
1. **Email Classification**: Classifies inbound emails into 5 operations categories (`Document Comparison`, `New SI Request`, `Invoice Query`, `General`, `Spam`) using OpenRouter decision models (`~typesafe/jev-latest`).
2. **Multi-format Document Extraction**: Pulls 7 standard shipping fields (`shipper`, `consignee`, `notify_party`, `port_of_loading`, `port_of_discharge`, `container_count`, `gross_weight_kg`) from PDF, DOCX, XLSX, and TXT attachments via Claude tool-use (with vision fallback for scanned PDFs).
3. **Hybrid Field Comparison**: Compares Shipping Instruction (SI) vs draft Bill of Lading (BL) values using deterministic normalization first, escalating differing text representations to Claude Haiku for entity verification.
4. **FastAPI Service**: Serves the React frontend (`ShipCheck`) with endpoints strictly matching frontend TypeScript contracts and CORS enabled.

---

## 2. Repository Layout

```
email-extract-compare/
├── core/                           # Primary OOP engine & domain models
│   ├── __init__.py                 # Exported classes & domain functions
│   ├── classifier.py               # EmailClassifier, ClassificationResult
│   ├── compare_ai.py               # DocumentComparator, ValueNormalizer, ComparisonResult
│   ├── extract.py                  # extract_fields, extract_fields_from_image, FIELDS
│   ├── check_email.py              # EmailMessage, AttachmentExtractor, EmailVerificationPipeline
│   ├── parse_eml.py                # parse_eml
│   ├── classify_wrapper.py         # classify_email
│   └── readers/                    # Format dispatchers (PDF, DOCX, XLSX, TXT)
│
├── api/                            # FastAPI backend application
│   ├── __init__.py                 # Exports FastAPI app
│   ├── main.py                     # App factory, CORS middleware, routes
│   ├── db.py                       # SQLite engine, init_db(), get_session()
│   ├── models.py                   # SQLModel models: EmailRecord, ComparisonRecord
│   ├── schemas.py                  # Pydantic models matching frontend TypeScript contracts
│   ├── adapter.py                  # Adapts core domain models to frontend schemas
│   └── routes/
│       ├── emails.py               # GET /api/emails & POST /api/emails/batch (cache)
│       ├── classify.py             # POST /api/classify
│       ├── compare.py              # POST /api/compare & POST /api/compare/text
│       ├── comparisons.py         # GET /api/comparisons & PATCH /review
│       └── health.py               # GET /api/health
│
├── tests/                          # Automated test suite
│   ├── __init__.py
│   ├── test_pipeline.py            # Unit tests for core engine (classifier, comparator, pipeline)
│   ├── test_api.py                 # Integration tests for FastAPI endpoints
│   └── test_db.py                  # Tests for SQLite persistence, caching, and serialization
│
├── classifier.py                   # Root shim -> core.classifier
├── compare_ai.py                   # Root shim -> core.compare_ai
├── check_email.py                  # Root CLI shim -> core.check_email
├── extract.py                      # Root shim -> core.extract
├── parse_eml.py                    # Root shim -> core.parse_eml
├── classify_wrapper.py             # Root shim -> core.classify_wrapper
├── run_eml_folder.py               # Standalone runner for real .eml folders
├── run_full_dataset.py             # Standalone runner producing competition submission.json
├── requirements.txt                # Production & development dependencies
└── AGENTS.md                       # This developer & agent protocol guide
```

---

## 3. Mandatory Protocol for Agents & Contributors

> [!IMPORTANT]
> **Always adhere to the following workflow whenever making updates, refactorings, or adding features:**

### Step 1: Preserve Architecture & Shims
- Place new domain and processing logic inside `core/`.
- Keep the FastAPI endpoints and schemas inside `api/`.
- **Do not break root shims** (`check_email.py`, `classifier.py`, etc.). CLI tools and batch scripts (`run_full_dataset.py`, `run_eml_folder.py`) rely on these entrypoints.

### Step 2: Maintain Frontend TypeScript Schema Alignment
- If modifying API responses or requests, check [`api/schemas.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/api/schemas.py) and ensure strict compatibility with the React frontend contracts:
  - `EmailType`: `"Document Comparison" | "New SI Request" | "Invoice Query" | "General" | "Spam"`
  - `EmailStatus`: `"New" | "Mismatch" | "Match" | "Needs Review" | "Classified" | "Processing"`
  - `EmailClassifyRequest` / `EmailClassifyResponse`
  - `ComparisonField` / `CompareResponse`

### Step 3: Run the Test Suite
**Before reporting completion on any task**, you MUST run the automated test suite and ensure all tests pass:

```powershell
# Windows PowerShell (using project venv)
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v

# Standard Linux/macOS
python -m unittest discover -s tests -p "test_*.py" -v
```

### Step 4: Add Tests for New Changes
- Whenever you introduce new features, endpoints, or fixes, add corresponding test cases in [`tests/test_pipeline.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/tests/test_pipeline.py) or [`tests/test_api.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/tests/test_api.py).

### Step 5: Verify Syntax Compilation
Run byte-compilation across the codebase to catch syntax and import regressions early:

```powershell
.\.venv\Scripts\python.exe -m py_compile api/main.py api/schemas.py api/adapter.py core/check_email.py core/classifier.py core/compare_ai.py
```

---

## 4. Key Developer Commands

### Launch FastAPI Server
```bash
uvicorn api.main:app --reload --port 8000
```
- Swagger Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/health`

### Run Single Email CLI Debugger
```bash
python check_email.py 003
```

### Run Batch Verification
```bash
python run_full_dataset.py
```

