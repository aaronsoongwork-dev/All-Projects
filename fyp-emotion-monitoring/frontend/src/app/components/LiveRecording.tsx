import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { Mic, Square, Play, Pause, Waves, Mic as MicIcon} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Button } from "./ui/button";
import {
  addSession, calculateSessionSummary, type EmotionData, type Emotion,
} from "../utils/emotionEngine";
import { LiveSession } from "../api/liveSession";
import { toEmotionData } from "../api/adapters";
import { useSessions } from "../contexts/SessionsContext";
import { toast } from "sonner";
import { getSessions, type Session } from "../utils/emotionEngine"; // add Session + getSessions to existing import
import {SessionDetailsDialog} from "./SessionDetailsDialog.tsx";

const EMOTION_COLORS: { [key in Emotion]: string } = {
  happy: "#c07c20", sad: "#1e5f8a", angry: "#b8312f",
  neutral: "#786c5c"
};

const serif = "'Playfair Display', Georgia, serif";
const sans = "'IBM Plex Sans', system-ui, sans-serif";
const mono = "'IBM Plex Mono', monospace";

/**
 * Scrolling display of real microphone level. `level` is the peak amplitude
 * (0..1) of the most recent audio frame, pushed up from LiveSession — these
 * bars now reflect actual input rather than an animation, so a dead mic is
 * visible immediately instead of looking like it's working.
 */
function WaveformBars({ active, level }: { active: boolean; level: number }) {
  const BARS = 32;
  const [history, setHistory] = useState<number[]>(() => new Array(BARS).fill(0));

  useEffect(() => {
    if (!active) {
      setHistory(new Array(BARS).fill(0));
      return;
    }
    // Sampled on an interval rather than on every frame: audio callbacks fire
    // far faster than the display needs, and re-rendering on each would churn.
    const id = setInterval(() => {
      setHistory((prev) => [...prev.slice(1), levelRef.current]);
    }, 60);
    return () => clearInterval(id);
  }, [active]);

  const levelRef = useRef(level);
  levelRef.current = level;

  return (
      <div className="flex items-center justify-center gap-[2px] h-8">
        {history.map((v, i) => (
            <div
                key={i}
                style={{
                  width: 2,
                  backgroundColor: active ? "var(--primary)" : "var(--muted-foreground)",
                  opacity: active ? 0.35 + Math.min(v * 2, 1) * 0.65 : 0.2,
                  // sqrt curve: quiet speech is otherwise almost invisible
                  height: active ? `${Math.max(8, Math.sqrt(Math.min(v, 1)) * 100)}%` : "15%",
                  transition: "height 0.08s linear, opacity 0.08s linear",
                }}
            />
        ))}
      </div>
  );
}

function getDominantWithScore(scores: { [key in Emotion]: number }) {
  const entries = Object.entries(scores) as [Emotion, number][];
  const dominant = entries.reduce((a, b) => (a[1] > b[1] ? a : b));
  return { emotion: dominant[0], confidence: dominant[1] };
}

/* ── Recent Live Sessions Panel ── */
function RecentLiveSessions({ onViewSession }: { onViewSession?: (session: Session) => void }) {
  const sessions = getSessions().filter((s) => s.type === "live").slice(0, 5);

  if (sessions.length === 0) return null;

  return (
      <div>
        <p className="text-[11px] tracking-[0.2em] uppercase text-muted-foreground font-normal mb-3" style={{ fontFamily: sans }}>
          Recent Live Sessions
        </p>
        <div className="border" style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}>
          <div className="divide-y" style={{ borderColor: "var(--border)" }}>
          {sessions.map((session) => {
            const dominant = session.summary.dominantEmotion;
            return (
                <div key={session.id} className="flex items-center gap-4 px-5 py-4">
                  <div
                      className="flex-shrink-0 flex items-center justify-center border"
                      style={{ width: 40, height: 40, borderColor: "var(--border)", backgroundColor: "var(--muted)" }}
                  >
                    <MicIcon style={{ width: 16, height: 16, color: "var(--muted-foreground)" }} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-normal text-foreground truncate" style={{ fontFamily: sans }}>
                      Live session · {new Date(session.timestamp).toLocaleDateString()}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5 font-normal" style={{ fontFamily: sans }}>
                      {Math.floor(session.duration / 60)}:{(session.duration % 60).toString().padStart(2, "0")} min
                      &nbsp;·&nbsp;
                      <span style={{ color: EMOTION_COLORS[dominant] }} className="capitalize">{dominant}</span>
                    </p>
                  </div>

                  <button
                      className="flex-shrink-0 px-3 py-1.5 border text-[11px] tracking-[0.14em] uppercase font-normal transition-colors hover:bg-muted"
                      style={{ borderColor: "var(--border)", fontFamily: sans, color: "var(--foreground)" }}
                      onClick={() => onViewSession?.(session)}
                  >
                    View
                  </button>
                </div>
            );
          })}
          </div>
        </div>
      </div>
  );
}

export function LiveRecording() {
  const navigate = useNavigate();
  const { health, isMock, refreshSessions } = useSessions();
  const [isRecording, setIsRecording] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [duration, setDuration] = useState(0);
  const [level, setLevel] = useState(0);
  const [emotionData, setEmotionData] = useState<EmotionData[]>([]);
  const [currentEmotion, setCurrentEmotion] = useState<EmotionData | null>(null);
  const windowEmotionDataRef = useRef<EmotionData[]>([]);
  const WINDOW_SECS = 5;
  const [transcript, setTranscript] = useState<{ time: number; text: string; emotion: Emotion }[]>([]);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const [viewedSession, setViewedSession] = useState<Session | null>(null);

  const sessionRef = useRef<LiveSession | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);
  const pausedTimeRef = useRef<number>(0);
  const pauseStartRef = useRef<number>(0);

  // Elapsed-time display only. Predictions arrive from the server whenever a
  // chunk completes — they are not on this clock.
  useEffect(() => {
    if (isRecording && !isPaused) {
      intervalRef.current = setInterval(() => {
        setDuration(
          Math.floor((Date.now() - startTimeRef.current - pausedTimeRef.current) / 1000),
        );
      }, 1000);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [isRecording, isPaused]);

  // Releases the mic and socket if the user navigates away mid-session.
  useEffect(() => () => sessionRef.current?.teardown(), []);

  // Auto-follow new transcript lines while recording. Skipped when the
  // transcript is empty so navigating to the page doesn't yank the scroll
  // position down on mount.
  useEffect(() => {
    if (transcript.length === 0) return;
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [transcript]);

  const startRecording = async () => {
    setIsConnecting(true);
    setEmotionData([]);
    windowEmotionDataRef.current = [];
    setTranscript([]);
    setCurrentEmotion(null);
    setDuration(0);

    const session = new LiveSession({
      onLevel: setLevel,
      onProcessing: setIsProcessing,
      onReading: ({ transcript: text, emotion, timestamp }) => {
        const elapsed = Math.max(
            0,
            Math.round((timestamp * 1000 - startTimeRef.current) / 1000),
        );
        const reading = toEmotionData(elapsed, text, emotion);
        setEmotionData((prev) => [...prev, reading]);

        // Rolling window average, kept in a ref rather than state — this is
        // an internal computation input, not something the UI renders
        // directly, so it doesn't need to trigger its own re-render.
        const windowStart = elapsed - WINDOW_SECS;
        const updated = [...windowEmotionDataRef.current, reading].filter(
            (r) => r.timestamp >= windowStart,
        );
        windowEmotionDataRef.current = updated;

        if (updated.length > 0) {
          const avgFused = {happy: 0, sad: 0, angry: 0, neutral: 0};
          for (const r of updated) {
            for (const k of Object.keys(avgFused) as (keyof typeof avgFused)[]) {
              avgFused[k] += r.fused[k];
            }
          }
          for (const k of Object.keys(avgFused) as (keyof typeof avgFused)[]) {
            avgFused[k] /= updated.length;
          }
          const entries = Object.entries(avgFused) as [Emotion, number][];
          const dominant = entries.reduce((a, b) => (a[1] > b[1] ? a : b));

          setCurrentEmotion({
            timestamp: elapsed,
            fused: avgFused,
            audio: avgFused,
            text: avgFused,
            dominantEmotion: dominant[0],
            confidence: dominant[1],
            isMock: reading.isMock,
            modalityWeights: reading.modalityWeights,
            audioEmotion: reading.audioEmotion,
            textEmotion: reading.textEmotion,
          });
        }

        // Whisper returns "" for silence — no point adding an empty line.
        if (text.trim()) {
          setTranscript((prev) => [
            ...prev,
            { time: elapsed, text, emotion: reading.dominantEmotion },
          ]);
        }
      },
      onError: (message) => toast.error(message),
    });

    try {
      await session.start();
    } catch (err) {
      session.teardown();
      setIsConnecting(false);
      const message = err instanceof Error ? err.message : String(err);
      if (err instanceof DOMException) {
        toast.error(
            err.name === "NotAllowedError"
                ? "Microphone access denied. Allow it in your browser settings and try again."
                : "Could not access the microphone.",
        );
      } else {
        toast.error(message);
      }
      return;
    }

    sessionRef.current = session;
    startTimeRef.current = Date.now();
    pausedTimeRef.current = 0;
    setIsConnecting(false);
    setIsRecording(true);
    setIsPaused(false);
    toast.success(
        isMock ? "Analysis started (mock mode — placeholder results)" : "Analysis started",
    );
  };

  const pauseRecording = () => {
    pauseStartRef.current = Date.now();
    sessionRef.current?.setMuted(true);
    setIsPaused(true);
    setLevel(0);
    toast.info("Analysis paused");
  };

  const resumeRecording = () => {
    pausedTimeRef.current += Date.now() - pauseStartRef.current;
    sessionRef.current?.setMuted(false);
    setIsPaused(false);
    toast.info("Analysis resumed");
  };

  const stopRecording = async () => {
    const session = sessionRef.current;
    setIsSaving(true);
    setLevel(0);

    // The server still has to process the final partial chunk, so this can
    // take a few seconds — hence the saving state on the button.
    const reportId = (await session?.stop()) ?? null;
    sessionRef.current = null;

    setIsRecording(false);
    setIsPaused(false);
    setIsSaving(false);
    setIsProcessing(false);

    if (emotionData.length === 0) {
      // An empty session is discarded completely and returns to a fresh state.
      setDuration(0);
      setEmotionData([]);
      windowEmotionDataRef.current = [];
      setTranscript([]);
      setCurrentEmotion(null);
      startTimeRef.current = 0;
      pausedTimeRef.current = 0;
      pauseStartRef.current = 0;
      toast.error("No speech was analysed — nothing to save");
      return;
    }

    // Mirror the saved session locally so the dashboard updates instantly.
    // Using the backend's report id keeps this row from duplicating when the
    // store is later rehydrated from /api/reports.
    addSession({
      id: reportId ?? `local-${Date.now()}`,
      timestamp: Date.now(),
      duration,
      type: "live",
      emotionData,
      summary: calculateSessionSummary(emotionData),
    });

    if (reportId) {
      toast.success("Analysis saved");
      void refreshSessions();
    } else {
      toast.warning("Analysis complete, but it could not be saved to the server");
    }
    setTimeout(() => navigate("/"), 1500);
  };

  const chartData = emotionData.slice(-20).map((data) => ({
    time: `${data.timestamp}s`,
    happy: (data.fused.happy * 100).toFixed(1),
    sad: (data.fused.sad * 100).toFixed(1),
    angry: (data.fused.angry * 100).toFixed(1),
    neutral: (data.fused.neutral * 100).toFixed(1),
  }));

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const isActive = isRecording && !isPaused;
  const fusedResult = currentEmotion ? getDominantWithScore(currentEmotion.fused) : null;
  const weights = currentEmotion?.modalityWeights ?? null;
  const backendReachable = health !== null;

  const tooltipStyle = {
    background: "var(--card)", border: "1px solid var(--border)", borderRadius: 0,
    boxShadow: "none", color: "var(--card-foreground)", fontSize: 12, fontFamily: sans,
  };
  const axisStyle = { fontSize: 11, fill: "var(--muted-foreground)", fontFamily: sans };

  return (
      <div className="min-h-full bg-background">
        <style>{`
        @keyframes waveBar { from { transform: scaleY(0.3); } to { transform: scaleY(1); } }
      `}</style>

        <div className="max-w-7xl mx-auto p-8">
          {/* Page header */}
          <div className="border-b mb-8 pb-6" style={{ borderColor: "var(--border)" }}>
            <div className="flex items-start justify-between">
              <div>
                <h1
                    className="font-bold text-foreground leading-tight"
                    style={{ fontFamily: serif, fontSize: "clamp(1.75rem, 3vw, 2.5rem)", letterSpacing: "-0.02em" }}
                >
                  Live Emotion{" "}
                  <em style={{ fontStyle: "italic", color: "var(--primary)" }}>Analysis</em>
                </h1>
                <p className="text-sm text-muted-foreground mt-1.5" style={{ fontFamily: sans, fontWeight: 300 }}>
                  Real-time audio-text fusion · attention-based multimodal analysis
                </p>
              </div>
              {isActive && (
                  <div
                      className="flex items-center gap-2 px-3 py-1.5 border"
                      style={{ borderColor: "var(--primary)", color: "var(--primary)" }}
                  >
                <span
                    className="size-1.5 rounded-full animate-pulse inline-block"
                    style={{ backgroundColor: "var(--primary)" }}
                />
                    <span className="text-xs tracking-[0.2em] uppercase font-semibold" style={{ fontFamily: sans }}>
                  Live
                </span>
                  </div>
              )}
            </div>
          </div>

          {/* Results shown here are only as real as the backend serving them —
              say so plainly rather than letting placeholders look like data. */}
          {!backendReachable && (
              <div className="border-l-2 px-4 py-3 mb-8" style={{ borderColor: "#b8312f", backgroundColor: "var(--card)" }}>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] mb-1" style={{ color: "#b8312f", fontFamily: sans }}>
                  Backend unreachable
                </p>
                <p className="text-xs text-muted-foreground" style={{ fontFamily: sans }}>
                  Start it with <span style={{ fontFamily: mono }}>cd backend &amp;&amp; uvicorn main:app --reload --port 8000</span>, then reload this page.
                </p>
              </div>
          )}
          {backendReachable && isMock && (
              <div className="border-l-2 px-4 py-3 mb-8" style={{ borderColor: "#c07c20", backgroundColor: "var(--card)" }}>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] mb-1" style={{ color: "#c07c20", fontFamily: sans }}>
                  Mock mode
                </p>
                <p className="text-xs text-muted-foreground" style={{ fontFamily: sans }}>
                  Transcripts and emotion scores below are randomised placeholders — the trained checkpoint isn't loaded. The full pipeline is running; only the predictions are fake.
                </p>
              </div>
          )}

          {/* Main layout */}
          <div className="grid grid-cols-1 xl:grid-cols-[320px_1fr] gap-8 items-stretch">

            {/* ── Recorder Control ── */}
            <div className="flex flex-col gap-6 h-full">
              <div className="flex flex-1 flex-col">
                <p className="text-xs tracking-[0.2em] uppercase text-muted-foreground mb-3" style={{ fontFamily: sans }}>
                  Analysis Control
                </p>
                <div
                    className="border flex flex-1 flex-col"
                    style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}
                >
                  {/* Color bar */}
                  <div
                      className="h-0.5 w-full transition-all duration-700"
                      style={{
                        backgroundColor: isActive ? "var(--primary)" : isPaused ? "#c07c20" : "var(--muted)",
                      }}
                  />

                  <div className="p-7 flex flex-1 flex-col items-center justify-center gap-5">
                    {/* Mic button */}
                    <div className="relative flex items-center justify-center mt-2">
                      {isActive && (
                          <>
                            <div className="absolute size-28 opacity-10 animate-ping" style={{ backgroundColor: "var(--primary)", borderRadius: 0 }} />
                            <div className="absolute size-20 opacity-10" style={{ backgroundColor: "var(--primary)", borderRadius: 0, animation: "ping 1.4s ease-out 0.5s infinite" }} />
                          </>
                      )}
                      <button
                          onClick={!isRecording && !isConnecting ? startRecording : undefined}
                          disabled={isRecording || isConnecting || !backendReachable}
                          title={backendReachable ? undefined : "Backend is not running"}
                          className="relative flex items-center justify-center transition-all duration-200"
                          style={{
                            width: 80, height: 80,
                            borderRadius: 0,
                            backgroundColor: !isRecording ? "var(--foreground)" : isActive ? "var(--primary)" : "#c07c20",
                            cursor: !isRecording && backendReachable && !isConnecting ? "pointer" : "not-allowed",
                            opacity: backendReachable ? 1 : 0.4,
                          }}
                      >
                        {isConnecting ? (
                            <span className="size-6 rounded-full border-2 border-background/30 border-t-background animate-spin" />
                        ) : (
                            <Mic style={{ width: 28, height: 28, color: isActive ? "var(--card)" : "var(--background)" }} />
                        )}
                      </button>
                    </div>

                    {/* Timer */}
                    <div className="text-center">
                      <div
                          className="text-5xl leading-none tabular-nums"
                          style={{
                            fontFamily: mono,
                            fontWeight: 400,
                            letterSpacing: "0.06em",
                            color: isActive ? "var(--primary)" : "var(--foreground)",
                          }}
                      >
                        {formatDuration(duration)}
                      </div>
                      <div className="mt-2 h-4 flex items-center justify-center">
                        {isActive && (
                            <span className="text-xs tracking-[0.2em] uppercase font-semibold" style={{ color: "var(--primary)", fontFamily: sans }}>
                          Analysing
                        </span>
                        )}
                        {isPaused && (
                            <span className="text-xs tracking-[0.2em] uppercase font-semibold" style={{ color: "#c07c20", fontFamily: sans }}>
                          Paused
                        </span>
                        )}
                        {isConnecting && (
                            <span className="text-xs tracking-[0.2em] uppercase font-semibold text-muted-foreground" style={{ fontFamily: sans }}>
                          Connecting
                        </span>
                        )}
                        {!isRecording && !isConnecting && duration === 0 && (
                            <span className="text-xs text-muted-foreground tracking-wider" style={{ fontFamily: sans }}>
                          {backendReachable ? "Tap to begin" : "Backend offline"}
                        </span>
                        )}
                      </div>
                    </div>

                    <div className="w-full"><WaveformBars active={isActive} level={level} /></div>

                    {isProcessing && isActive && (
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <span className="size-1.5 rounded-full animate-pulse inline-block" style={{ backgroundColor: "var(--primary)" }} />
                          <span className="text-xs tracking-wider uppercase" style={{ fontFamily: sans, color: "var(--primary)" }}>
                            Processing…
                          </span>
                        </div>
                    )}

                    {isRecording && (
                        <div className="flex gap-2 w-full">
                          {!isPaused ? (
                              <Button
                                  variant="outline"
                                  onClick={pauseRecording}
                                  className="flex-1 text-xs font-semibold uppercase tracking-wider py-2"
                                  style={{ fontFamily: sans, borderRadius: 0, borderColor: "var(--border)" }}
                              >
                                <Pause style={{ width: 14, height: 14, marginRight: 6 }} />
                                Pause
                              </Button>
                          ) : (
                              <Button
                                  variant="outline"
                                  onClick={resumeRecording}
                                  className="flex-1 text-xs font-semibold uppercase tracking-wider py-2"
                                  style={{ fontFamily: sans, borderRadius: 0, borderColor: "var(--border)" }}
                              >
                                <Play style={{ width: 14, height: 14, marginRight: 6 }} />
                                Resume
                              </Button>
                          )}
                          <Button
                              onClick={stopRecording}
                              disabled={isSaving}
                              className="flex-1 text-xs font-semibold uppercase tracking-wider py-2"
                              style={{
                                fontFamily: sans, borderRadius: 0,
                                backgroundColor: "var(--foreground)", color: "var(--background)",
                              }}
                          >
                            {isSaving ? (
                                <>
                                  <span className="size-3 rounded-full border-2 border-background/30 border-t-background animate-spin mr-1.5" />
                                  Saving…
                                </>
                            ) : (
                                <>
                                  <Square style={{ width: 14, height: 14, marginRight: 6 }} />
                                  Stop & Save
                                </>
                            )}
                          </Button>
                        </div>
                    )}

                    {emotionData.length > 0 && (
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Waves style={{ width: 14, height: 14 }} />
                          <span className="text-xs tabular-nums" style={{ fontFamily: mono }}>
                        {emotionData.length} data points
                      </span>
                        </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Score breakdown */}
              {currentEmotion && (
                  <div>
                    <p className="text-xs tracking-[0.2em] uppercase text-muted-foreground mb-3" style={{ fontFamily: sans }}>
                      Fused Score Breakdown
                    </p>
                    <div className="border p-4 space-y-3" style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}>
                      {Object.entries(currentEmotion.fused)
                          .sort((a, b) => b[1] - a[1])
                          .map(([emotion, value]) => (
                              <div key={emotion} className="flex items-center gap-3">
                        <span className="text-xs w-16 capitalize tracking-wide text-muted-foreground" style={{ fontFamily: sans }}>
                          {emotion}
                        </span>
                                <div className="flex-1 h-1.5" style={{ backgroundColor: "var(--muted)" }}>
                                  <div
                                      className="h-full transition-all duration-500"
                                      style={{ width: `${(value * 100).toFixed(1)}%`, backgroundColor: EMOTION_COLORS[emotion as Emotion] }}
                                  />
                                </div>
                                <span className="text-xs tabular-nums w-8 text-right text-muted-foreground" style={{ fontFamily: mono }}>
                          {(value * 100).toFixed(0)}%
                        </span>
                              </div>
                          ))}
                    </div>
                  </div>
              )}
            </div>

            {/* ── Right panel ── */}
            <div className="space-y-6">

              {/* Live Transcription */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs tracking-[0.2em] uppercase text-muted-foreground" style={{ fontFamily: sans }}>
                    Live Transcription
                  </p>
                  {isActive && (
                      <span className="flex items-center gap-1.5 text-xs tracking-widest uppercase font-semibold" style={{ color: "#2e7d52", fontFamily: sans }}>
                    <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse inline-block" />
                    Streaming
                  </span>
                  )}
                </div>
                <div
                    className="border p-4"
                    style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}
                >
                  <div
                      className="min-h-[130px] max-h-48 overflow-y-auto border p-4 space-y-3"
                      style={{ borderColor: "var(--border)", backgroundColor: "var(--background)" }}
                  >
                    {transcript.length === 0 ? (
                        <p className="text-sm text-muted-foreground/50 italic" style={{ fontFamily: serif }}>
                          Transcribed text will appear here in real-time...
                        </p>
                    ) : (
                        transcript.map((entry, index) => (
                            <div key={index} className="flex items-start gap-3">
                        <span className="text-xs text-muted-foreground/60 tabular-nums pt-0.5 w-7 flex-shrink-0" style={{ fontFamily: mono }}>
                          {entry.time}s
                        </span>
                              <span
                                  className="text-xs px-1.5 py-0.5 flex-shrink-0 tracking-widest uppercase font-semibold"
                                  style={{ backgroundColor: "var(--muted)", color: EMOTION_COLORS[entry.emotion], fontFamily: sans }}
                              >
                          {entry.emotion}
                        </span>
                              <span className="text-sm text-foreground leading-relaxed" style={{ fontFamily: sans, fontWeight: 400, wordBreak: "break-word" }}>
                          {entry.text}
                        </span>
                            </div>
                        ))
                    )}
                    <div ref={transcriptEndRef} />
                  </div>
                </div>
              </div>

              {/* Real-Time Prediction */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs tracking-[0.2em] uppercase text-muted-foreground" style={{ fontFamily: sans }}>
                    Real-Time Emotion Prediction
                  </p>
                  <span className="flex items-center gap-1.5 text-xs uppercase tracking-wide text-muted-foreground" style={{ fontFamily: sans }}>
                  <span className="size-1.5 rounded-full inline-block" style={{ backgroundColor: isActive ? "var(--primary)" : "var(--muted-foreground)", opacity: isActive ? 1 : 0.4 }} />
                    {isActive ? "Analyzing" : currentEmotion ? "Last Result" : "Awaiting Input"}
                </span>
                </div>

                <div
                    className="border p-5"
                    style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}
                >
                  {/*
                    The model has a single classifier over the fused audio+text
                    vector, so there is no audio-only or text-only emotion label
                    to show. What IS per-modality is the trust weighting the
                    model computes for each utterance (its modality_judge), so
                    that is what's displayed alongside the one real prediction.
                  */}
                  <div className="grid grid-cols-1 md:grid-cols-[1fr_1.2fr] gap-5">

                    {/* Fused prediction — the model's actual output */}
                    <div>
                      <span className="text-xs tracking-[0.14em] uppercase font-semibold block mb-3" style={{ fontFamily: sans, color: "var(--foreground)" }}>
                        Fused Prediction
                      </span>
                      <div
                          className="border p-4 flex flex-col items-center justify-center gap-1.5 min-h-[130px]"
                          style={{ borderColor: "var(--foreground)", backgroundColor: "var(--muted)" }}
                      >
                        {fusedResult ? (
                            <>
                              <span className="text-lg font-bold capitalize" style={{ fontFamily: serif, color: EMOTION_COLORS[fusedResult.emotion] }}>
                            {fusedResult.emotion}
                          </span>
                              <span className="text-xs text-muted-foreground" style={{ fontFamily: mono }}>
                            {(fusedResult.confidence * 100).toFixed(0)}% confidence
                          </span>
                            </>
                        ) : (
                            <span className="text-sm text-muted-foreground/50 italic" style={{ fontFamily: serif }}>
                              Awaiting first chunk…
                            </span>
                        )}
                      </div>
                    </div>

                    {/* Live modality trust weights */}
                    <div>
                      <span className="text-xs tracking-[0.14em] uppercase font-semibold block mb-3" style={{ fontFamily: sans, color: "var(--muted-foreground)" }}>
                        Modality Trust · Audio vs Text
                      </span>
                      <div
                          className="border p-4 min-h-[130px] flex flex-col justify-center gap-4"
                          style={{ borderColor: "var(--border)", borderStyle: "dashed", backgroundColor: "var(--background)" }}
                      >
                        {weights ? (
                            <>
                              {([
                                { label: "Audio", value: weights.audio, color: "var(--primary)", emotion: currentEmotion?.audioEmotion },
                                { label: "Text", value: weights.text, color: "#1e5f8a", emotion: currentEmotion?.textEmotion },
                              ] as const).map((row) => (
                                  <div key={row.label} className="flex items-center gap-3">
                                <span className="text-xs w-16 tracking-wide uppercase text-muted-foreground" style={{ fontFamily: sans }}>
                      {row.label}
                    </span>
                                    <div className="flex-1 h-2" style={{ backgroundColor: "var(--muted)" }}>
                                      <div
                                          className="h-full transition-all duration-500"
                                          style={{ width: `${(row.value * 100).toFixed(1)}%`, backgroundColor: row.color }}
                                      />
                                    </div>
                                    <span className="text-xs tabular-nums w-9 text-right text-muted-foreground" style={{ fontFamily: mono }}>
                                  {(row.value * 100).toFixed(0)}%
                                </span>
                                    {row.emotion && (
                                        <span
                                            className="text-xs px-1.5 py-0.5 uppercase font-semibold tracking-wider"
                                            style={{ backgroundColor: "var(--muted)", color: EMOTION_COLORS[row.emotion.label as Emotion] ?? "var(--foreground)", fontFamily: sans }}
                                        >
                                      {row.emotion.label}
                                    </span>
                                    )}
                                  </div>
                              ))}
                              <p className="text-xs text-muted-foreground/60 leading-snug mt-1" style={{ fontFamily: sans }}>
                                Audio = tone/pitch · Text = words · Fused = combined
                              </p>
                            </>
                        ) : (
                            <span className="text-sm text-muted-foreground/50 italic text-center" style={{ fontFamily: serif }}>—</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Timeline chart */}
              {emotionData.length > 0 && (
                  <div>
                    <p className="text-xs tracking-[0.2em] uppercase text-muted-foreground mb-3" style={{ fontFamily: sans }}>
                      Emotion Timeline
                    </p>
                    <div className="border p-5" style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}>
                      <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="2 2" stroke="var(--border)" />
                          <XAxis dataKey="time" tick={axisStyle} />
                          <YAxis tick={axisStyle} />
                          <Tooltip contentStyle={tooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: 11, fontFamily: sans, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted-foreground)" }} />
                          {(Object.keys(EMOTION_COLORS) as Emotion[]).map((e) => (
                              <Line key={e} type="monotone" dataKey={e} stroke={EMOTION_COLORS[e]} strokeWidth={1.5} dot={false} />
                          ))}
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
              )}
            </div>
          </div>
        </div>

        {/* Recent live sessions — hidden while a session is actively recording */}
        {!isRecording && (
            <div className="max-w-7xl mx-auto px-8 pb-8">
              <RecentLiveSessions onViewSession={setViewedSession} />
            </div>
        )}

        <SessionDetailsDialog session={viewedSession} onClose={() => setViewedSession(null)} />
      </div>
  );
}
