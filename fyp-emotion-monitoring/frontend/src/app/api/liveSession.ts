/**
 * Live microphone -> WebSocket -> FastAPI streaming client.
 *
 * ── Why Web Audio and not MediaRecorder ──
 * MediaRecorder is the obvious choice for "record audio in the browser", but
 * its WebM/Opus output is only decodable as a complete file: every chunk after
 * the first has no container header, so the server cannot decode it in
 * isolation. A continuous stream of MediaRecorder chunks is therefore
 * undecodable server-side past the first one.
 *
 * Instead we tap the raw audio graph and send headerless 16kHz mono PCM16.
 * Every byte pair is a sample, so the server can slice the stream anywhere and
 * still have valid audio (backend/models/audio_utils.py:wrap_pcm16_as_wav),
 * and no ffmpeg subprocess is needed per chunk.
 *
 * The PCM is uncompressed — 32 KB/s upstream. Fine on localhost or a LAN
 * demo; if this is ever deployed over a slow link, that's the thing to
 * revisit (Opus-encoding each chunk as its own complete file would work).
 */
import { getAccessToken } from "../lib/supabase";
import type { LiveServerMessage } from "./types";

const TARGET_SAMPLE_RATE = 16000;

/** Worklet source, inlined as a blob so there's no separate asset to serve. */
const WORKLET_SOURCE = `
class PcmTap extends AudioWorkletProcessor {
  process(inputs) {
    const channel = inputs[0]?.[0];
    // Copy — the buffer is reused by the audio thread after we return.
    if (channel) this.port.postMessage(new Float32Array(channel));
    return true;
  }
}
registerProcessor('pcm-tap', PcmTap);
`;

function floatToPcm16(input: Float32Array): ArrayBuffer {
  // Auto-gain: boost quiet audio so the model gets consistent levels.
  let peak = 0;
  for (let i = 0; i < input.length; i++) {
    const v = Math.abs(input[i]);
    if (v > peak) peak = v;
  }
  const TARGET_PEAK = 0.3;
  const gain = peak > 0.01 ? Math.min(TARGET_PEAK / peak, 8) : 1;

  const out = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i] * gain));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out.buffer;
}

/** Linear-interpolation downsample, used only if the browser wouldn't give
 *  us a 16kHz AudioContext directly. */
function resample(input: Float32Array, from: number, to: number): Float32Array {
  if (from === to) return input;
  const ratio = from / to;
  const out = new Float32Array(Math.floor(input.length / ratio));
  for (let i = 0; i < out.length; i++) {
    const pos = i * ratio;
    const idx = Math.floor(pos);
    const frac = pos - idx;
    const a = input[idx] ?? 0;
    const b = input[idx + 1] ?? a;
    out[i] = a + (b - a) * frac;
  }
  return out;
}

export interface LiveSessionCallbacks {
  onReady?: (info: { mock: boolean }) => void;
  onReading?: (msg: Extract<LiveServerMessage, { type: "reading" }>) => void;
  onSummary?: (msg: Extract<LiveServerMessage, { type: "summary" }>) => void;
  onError?: (message: string) => void;
  /** Fires with the current input level (0..1) for the waveform display. */
  onLevel?: (level: number) => void;
  /** Fires when a chunk is sent to the server for processing. */
  onProcessing?: (processing: boolean) => void;
}

export class LiveSession {
  private ws: WebSocket | null = null;
  private ctx: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private node: AudioWorkletNode | ScriptProcessorNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private muted = false;
  private closed = false;
  private bytesSent = 0;
  private chunkThreshold = 32000 * 2; // 2s default, updated from server

  private cb: LiveSessionCallbacks;

  constructor(cb: LiveSessionCallbacks = {}) {
    this.cb = cb;
  }

  /** Requests the mic, opens the socket, and begins streaming. */
  async start(): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    // Asking for 16kHz up front lets the browser resample for us. Not all
    // browsers honour it, hence the fallback resample() below.
    try {
      this.ctx = new AudioContext({ sampleRate: TARGET_SAMPLE_RATE });
    } catch {
      this.ctx = new AudioContext();
    }
    const inputRate = this.ctx.sampleRate;

    await this.openSocket();
    if (this.closed) return;

    this.source = this.ctx.createMediaStreamSource(this.stream);

    const onSamples = (samples: Float32Array) => {
      if (this.muted) return;

      // Peak level for the waveform bars — computed here because this is the
      // only place with access to the raw samples.
      if (this.cb.onLevel) {
        let peak = 0;
        for (let i = 0; i < samples.length; i++) {
          const v = Math.abs(samples[i]);
          if (v > peak) peak = v;
        }
        this.cb.onLevel(peak);
      }

      if (this.ws?.readyState !== WebSocket.OPEN) return;
      const pcm = floatToPcm16(resample(samples, inputRate, TARGET_SAMPLE_RATE));
      this.ws.send(pcm);
      this.bytesSent += pcm.byteLength;
      // Notify when a chunk boundary is likely reached
      if (this.bytesSent >= this.chunkThreshold) {
        this.bytesSent = 0;
        this.cb.onProcessing?.(true);
      }
    };

    await this.attachTap(onSamples);
  }

  /** Prefer AudioWorklet (off the main thread); fall back where unavailable. */
  private async attachTap(onSamples: (s: Float32Array) => void): Promise<void> {
    const ctx = this.ctx!;

    if (ctx.audioWorklet) {
      const url = URL.createObjectURL(
        new Blob([WORKLET_SOURCE], { type: "application/javascript" }),
      );
      try {
        await ctx.audioWorklet.addModule(url);
        const node = new AudioWorkletNode(ctx, "pcm-tap");
        node.port.onmessage = (e) => onSamples(e.data as Float32Array);
        this.source!.connect(node);
        // Worklets need a destination path to be pulled, but we don't want to
        // hear ourselves — a muted gain node keeps the graph alive silently.
        const sink = ctx.createGain();
        sink.gain.value = 0;
        node.connect(sink).connect(ctx.destination);
        this.node = node;
        return;
      } catch {
        // fall through to ScriptProcessor
      } finally {
        URL.revokeObjectURL(url);
      }
    }

    // Deprecated but universally supported. Runs on the main thread; fine at
    // this buffer size, and only reached on older browsers.
    const node = ctx.createScriptProcessor(4096, 1, 1);
    node.onaudioprocess = (e) => onSamples(new Float32Array(e.inputBuffer.getChannelData(0)));
    this.source!.connect(node);
    const sink = ctx.createGain();
    sink.gain.value = 0;
    node.connect(sink).connect(ctx.destination);
    this.node = node;
  }

  private openSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      const proto = location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${proto}//${location.host}/ws/live-session`);
      ws.binaryType = "arraybuffer";
      this.ws = ws;

      let settled = false;

      ws.onopen = async () => {
        // The server expects the auth handshake as the very first message.
        ws.send(
          JSON.stringify({
            token: (await getAccessToken()) ?? "",
            format: "pcm16",
            sampleRate: TARGET_SAMPLE_RATE,
          }),
        );
      };

      ws.onmessage = (event) => {
        let msg: LiveServerMessage;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }

        switch (msg.type) {
          case "ready":
            if (!settled) {
              settled = true;
              resolve();
            }
            this.chunkThreshold = msg.chunkBytes;
            this.cb.onReady?.({ mock: msg.mock });
            break;
          case "reading":
            this.cb.onProcessing?.(false);
            this.cb.onReading?.(msg);
            break;
          case "summary":
            this.cb.onSummary?.(msg);
            break;
          case "error":
            this.cb.onError?.(msg.message);
            break;
        }
      };

      ws.onerror = () => {
        if (!settled) {
          settled = true;
          reject(
            new Error(
              "Could not connect to the live analysis backend. Is it running on port 8000?",
            ),
          );
        }
      };

      ws.onclose = (e) => {
        if (!settled) {
          settled = true;
          // 4001 is our own "bad token" close code from the server.
          reject(
            new Error(
              e.code === 4001
                ? "Session rejected: not signed in, or the login has expired."
                : "Live session closed before it started.",
            ),
          );
        }
      };
    });
  }

  /** Pause/resume streaming without dropping the socket or the mic grant. */
  setMuted(muted: boolean): void {
    this.muted = muted;
  }

  /**
   * Ask the server to flush the final partial chunk and persist the session.
   * Resolves with the saved report id once the summary arrives, or null if
   * the server doesn't answer in time.
   */
  async stop(): Promise<string | null> {
    if (this.closed) return null;
    this.closed = true;

    const summary = new Promise<string | null>((resolve) => {
      if (this.ws?.readyState !== WebSocket.OPEN) return resolve(null);

      // The final chunk still has to run through Whisper + the model, so give
      // it real time — but never hang the UI forever.
      const timer = setTimeout(() => resolve(null), 20000);
      const previous = this.cb.onSummary;
      this.cb.onSummary = (msg) => {
        clearTimeout(timer);
        previous?.(msg);
        resolve(msg.reportId);
      };
      this.ws.send(JSON.stringify({ action: "end" }));
    });

    const reportId = await summary;
    this.teardown();
    return reportId;
  }

  /** Release the mic and socket immediately, without waiting for a summary. */
  teardown(): void {
    this.closed = true;

    if (this.node) {
      this.node.disconnect();
      if ("port" in this.node) this.node.port.onmessage = null;
      else this.node.onaudioprocess = null;
    }
    this.source?.disconnect();
    this.stream?.getTracks().forEach((t) => t.stop());
    void this.ctx?.close().catch(() => {});

    if (this.ws && this.ws.readyState <= WebSocket.OPEN) this.ws.close();

    this.node = null;
    this.source = null;
    this.stream = null;
    this.ctx = null;
    this.ws = null;
  }
}
