import { useSyncExternalStore } from "react";

// Shared emotion types + the in-memory session store.
//
// Real predictions now come from the backend via ../api/ — see
// api/adapters.ts, which converts backend responses into EmotionData. The
// generateMock* helpers below are retained only as fixtures for UI work
// without a running backend; nothing in the live or upload path uses them.
//
// NOTE: the model predicts four labels (neutral/happy/sad/angry). `fearful`
// and `surprised` are placeholders pending the planned UI narrowing — see the
// header comment in api/adapters.ts for how to remove them.
export type Emotion = "happy" | "sad" | "angry" | "neutral";

export interface EmotionData {
  timestamp: number;
  audio: { [key in Emotion]: number };
  text: { [key in Emotion]: number };
  fused: { [key in Emotion]: number };
  dominantEmotion: Emotion;
  confidence: number;
  transcript?: string;
  modalityWeights?: { audio: number; text: number };
  audioEmotion?: { label: Emotion; confidence: number };
  textEmotion?: { label: Emotion; confidence: number };
  isMock?: boolean;
}

export interface Session {
  id: string;
  timestamp: number;
  duration: number;
  type: "live" | "upload";
  /** Original upload filename, when the session came from a file. */
  filename?: string;
  emotionData: EmotionData[];
  summary: {
    dominantEmotion: Emotion;
    averageConfidence: number;
    emotionDistribution: { [key in Emotion]: number };
  };
}

const EMOTIONS: Emotion[] = ["happy", "sad", "angry", "neutral"];

// Generate random emotion probabilities that sum to 1
export function generateEmotionScores(): { [key in Emotion]: number } {
  const scores: Partial<{ [key in Emotion]: number }> = {};
  let remaining = 1;
  
  EMOTIONS.forEach((emotion, index) => {
    if (index === EMOTIONS.length - 1) {
      scores[emotion] = remaining;
    } else {
      const value = Math.random() * remaining;
      scores[emotion] = value;
      remaining -= value;
    }
  });
  
  return scores as { [key in Emotion]: number };
}

// Generate mock emotion data with slight variations
export function generateMockEmotionData(timestamp: number, transcript?: string): EmotionData {
  const audioScores = generateEmotionScores();
  const textScores = generateEmotionScores();
  
  // Attention-based fusion with slight bias toward audio
  const fusedScores: Partial<{ [key in Emotion]: number }> = {};
  const audioWeight = 0.6;
  const textWeight = 0.4;
  
  EMOTIONS.forEach(emotion => {
    fusedScores[emotion] = 
      audioScores[emotion] * audioWeight + 
      textScores[emotion] * textWeight;
  });

  // Find dominant emotion
  const dominantEmotion = EMOTIONS.reduce((a, b) => 
    (fusedScores[a] || 0) > (fusedScores[b] || 0) ? a : b
  );

  return {
    timestamp,
    audio: audioScores,
    text: textScores,
    fused: fusedScores as { [key in Emotion]: number },
    dominantEmotion,
    confidence: fusedScores[dominantEmotion] || 0,
    transcript,
  };
}

// Generate mock transcript
const SAMPLE_PHRASES = [
  "I'm really excited about this project",
  "This is quite frustrating to deal with",
  "Let me explain the situation",
  "I completely understand your concern",
  "That's an interesting point",
  "I'm not sure about that approach",
  "This looks promising",
  "We need to address this immediately",
  "Thank you for your patience",
  "I'm happy to help with this",
];

export function generateMockTranscript(): string {
  return SAMPLE_PHRASES[Math.floor(Math.random() * SAMPLE_PHRASES.length)];
}

// ── Session store ──────────────────────────────────────────────────────────
// In-memory, and the single read point for Dashboard, Reports, Analytics and
// Profile. `hydrateSessions()` fills it from GET /api/reports at app start
// (see contexts/SessionsContext.tsx), so those pages show real persisted data
// without each having to know about the API.
let sessions: Session[] = [];

/** Notified whenever the store changes, so views can re-render. */
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((fn) => fn());
}

export function subscribeToSessions(fn: () => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function addSession(session: Session) {
  // A new array rather than an in-place unshift: useSessionStore() below
  // compares snapshots by reference, so mutating would not re-render.
  sessions = [session, ...sessions].slice(0, 50);
  notify();
}

/**
 * Replace the store with sessions loaded from the backend. Called once on
 * sign-in; sessions created during this browser session are merged in front
 * so a just-finished recording doesn't vanish on refresh-race.
 */
export function hydrateSessions(loaded: Session[]) {
  const loadedIds = new Set(loaded.map((s) => s.id));
  const localOnly = sessions.filter((s) => !loadedIds.has(s.id));
  sessions = [...localOnly, ...loaded].slice(0, 50);
  notify();
}

export function clearSessions() {
  sessions = [];
  notify();
}

/**
 * Drop sessions by id (e.g. after the user deletes them in Reports).
 * Every page reads through useSessionStore(), so one removal updates the
 * whole app — Dashboard, Analytics, Reports, Profile — at once.
 */
export function removeSessions(ids: string[]) {
  if (ids.length === 0) return;
  const doomed = new Set(ids);
  sessions = sessions.filter((s) => !doomed.has(s.id));
  notify();
}

export function getSessions(): Session[] {
  return sessions;
}

/**
 * Subscribe a component to the store.
 *
 * Pages must use this rather than calling getSessions() during render:
 * hydrateSessions() fills the store asynchronously from GET /api/reports
 * after mount, so a bare read captures the empty pre-fetch array and never
 * updates when the real reports land.
 */
export function useSessionStore(): Session[] {
  return useSyncExternalStore(subscribeToSessions, getSessions);
}

export function getSessionById(id: string): Session | undefined {
  return sessions.find(s => s.id === id);
}

// Calculate session summary
export function calculateSessionSummary(emotionData: EmotionData[]) {
  const emotionCounts: { [key in Emotion]: number } = {
    happy: 0,
    sad: 0,
    angry: 0,
    neutral: 0,
  };

  let totalConfidence = 0;

  emotionData.forEach(data => {
    emotionCounts[data.dominantEmotion]++;
    totalConfidence += data.confidence;
  });

  // Ties go to the earliest emotion in canonical order (strict `>=`),
  // matching the backend's first-max-wins convention so a just-saved
  // session doesn't flip its headline emotion after a refresh.
  const dominantEmotion = EMOTIONS.reduce((a, b) =>
    emotionCounts[a] >= emotionCounts[b] ? a : b
  );

  const total = emotionData.length;
  const emotionDistribution: Partial<{ [key in Emotion]: number }> = {};
  EMOTIONS.forEach(emotion => {
    emotionDistribution[emotion] = total > 0 ? emotionCounts[emotion] / total : 0;
  });

  return {
    dominantEmotion,
    averageConfidence: total > 0 ? totalConfidence / total : 0,
    emotionDistribution: emotionDistribution as { [key in Emotion]: number },
  };
}
