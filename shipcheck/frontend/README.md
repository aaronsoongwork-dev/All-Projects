# ShipCheck Frontend

React + Vite frontend for the Averis ShipCheck shipping-operations prototype.

## What is included

- Dashboard, inbox, email detail, processing, comparison, review queue, reports, and upload/compare flows.
- Demo mode with seeded shipping-email data, so the app runs without credentials.
- Optional Google OAuth + Gmail read-only access through the Gmail API.
- Client-side PDF text extraction and SI vs Bill of Lading comparison.
- Responsive project structure that matches the intended `frontend/src/app` + `frontend/src/styles` layout.

## Requirements

Use a recent Node.js version (Node 20+ recommended) and npm.

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:5173`.

### Demo mode

No environment variable is required. With `VITE_GOOGLE_CLIENT_ID` empty, the login screen provides **Continue with Demo Data**.

### Gmail mode

Create a Google OAuth Web application and set:

```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

For local development, add `http://localhost:5173` to the OAuth client's authorized JavaScript origins. The app requests read-only Gmail access plus basic Google profile information.

> The Gmail token is used directly by the browser for this prototype. For production, move OAuth/token handling behind a backend and apply your organization's security and consent requirements.

## Commands

```bash
npm run dev       # local development
npm run typecheck # TypeScript checks
npm run build     # production build
npm run preview   # preview the production build
```

## Frontend layout

```text
frontend/
├── .env.example
├── .gitignore
├── index.html
├── package.json
├── README.md
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── app/
    │   └── App.tsx
    ├── styles/
    │   └── index.css
    ├── main.tsx
    └── vite-env.d.ts
```
