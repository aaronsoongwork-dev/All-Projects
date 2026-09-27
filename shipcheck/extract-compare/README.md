# ShipCheck — Shipping Document Verification & Comparison Service

Part of the Averis x Monash Hackathon 2026 submission. **ShipCheck** is an automated shipping document processing engine and FastAPI backend serving a React operations dashboard. It extracts the 7 standard shipping fields from multi-format attachments (PDF, DOCX, XLSX, TXT) via Claude, classifies inbound correspondence, and performs hybrid deterministic + AI field comparison between Shipping Instructions (SI) and draft Bills of Lading (BL).

---

## What's in here

### 1. Backend Service (`api/`)
| Module | Description |
|---|---|
| [`api/main.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/api/main.py) | FastAPI application entrypoint with CORS middleware (`allow_origins=["*"]`), routes, and OpenAPI docs |
| [`api/schemas.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/api/schemas.py) | Pydantic request & response models strictly matching the frontend TypeScript contracts |
| [`api/adapter.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/api/adapter.py) | Data adapter translating between domain engine results and frontend UI models |
| [`api/routes/classify.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/api/routes/classify.py) | `POST /api/classify` — Classifies inbound email intent with heuristic fallback |
| [`api/routes/compare.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/api/routes/compare.py) | `POST /api/compare` (multipart file uploads) & `POST /api/compare/text` (raw text) |
| [`api/routes/health.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/api/routes/health.py) | `GET /api/health` — Service health check & provider readiness |

### 2. Core Processing Engine (`core/`)
| Module | Description |
|---|---|
| [`core/classifier.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/core/classifier.py) | `EmailClassifier` & `ClassificationResult` using OpenRouter decision models (`~typesafe/jev-latest`) |
| [`core/compare_ai.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/core/compare_ai.py) | `DocumentComparator`, `ValueNormalizer`, and `ComparisonResult` for hybrid field comparison |
| [`core/extract.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/core/extract.py) | Claude structured tool-use extraction (text via Haiku, scanned PDF vision fallback via Sonnet) |
| [`core/check_email.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/core/check_email.py) | `EmailMessage`, `AttachmentExtractor`, and `EmailVerificationPipeline` orchestrator |
| [`core/readers/`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/core/readers) | Text extractors for `.txt`, `.pdf`, `.docx`, `.xlsx` with scanned PDF detection |
| [`core/parse_eml.py`](file:///c:/Users/PC/Documents/GitHub/email-extract-compare/core/parse_eml.py) | Parses standard `.eml` files into subjects, bodies, and attachment byte payloads |

### 3. Standalone Scripts & CLI Shims
| Script | Description |
|---|---|
| `check_email.py` | CLI debugging tool — inspect single dataset email: classify → extract → compare |
| `run_full_dataset.py` | Batch checkpoint runner producing `submission.json` and Excel evaluation reports |
| `run_eml_folder.py` | Batch directory runner for real `.eml` files in `emails/` |

---

## How It Works

```
                        [ Inbound Email / Documents ]
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            ▼                                                   ▼
   [ Email Classification ]                             [ Attachments (PDF/DOCX/XLSX/TXT) ]
      EmailClassifier                                           │
  (OpenRouter / Heuristic)                              core/readers/
            │                                                   ▼
     Category Assigned:                                    Plain Text / Scanned Image
    - Document Comparison                                       │
    - New SI Request                                            ▼
    - Invoice Query                                    extract.py (Claude Structured Tool)
    - General                                                   │
    - Spam                                              7 Extracted Fields (SI & BL)
                                                                │
                                                                ▼
                                                    DocumentComparator (Hybrid)
                                                    ├─ Deterministic normalization
                                                    └─ Claude Haiku second-pass for text
                                                                │
                                                                ▼
                                                CompareResponse / VerificationReport
                                                (Match / Mismatch / Needs Review)
```

### The 7 Standard Fields
1. `shipper` (Shipper / Exporter details)
2. `consignee` (Consignee)
3. `notify_party` (Notify Party)
4. `port_of_loading` (Port of Loading / POL)
5. `port_of_discharge` (Port of Discharge / POD)
6. `container_count` (Total container count, e.g. `6 x 40'HC`)
7. `gross_weight_kg` (Total gross weight in kilograms)

---

## Frontend Integration Contracts

The API endpoints strictly conform to the TypeScript contracts required by the ShipCheck frontend:

```typescript
type EmailType = "Document Comparison" | "New SI Request" | "Invoice Query" | "General" | "Spam";
type EmailStatus = "New" | "Mismatch" | "Match" | "Needs Review" | "Classified" | "Processing";

interface EmailClassifyRequest {
  subject: string;
  snippet: string;
  body: string;
}

interface EmailClassifyResponse {
  type: EmailType;
  confidence: float;
  reasoning?: string;
}

interface ComparisonField {
  field: string;
  si: string;
  bl: string;
  match: boolean;
}

interface CompareResponse {
  status: EmailStatus;
  fields: ComparisonField[];
  summary?: string;
}
```

---

## Setup & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:

```ini
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-v1-...
```

---

## Running the Services

### 1. Start the FastAPI Backend
```bash
uvicorn api.main:app --reload --port 8000
```
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 2. CLI Debugging Tool
Verify an email from the dataset (`inbox/email_NNN.json` and `attachments/`):
```bash
python check_email.py 004
```

### 3. Batch Evaluation
Run across all emails in the dataset and generate `submission.json` and `results.xlsx`:
```bash
python run_full_dataset.py
```

### 4. Process a Folder of `.eml` Files
```bash
python run_eml_folder.py ./emails
```
