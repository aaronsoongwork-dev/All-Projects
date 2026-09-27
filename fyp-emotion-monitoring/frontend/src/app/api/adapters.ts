/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  THE LABEL SEAM — read this before changing the emotion set.
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * The model predicts FIVE labels: Neutral, Happy, Sad, Angry, Frustrated.
 * The UI is built around SIX: those four plus fearful and surprised.
 *
 * Frustrated is mapped to "angry" in the UI since it's the closest match.
 * Rather than spread the mismatch across the six components that render
 * emotions, it is contained here. Every backend response passes through
 * `toEmotionData()`, which fills the two unsupported keys with 0.
 */
import type { Emotion, EmotionData } from "../utils/emotionEngine";
import type { AnalysisSegment, BackendLabel, EmotionResult, LiveReading } from "./types";

/** Backend label -> the frontend's lowercase key. */
const LABEL_TO_EMOTION: Record<BackendLabel, Emotion> = {
  Neutral: "neutral",
  Happy: "happy",
  Sad: "sad",
  Angry: "angry",
  Frustrated: "angry",
};

/** Map one backend label onto the UI's emotion key. */
export function labelToEmotion(label: BackendLabel): Emotion {
  return LABEL_TO_EMOTION[label] ?? "neutral";
}

function emptyScores(): Record<Emotion, number> {
  return { happy: 0, sad: 0, angry: 0, neutral: 0 };
}

/** Map the backend's 4-label probability dict onto the UI's score shape. */
function toScores(probs: Record<BackendLabel, number>): Record<Emotion, number> {
  const scores = emptyScores();
  for (const [label, value] of Object.entries(probs)) {
    const key = LABEL_TO_EMOTION[label as BackendLabel];
    // Ignore labels we don't recognise rather than crashing — if the model is
    // retrained with more classes, the UI degrades instead of breaking.
    if (key) scores[key] = value;
  }
  return scores;
}

/**
 * Convert one backend prediction into the EmotionData the charts consume.
 */
export function toEmotionData(
  timestamp: number,
  transcript: string,
  emotion: EmotionResult,
): EmotionData {
  const fused = toScores(emotion.probs);
  const audio = emotion.audio_emotion ? toScores({ [emotion.audio_emotion.label]: emotion.audio_emotion.confidence } as Record<BackendLabel, number>) : fused;
  const text = emotion.text_emotion ? toScores({ [emotion.text_emotion.label]: emotion.text_emotion.confidence } as Record<BackendLabel, number>) : fused;

  return {
    timestamp,
    audio,
    text,
    fused,
    dominantEmotion: LABEL_TO_EMOTION[emotion.top_label] ?? "neutral",
    confidence: emotion.confidence,
    transcript,
    modalityWeights: emotion.modality_weights,
    audioEmotion: emotion.audio_emotion ? { label: LABEL_TO_EMOTION[emotion.audio_emotion.label] ?? "neutral", confidence: emotion.audio_emotion.confidence } : undefined,
    textEmotion: emotion.text_emotion ? { label: LABEL_TO_EMOTION[emotion.text_emotion.label] ?? "neutral", confidence: emotion.text_emotion.confidence } : undefined,
    isMock: emotion.mock ?? false,
  };
}

/** Convert an uploaded file's analysis windows into a timeline. */
export function segmentsToEmotionData(segments: AnalysisSegment[]): EmotionData[] {
  return segments.map((s) =>
    toEmotionData(Math.round(s.start), s.transcript, s.emotion),
  );
}

/** Convert a stored live session's readings back into chart data. */
export function readingsToEmotionData(readings: LiveReading[]): EmotionData[] {
  if (readings.length === 0) return [];
  const start = readings[0].timestamp;
  return readings.map((r) =>
    toEmotionData(Math.round(r.timestamp - start), r.transcript, r.emotion),
  );
}
