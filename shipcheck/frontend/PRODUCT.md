# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary Audience**: Maritime shipping operations teams, logistics coordinators, ocean freight forwarders, and shipping documentation clerks.
- **Operating Situation**: Managing a shared, high-volume operations inbox receiving constant inbound correspondence: document verification requests, new shipping instructions, invoice queries, vessel schedule updates, and spam.
- **Core Job**: Rapidly triage operational emails, verify that draft Bills of Lading (BL) match customer Shipping Instructions (SI) across all critical fields, resolve discrepancies with carriers or shippers, and escalate unresolvable anomalies before documentation cut-offs.

## Product Purpose

ShipCheck automates shipping email classification and maritime document cross-checking (SI vs. BL). It parses incoming logistics emails, reads document attachments, matches counterpart shipment fields side-by-side, surfaces discrepancies, and routes ambiguous or unparseable cases into a structured human-in-the-loop review workflow so that documentation errors are caught before cargo sails.

## Positioning

Unlike generic email inboxes or monolithic freight forwarding ERPs/TMSs, ShipCheck provides zero-token cached email classification, maritime document extraction, and side-by-side discrepancy verification that guarantees transparent human escalation instead of silent failures or hallucinated data.

## Operating Context

- **Multi-Party Influx**: Constant streams of messages from ocean carriers (e.g., Maersk, MSC, CMA CGM, Hapag-Lloyd, ONE), shippers, consignees, customs brokers, and port agents.
- **Noisy Document Formats**: Semi-structured, multi-page PDF documents (Shipper's Letter of Instruction / SI vs. Carrier Draft Sea Waybill / BL).
- **Cut-Off Pressure**: Time-critical documentation and sailing cut-off deadlines where typographical or numeric mismatches in container numbers, seal numbers, piece counts, gross weight, cargo description, or ports result in customs holds, rollover fees, or bill reissuance penalties.

## Capabilities and Constraints

- **Classify**: Categorize incoming emails into distinct operational intents:
  - Document Comparison Requests (`comparison`)
  - New SI Requests (`new_si`)
  - Invoice Queries (`invoice`)
  - General Operations (`general`)
  - Spam / Marketing (`spam`)
- **Extract Data**: Ingest SI and BL documents via Gmail attachments or manual PDF file upload. Extract structured shipment attributes:
  - Shipper, Consignee, Notify Party
  - Vessel, Voyage
  - Container Number, Seal Number
  - Piece Count / Package Type, Gross Weight, Measurement / Volume
  - Cargo Description
  - Port of Loading (POL), Port of Discharge (POD)
- **Compare**: Automated field-level cross-comparison highlighting exact matches and discrepancies side-by-side with visual status indicators.
- **Human-in-the-Loop Escalation**: When extraction or comparison confidence is insufficient or fields mismatch, route the case to a dedicated review queue with email context, attachment links, and side-by-side discrepancy details.
- **Dual Operational Modes**:
  - *Live Gmail API Mode*: OAuth-based read-only inbox sync, fetching messages, decoding MIME bodies, and batching unclassified emails through the backend.
  - *Demo Mode*: Seeded realistic maritime emails and mock comparisons for zero-config testing and evaluation.
- **Stand-alone Upload & Compare**: Direct drag-and-drop file upload for ad-hoc SI and BL PDF comparison.
- **Caching Architecture**: Zero-token cached email retrieval from backend SQLite (`shipcheck.db`), only incurring LLM tokens for new unclassified messages.
- **Technical Constraints**: Client-side read-only Gmail access (`https://www.googleapis.com/auth/gmail.readonly`), FastAPI backend proxy (`/api`), client-side PDF parsing via `pdfjs-dist`. Strict error boundary with prominent user alerts if the backend is unavailable (no silent fallback).

## Brand Commitments

- **Name**: ShipCheck.
- **Visual Tone**: Warm editorial maritime aesthetic combining serif headlines (`Playfair Display`) with crisp, high-density data tables and badges (`Inter`).
- **Palette**: Warm beige/cream surfaces (`#EDEAE2`, `#F7F5EF`, `#FFFFFF`), deep maritime navy (`#1B3652`), ink text (`#1A1612`), with distinct amber (`#B45309`) and green (`#166534`) status tokens.
- **Shell Architecture**: Sticky sidebar and topbar; single primary window scrolling without nested vertical scrollbars.

## Evidence on Hand

- 7 seeded realistic logistics emails with full threads, statuses, and field payloads in `src/pages/InboxPage.tsx` / `App.tsx`.
- Comprehensive comparison field schemas and mock comparison pairs (`COMPARISON`).
- Live backend integration endpoints in `src/services/api.ts` (`/api/emails`, `/api/emails/batch`, `/api/compare`, `/api/comparisons`).
- Supabase client integration in `src/services/supabase.ts`.
- Client-side PDF parsing pipeline via `pdfjs-dist`.

## Product Principles

1. **Never guess, never fail silently**: When extraction or matching confidence is low, escalate to human review with all relevant context preserved.
2. **High-density operational clarity**: Prioritize immediate scanability and side-by-side contrast over decorative flair; operators must spot errors in seconds.
3. **Zero-token efficiency & fast retrieval**: Cache classified communications aggressively to keep latency low (<10ms) and LLM costs predictable.
4. **Uncompromised auditability**: Maintain clear provenance between raw email attachments, extracted values, and final comparison statuses.
