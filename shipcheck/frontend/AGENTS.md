# AGENTS.md

## Project Overview

**ShipCheck** is a shipping-operations frontend prototype built with **React 19**, **TypeScript**, and **Vite**. It automates maritime and logistics email triage, document comparison between **Shipping Instructions (SI)** and **Bills of Lading (BL)**, discrepancy detection, human review routing, and operational reporting.

The application is designed to run in two modes:
1. **Demo Mode (Default)**: Zero-configuration mode with seeded logistics data and realistic mock workflows.
2. **Gmail API Mode**: Live integration via Google OAuth Web Client to fetch, decode, classify, and inspect actual inbox messages in real time.

---

## Technical Stack & Dependencies

- **Runtime & Language**: Node.js 20+, TypeScript 5.7 (strict mode, bundler module resolution, ES2020 target)
- **UI Framework**: React 19 (`react`, `react-dom`)
- **Build Tool**: Vite 8 with `@vitejs/plugin-react`
- **PDF Extraction**: `pdfjs-dist` (v6.3.289) client-side worker for in-browser PDF parsing
- **Authentication**: `@react-oauth/google` for read-only Gmail access (`https://www.googleapis.com/auth/gmail.readonly`)
- **Styling**: Component-level inline styling + minimal utility CSS (`src/styles/index.css`) featuring an editorial design system (Playfair Display + Inter typography, warm beige palette)

---

## Directory Structure

```text
email-app-UI/
├── .env.example            # Environment variable template (VITE_GOOGLE_CLIENT_ID)
├── .env.local              # Local environment overrides (git-ignored)
├── .gitignore              # Ignored paths: node_modules, dist, .env*, build info
├── index.html              # Single-page app HTML entry point
├── package.json            # Project dependencies and npm scripts
├── tsconfig.json           # Strict TypeScript configuration with '@/*' alias
├── vite.config.ts          # Vite server & build configuration (port 5173, host 0.0.0.0)
└── src/
    ├── main.tsx            # App bootstrap; wraps <App /> in GoogleOAuthProvider
    ├── vite-env.d.ts       # Vite client types
    ├── styles/
    │   └── index.css       # Fonts (@import Playfair Display, Inter), app shell, scrollbars
    └── app/
        └── App.tsx         # Monolithic core containing all types, mock data, services,
                            # UI primitives, and page views (Dashboard, Inbox, Comparison, etc.)
```

---

## Architecture & Data Flow

### 1. State-Driven Routing
Routing is handled within `src/app/App.tsx` via the `Page` union type without external router dependencies:
- `dashboard`: Key operational metrics, status breakdowns, activity feed, and quick actions.
- `inbox`: Filterable, searchable list of incoming logistics emails with badge statuses.
- `email-detail`: Detailed view of selected email, headers, body, attachments, and action to trigger document comparison.
- `processing`: Animated multi-step extraction/processing progress screen.
- `comparison`: Side-by-side comparison table (SI vs BL) showing matching and mismatched logistics fields.
- `review`: Human review queue for flagged discrepancies or unparseable documents.
- `review-detail`: Detail resolution screen for human operators to inspect and resolve mismatches.
- `reports`: Operational analytics, processing volume, match accuracy rates, and error trends.
- `upload`: Client-side drag-and-drop file upload for custom SI and BL PDF documents.
- `upload-comparison`: Comparison results generated directly from uploaded PDF documents.

### 2. Dual Operation Modes
- **Demo Mode**:
  - Activated by clicking **"Continue with Demo Data"** on the login screen or when `VITE_GOOGLE_CLIENT_ID` is unset.
  - Seeds state with 7 realistic logistics emails (`MOCK`), mock comparison rows (`COMPARISON`), and simulated statuses.
  - Users can trigger live AI classification at any time via the **"⚡ Classify with AI"** button.
- **Gmail API Mode**:
  - Triggered with Google OAuth login.
  - Queries `users/me/messages?maxResults=100&q=in:inbox`.
  - Concurrently fetches full message payloads (`users/me/messages/{id}?format=full`).
  - Decodes base64 body content (both plain text and multi-part MIME trees).
  - Triggers asynchronous batch classification via the FastAPI backend (`POST /api/classify`) with bounded concurrency and real-time progress reporting.

### 3. FastAPI AI Backend & SQLite Database Integration (`email-extract-compare`)
- **Proxy Configuration**: `vite.config.ts` proxies `/api` requests to `http://localhost:8000`.
- **Database & Cache Architecture**:
  - `GET /api/emails`: Instant cache-first retrieval (<10ms) of previously classified emails from `shipcheck.db`.
  - `POST /api/emails/batch`: Intelligent caching layer—checks SQLite by message ID; returns existing records at **0 LLM token cost** and only classifies new unclassified messages.
  - `POST /api/compare`: Multipart upload comparing SI and BL; saves results into `ComparisonRecord` and returns `comparison_id`.
  - `GET /api/comparisons`: Fetches historical comparison records for review and operational reporting.
- **Service Layer (`src/services/api.ts`)**:
  - `getCachedEmailsApi(...)`: Instant cache-first retrieval.
  - `syncEmailBatchApi(...)`: Zero-token batch sync to SQLite.
  - `compareFilesApi(...)`: AI file comparison with persistent report storage.
  - `getComparisonsApi(...)`: Comparison history retrieval.
- **Strict Error Handling Protocol**:
  - **No silent fallback to client-side heuristics**: If the backend is down or an endpoint returns an error, the application displays an explicit error alert banner to the user (`AI Backend Error: ...`) and sets error indicators in the TopBar and Inbox.


---

## Design System & Styling Conventions

- **Visual Tone**: Warm editorial, clean typography, high data readability inspired by modern dashboard aesthetics.
- **Palette Tokens**:
  - Background: `#EDEAE2` / `#F0EBE1` (warm beige)
  - Surface: `#F7F5EF` / `#FFFFFF`
  - Primary Navy: `#1B3652` (accent navy: `#264D76`)
  - Ink (Text): `#1A1612`
  - Muted Text: `#6B6560`, Faint: `#A8A298`
  - Borders: `#D8D3C8`, `#E5E1D8`
  - Warning/Mismatch: Amber (`#B45309`, bg: `#FEF3C7`, border: `#F6D860`)
  - Success/Match: Green (`#166534`, bg: `#DCFCE7`, border: `#86EFAC`)
- **Typography**:
  - Headers & accents: `'Playfair Display', ui-serif, Georgia, serif` (`font-serif`)
  - Body & data: `'Inter', ui-sans-serif, system-ui, sans-serif`
- **Shell Layout**:
  - **No nested scrolling**: The browser window is the primary vertical scroll container.
  - Sidebar (`.app-sidebar`): Fixed width 210px (190px on mobile <=800px), sticky positioned at `top: 0`.
  - Top Bar (`.app-topbar`): Sticky positioned at `top: 0`, 44px height.
- **Reusable UI Primitives**:
  - `SectionLabel`: Editorial section header prefixed with an em-dash (`— LABEL STYLE`).
  - `Badge`: Upper-case pill badge with colored background, border, and status dot for `Match`, `Mismatch`, and `Needs Review`.
  - `Divider`: Standard subtle 1px divider.

---

## Essential Commands

> **Windows PowerShell Note**: If PowerShell script execution policies block `npm.ps1`, execute commands via `cmd.exe /c "npm ..."` or `npm.cmd ...`.

```bash
# Start Vite development server (http://localhost:5173)
npm run dev

# Run TypeScript type checks without emitting files
npm run typecheck

# Build for production (tsc project build + Vite bundle into dist/)
npm run build

# Preview production build locally (http://localhost:4173)
npm run preview
```

---

## Guidelines for AI Agents & Contributors

1. **Preserve Design Integrity**:
   - Maintain the warm editorial aesthetic, typography contrast (Playfair Display for headings, Inter for tables/data), and specific color palette.
   - Do not introduce arbitrary generic frameworks (e.g. standard Tailwind or Bootstrap) that clash with the established design tokens.
   - Preserve the sticky shell layout and avoid introducing nested vertical scrollbars.

2. **Code Structure & Refactoring**:
   - `src/app/App.tsx` is currently a monolithic file containing all subcomponents, mock data, and utilities.
   - When modularizing or adding features:
     - Keep extracted components in focused subdirectories under `src/` (e.g. `src/components/`, `src/views/`, `src/services/`, `src/types/`).
     - Retain all `Page`, `EmailType`, `EmailStatus`, and `ComparisonField` type definitions.
     - Ensure path aliases `@/*` (configured in `vite.config.ts` and `tsconfig.json`) are used cleanly.

3. **PDF Worker Handling**:
   - Client-side PDF extraction relies on `pdfjs-dist/build/pdf.worker.mjs`.
   - Never remove or alter `GlobalWorkerOptions.workerSrc` without verifying that client-side PDF file processing and building (`npm run build`) still succeeds.

4. **Authentication & Security**:
   - The Gmail OAuth flow is currently purely browser-based for prototyping.
   - Never commit Google Client Secrets or actual OAuth tokens into git or repository files.
   - Any backend integration should transition token exchange and Gmail API calls to a secure server environment.

5. **Verification Before Committing**:
   - Always verify TypeScript correctness with `npm run typecheck` (or `cmd.exe /c "npm run typecheck"`).
   - Ensure the Vite production bundle builds without errors via `npm run build`.

