/**
 * Wire types — these mirror the FastAPI responses exactly.
 *
 * Keep this file honest about what the backend actually sends. The
 * translation into the shapes the UI components want lives in adapters.ts.
 */

/**
 * The labels the trained model predicts, in the order preprocess.py's
 * LABEL_MAP defines (neu=0, hap=1, sad=2, ang=3).
 *
 * The backend is the source of truth here — GET /api/health returns this
 * same list, and `verifyLabels()` in client.ts warns if the two ever drift
 * apart (e.g. someone retrains with a 6-class setup and forgets the UI).
 */
export const BACKEND_LABELS = ["Neutral", "Happy", "Sad", "Angry", "Frustrated"] as const;
export type BackendLabel = (typeof BACKEND_LABELS)[number];

/** Per-utterance trust weighting produced by the model's modality_judge. */
export interface ModalityWeights {
  audio: number;
  text: number;
}

export interface EmotionResult {
  probs: Record<BackendLabel, number>;
  top_label: BackendLabel;
  confidence: number;
  modality_weights: ModalityWeights;
  audio_emotion?: { label: BackendLabel; confidence: number };
  text_emotion?: { label: BackendLabel; confidence: number };
  mock?: boolean;
}

/** One 8-second analysis window of an uploaded file. */
export interface AnalysisSegment {
  start: number;
  end: number;
  transcript: string;
  emotion: EmotionResult;
}

export interface AnalyzeFileResponse {
  /** All segment transcripts joined. */
  transcript: string;
  /** Highest-confidence segment, as a single headline result. */
  emotion: EmotionResult;
  /** The real timeline — the model window is fixed at 8s, so long files
   *  are analysed as consecutive windows rather than truncated. */
  segments: AnalysisSegment[];
  /** Majority vote across windows (first-seen wins ties) — the same value
   *  persisted with the report. Absent on rows written before it existed. */
  summary?: {
    dominant_label: BackendLabel | null;
    label_distribution: Record<string, number>;
    average_confidence: number;
  };
  duration_secs: number;
  report_id: string | null;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  mock_mode: boolean;
  auth_disabled: boolean;
  persistence_enabled: boolean;
  labels: string[];
  audio_model: string;
  text_model: string;
}

/** One stored row from GET /api/reports. `data` is the jsonb blob we wrote. */
export interface ReportRow {
  id: string;
  user_id: string;
  created_at: string;
  data: {
    type?: "live" | "upload";
    transcript?: string;
    emotion?: EmotionResult;
    segments?: AnalysisSegment[];
    duration_secs?: number;
    filename?: string;
    readings?: LiveReading[];
    num_chunks?: number;
    summary?: {
      dominant_label: BackendLabel | null;
      label_distribution: Record<string, number>;
      average_confidence: number;
    };
  };
}

// ── Live WebSocket messages ────────────────────────────────────────────────

export interface LiveReading {
  transcript: string;
  emotion: EmotionResult;
  timestamp: number;
}

export type LiveServerMessage =
  | { type: "ready"; chunkBytes: number; sampleRate: number; mock: boolean }
  | {
      type: "reading";
      transcript: string;
      emotion: EmotionResult;
      timestamp: number;
      chunkIndex: number;
    }
  | { type: "summary"; reportId: string | null; numReadings: number }
  | { type: "error"; message: string };
