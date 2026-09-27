# ShipCheck

**AI-powered shipping document verification platform** — built for the Averis x Monash Datathon 2025.

ShipCheck automates one of the most tedious parts of shipping operations: sorting through mass volumes of email correspondence, classifying requests, and manually cross-checking Shipping Instructions (SI) against Bills of Lading (BL) for discrepancies. It reduces manual labor, catches errors humans miss, and flags only the cases that genuinely need a human review.

🔗 **Live site:** [shipcheck.lukewon.tech](https://shipcheck.lukewon.tech)

## Team

Built by **Team Fortress 3** for the Averis x Monash Datathon 2025:

| Member | Role |
|---|---|
| Luke Won | Team Lead |
| Ervin Yap | Full Stack Developer |
| Aaron Soong | Graphic Design & Quality Assurance |
| Shayan Nadeem | Frontend Developer |
| Samuel Zuzartee | Backend Developer |

## Results

Validated against ground-truth results across **520 emails**:

| Metric | Accuracy |
|---|---|
| Email Classification | 100% |
| Discrepancy Detection | 100% (46/46 defects caught) |
| Reliability & Escalation | 100% (20/20 correctly flagged) |

## How it works

Every email passes through three stages, from inbox to discrepancy report:

1. **Classification** — A lightweight classifier (Typesafe Jev AI) sorts incoming emails into one of five categories (BL comparison, SI request, invoice query, general, spam) in under 200ms per email.
2. **Extraction** — Claude Haiku reads each SI and BL document, extracting 7 key fields (shipper, consignee, notify party, port of loading, port of discharge, container count, gross weight). Claude Sonnet handles scanned/image-only documents as a vision fallback.
3. **Comparison** — Fields are normalized (e.g. "Port of Loading" = "Load Port") and compared. A second Haiku pass catches mismatches, and incomplete or corrupted cases are flagged for human review.

Emails can be ingested automatically via Gmail API (using "Login with Google"), or uploaded manually as `.eml` files. Documents can be PDF, DOCX, XLSX, or TXT — including scanned PDFs, which are auto-detected and routed to vision-based OCR.

## Tech stack

- **Frontend:** React + Vite JS, hosted on Cloudflare Pages
- **Backend:** FastAPI on GCP Cloud Run (serverless)
- **Auth & DB:** Supabase
- **Email ingestion:** Gmail API + Google OAuth
- **Classification:** Typesafe Jev AI (via OpenRouter)
- **Document intelligence:** Claude Haiku 4.5 (extraction & comparison), Claude Sonnet 5 (vision OCR fallback)

## Repositories

This project is split across three repos:

- 🖥️ **[email-app-UI](https://github.com/aaronsoongwork-dev/email-app-UI)** — React frontend, dashboard, and review queue
- ⚙️ **[email-app-backend](https://github.com/aaronsoongwork-dev/email-app-backend)** — FastAPI backend, Gmail ingestion, Supabase integration
- 🔍 **[email-extract-compare](https://github.com/aaronsoongwork-dev/email-extract-compare)** — Document extraction and SI/BL comparison pipeline (Claude integration)

Run them together in this order: **backend → extract-compare → UI**. See each repo's README for setup instructions.

## My role

Graphic design and quality assurance — conducted functional and cross-platform testing on the live pipeline, and contributed to the visual identity of the platform (logo, UI design elements).

---
*Originally forked from [Team-Fortress-3](https://github.com/Team-Fortress-3) — this is a personal copy for portfolio purposes. All credit for the original build goes to the full team listed above.*
