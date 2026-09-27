"""
Live audio session over WebSocket.

Protocol (frontend/src/app/api/liveSession.ts implements the client side):

  1. Client opens ws connection to /ws/live-session

  2. First message, JSON:
       {"token": "<supabase jwt>", "format": "pcm16", "sampleRate": 16000}
     `format` defaults to "pcm16"; "webm" is accepted for one-shot blobs but
     is NOT usable for a continuous stream (see below).

  3. Server replies {"type": "ready"} once auth passes, then the client
     streams audio as binary frames.

  4. Every CHUNK_THRESHOLD_BYTES, the server runs the pipeline
     (wav -> transcript -> fusion model) and sends:
       {"type": "reading", "transcript": str, "emotion": {...},
        "timestamp": float, "chunkIndex": int}

  5. Client ends the session with {"action": "end"}; the server flushes any
     remaining audio, persists the session, and replies
       {"type": "summary", "reportId": str | null, "numReadings": int}

Why raw PCM and not MediaRecorder blobs
---------------------------------------
MediaRecorder produces WebM/Opus that is only decodable as a complete file —
every chunk after the first lacks a container header, so decoding one in
isolation fails. The original version of this handler passed each chunk
straight to ffmpeg as "webm", which could only ever have worked for the very
first chunk of a session. The client now captures raw PCM16 through the Web
Audio API instead, which is header-free and safe to slice at any point.
"""
import asyncio
import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from fastapi import WebSocket, WebSocketDisconnect

from auth import verify_ws_token
from config import CHUNK_THRESHOLD_BYTES, INFERENCE_WORKERS, SAMPLE_RATE
from models import audio_utils, emotion_model, stt
from storage import save_session_report

executor = ThreadPoolExecutor(max_workers=INFERENCE_WORKERS)

# Below this, a chunk is too short to say anything useful about (and Whisper
# tends to hallucinate on near-silence). 2 seconds of 16kHz PCM16.
MIN_FLUSH_BYTES = SAMPLE_RATE * 2  # 32000 bytes == 16000 samples == 2s


async def run_blocking(fn, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, fn, *args)


async def process_chunk(
    raw_audio_bytes: bytes, fmt: str = "pcm16", sample_rate: int = SAMPLE_RATE
) -> dict:
    """
    Runs one buffered chunk of audio through: container wrapping -> VAD check
    -> transcript (Whisper) -> the fusion model (audio waveform + transcript -> emotion).
    """
    if fmt == "pcm16":
        wav_bytes = audio_utils.wrap_pcm16_as_wav(raw_audio_bytes, sample_rate)
    else:
        wav_bytes = await run_blocking(audio_utils.to_wav_pcm16, raw_audio_bytes, fmt)

    waveform = await run_blocking(audio_utils.bytes_to_model_waveform, wav_bytes)

    # VAD: skip chunks with no speech (saves ~1-2s per silent chunk)
    rms = float(waveform.pow(2).mean().sqrt())
    if rms < 0.005:
        return {"transcript": "", "emotion": None, "timestamp": time.time(), "silent": True}

    # Noise gate: zero out samples below threshold to reduce background noise
    waveform = audio_utils.noise_gate(waveform, threshold=0.01)

    # Enhance audio: compress dynamic range, normalize, high-pass filter
    waveform = audio_utils.enhance_audio(waveform)

    # Run Whisper and emotion model in parallel
    transcript_future = run_blocking(stt.transcribe, wav_bytes)
    emotion_future = run_blocking(emotion_model.predict, waveform, "")
    transcript, emotion_result = await asyncio.gather(transcript_future, emotion_future)

    # Re-run emotion model with transcript for text-audio fusion
    emotion_result = await run_blocking(emotion_model.predict, waveform, transcript)

    return {
        "transcript": transcript,
        "emotion": emotion_result,
        "timestamp": time.time(),
        "silent": False,
    }


def _summarise(readings: list[dict]) -> dict:
    """Aggregate a session's readings into the shape the Reports page wants."""
    labels = [r["emotion"]["top_label"] for r in readings]
    counts = Counter(labels)
    total = len(readings)

    return {
        "dominant_label": counts.most_common(1)[0][0] if counts else None,
        "label_distribution": {k: v / total for k, v in counts.items()} if total else {},
        "average_confidence": (
            sum(r["emotion"]["confidence"] for r in readings) / total if total else 0.0
        ),
    }


async def handle_audio_session(websocket: WebSocket):
    await websocket.accept()

    # --- 1. Auth handshake (first message must be JSON carrying the JWT) ---
    try:
        auth_msg = await websocket.receive_json()
    except Exception:
        await websocket.close(code=4000, reason="Expected JSON auth message first")
        return

    user = verify_ws_token(auth_msg.get("token", ""))
    if not user:
        await websocket.close(code=4001, reason="Invalid or missing token")
        return

    fmt = auth_msg.get("format", "pcm16")
    sample_rate = int(auth_msg.get("sampleRate", SAMPLE_RATE))

    user_id = user["sub"]
    audio_buffer = bytearray()
    session_readings: list[dict] = []
    started_at = time.time()

    await websocket.send_json(
        {
            "type": "ready",
            "chunkBytes": CHUNK_THRESHOLD_BYTES,
            "sampleRate": sample_rate,
            "mock": emotion_model.is_mock(),
        }
    )

    async def flush(force: bool = False) -> None:
        """Run the pipeline over the buffered audio and emit one reading."""
        nonlocal audio_buffer

        threshold = MIN_FLUSH_BYTES if force else CHUNK_THRESHOLD_BYTES
        if len(audio_buffer) < threshold:
            return

        chunk_bytes = bytes(audio_buffer)
        audio_buffer = bytearray()

        try:
            reading = await process_chunk(chunk_bytes, fmt, sample_rate)
        except Exception as e:
            # One bad chunk shouldn't take down the whole session.
            await websocket.send_json({"type": "error", "message": str(e)})
            return

        # Silent chunks must not become fake readings. Otherwise the frontend
        # shows a random-looking emotion even though no speech was analysed.
        if reading.get("silent"):
            return

        session_readings.append(reading)
        await websocket.send_json(
            {
                "type": "reading",
                "transcript": reading["transcript"],
                "emotion": reading["emotion"],
                "timestamp": reading["timestamp"],
                "chunkIndex": len(session_readings) - 1,
            }
        )

    client_ended = False

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            if message.get("bytes") is not None:
                audio_buffer.extend(message["bytes"])
                await flush()

            elif message.get("text") is not None:
                try:
                    payload = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                if payload.get("action") == "end":
                    await flush(force=True)  # don't discard the final partial chunk
                    client_ended = True
                    break

    except WebSocketDisconnect:
        pass
    finally:
        report_id = None
        # Only persist sessions explicitly ended by Stop & Save. Navigating
        # away closes the socket without `action: end` and must discard it.
        if client_ended and session_readings:
            report = {
                "type": "live",
                "readings": session_readings,
                "num_chunks": len(session_readings),
                "started_at": started_at,
                "ended_at": time.time(),
                "duration_secs": round(time.time() - started_at, 1),
                "summary": _summarise(session_readings),
            }
            try:
                saved = save_session_report(user_id, report)
                report_id = saved.get("id")
            except Exception as e:
                print(f"[warn] failed to save session report: {e}")

        if client_ended:
            try:
                await websocket.send_json(
                    {
                        "type": "summary",
                        "reportId": report_id,
                        "numReadings": len(session_readings),
                    }
                )
                await websocket.close()
            except Exception:
                pass
