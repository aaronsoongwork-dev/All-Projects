/**
 * REST calls to the FastAPI backend.
 *
 * Paths are relative ("/api/..."), which is deliberate: in dev the Vite proxy
 * forwards them to the backend (see vite.config.ts) and in production FastAPI
 * serves the built frontend from its own origin. Same code, no CORS, no
 * environment-dependent base URL.
 */
import { getAccessToken } from "../lib/supabase";
import { BACKEND_LABELS } from "./types";
import type { AnalyzeFileResponse, HealthResponse, ReportRow } from "./types";

/** Thrown for any non-2xx response, carrying the status for call sites. */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function authHeaders(): Promise<Record<string, string>> {
  const token = await getAccessToken();
  // No token in dev mode — the backend accepts this when DISABLE_AUTH=true,
  // and returns 401 otherwise, which is the correct outcome either way.
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Pull a useful message out of FastAPI's error body, whatever shape it is. */
async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      // FastAPI validation errors
      return body.detail.map((d: { msg?: string }) => d.msg).join("; ");
    }
    return JSON.stringify(body);
  } catch {
    return res.statusText || `Request failed (${res.status})`;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {

  let res: Response;
  try {
    const authHeaders_ = await authHeaders();

    const headers = { ...authHeaders_, ...(init.headers ?? {}) };

    res = await fetch(path, {
      ...init,
      headers,
    });
  } catch (error) {
    console.error('❌ Fetch error:', error);
    throw new ApiError(
        "Cannot reach the backend. Is it running on port 8000? (cd backend && uvicorn main:app --reload)",
        0,
    );
  }

  if (!res.ok) {
    const errorMsg = await errorMessage(res);
    console.error('❌ API error:', errorMsg, res.status);
    throw new ApiError(errorMsg, res.status);
  }

  return res.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

export interface QuoteResponse {
  text: string;
  author: string;
}

/** One quote per calendar day, fetched server-side (see main.py's /api/quote —
 *  it calls the upstream quotes API itself so the browser never has to deal
 *  with that API's own CORS policy). Unauthenticated; same for every user. */
export function getQuote(): Promise<QuoteResponse> {
  return request<QuoteResponse>("/api/quote");
}

/** Upload one complete audio file and get a single fused prediction back. */
export function analyzeFile(file: File): Promise<AnalyzeFileResponse> {
  const form = new FormData();
  form.append("file", file);
  // No Content-Type header — the browser must set the multipart boundary.
  return request<AnalyzeFileResponse>("/api/analyze-file", {
    method: "POST",
    body: form,
  });
}

export function getReports(): Promise<ReportRow[]> {
  return request<ReportRow[]>("/api/reports");
}

/** Delete persisted session reports by id. Local-only sessions simply
 *  match nothing server-side; the caller drops them from the store anyway. */
export function deleteReports(ids: string[]): Promise<{ deleted: number }> {
  return request<{ deleted: number }>("/api/reports", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
}

/**
 * Warn (loudly, once) if the backend's label set has drifted from what the
 * UI adapter expects — e.g. someone retrains as 6-class and the frontend is
 * silently dropping two classes. Cheap insurance against a confusing demo.
 */
export function verifyLabels(health: HealthResponse): void {
  const expected = [...BACKEND_LABELS].sort().join(",");
  const actual = [...health.labels].sort().join(",");
  if (expected !== actual) {
    console.warn(
      `[api] Label mismatch — backend serves [${health.labels.join(", ")}] but ` +
        `the UI adapter maps [${BACKEND_LABELS.join(", ")}]. ` +
        `Update BACKEND_LABELS and LABEL_TO_EMOTION in src/app/api/.`,
    );
  }
}
