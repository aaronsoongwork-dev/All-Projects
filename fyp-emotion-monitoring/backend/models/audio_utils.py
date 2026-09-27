"""
Two jobs:

1. Browsers record audio as WebM/Opus (MediaRecorder default), not raw
   WAV/PCM — `to_wav_pcm16` converts whatever comes in to 16kHz mono WAV.
   Requires ffmpeg installed on the host.

2. `bytes_to_model_waveform` reproduces your dataset.py's `_load_audio`
   logic exactly (mono, resample to 16kHz, pad/truncate to a fixed 8-second
   length) so inference audio is preprocessed identically to how the model
   was trained — this matters, mismatched preprocessing between training
   and inference is one of the most common causes of a model that "worked
   in testing" doing badly in production.
"""
import io
import wave

import torch
import torchaudio
from pydub import AudioSegment

from config import MAX_AUDIO_SAMPLES, SAMPLE_RATE


def to_wav_pcm16(raw_bytes: bytes, source_format: str = "webm") -> bytes:
    """
    Converts a COMPLETE browser-recorded audio file to 16kHz mono WAV bytes.

    Only valid for whole files (the /api/analyze-file upload path). It cannot
    decode a mid-stream MediaRecorder chunk — see wrap_pcm16_as_wav below.
    """
    audio = AudioSegment.from_file(io.BytesIO(raw_bytes), format=source_format)
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1).set_sample_width(2)
    out = io.BytesIO()
    audio.export(out, format="wav")
    return out.getvalue()


def wrap_pcm16_as_wav(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """
    Wraps headerless 16kHz mono PCM16 samples in a WAV container.

    This is the live-session path, and it exists because of a real constraint:
    MediaRecorder's WebM/Opus output is only decodable as a whole file. Chunks
    after the first carry no container header, so feeding one to ffmpeg (via
    to_wav_pcm16) fails — which is why the live stream sends raw PCM captured
    through the Web Audio API instead of MediaRecorder blobs.

    Being header-free also makes the stream trivially sliceable: any byte range
    on a 2-byte boundary is still valid audio. And it needs no ffmpeg subprocess
    per chunk, which matters when this runs every few seconds.
    """
    out = io.BytesIO()
    with wave.open(out, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_bytes)
    return out.getvalue()


def noise_gate(waveform: torch.Tensor, threshold: float = 0.01) -> torch.Tensor:
    """Zero out samples below threshold to reduce background noise."""
    mask = waveform.abs() < threshold
    return waveform.masked_fill(mask, 0.0)


def enhance_audio(waveform: torch.Tensor) -> torch.Tensor:
    """
    Enhance audio for better emotion analysis:
    1. Dynamic range compression — brings quiet parts up, loud parts down
    2. Normalization — consistent volume level
    3. High-pass filter — removes low-frequency rumble
    """
    import numpy as np

    wav_np = waveform.cpu().numpy()

    # 1. Dynamic range compression (soft knee)
    threshold = 0.3
    ratio = 4.0
    abs_wav = np.abs(wav_np)
    mask = abs_wav > threshold
    if np.any(mask):
        excess = abs_wav[mask] - threshold
        compressed = threshold + excess / ratio
        wav_np[mask] = np.sign(wav_np[mask]) * compressed

    # 2. Peak normalization to 0.7
    peak = np.max(np.abs(wav_np))
    if peak > 0.001:
        wav_np = wav_np * (0.7 / peak)

    # 3. Simple high-pass: remove frequencies below ~80Hz via differentiation
    # (emotions are carried in 80Hz-4kHz range, not sub-bass rumble)
    wav_np = wav_np - np.roll(wav_np, 1) * 0.95
    wav_np[0] = 0

    return torch.from_numpy(wav_np).to(waveform.dtype)


def bytes_to_full_waveform(wav_bytes: bytes) -> torch.Tensor:
    """
    Decode WAV to a mono 16kHz float32 waveform of its true length.

    Same normalisation as dataset.py's _load_audio, minus the fixed-length
    step — callers decide whether to pad/truncate (single prediction) or
    window (timeline over a long file).
    """
    waveform, sr = torchaudio.load(io.BytesIO(wav_bytes))  # [C, T]

    if waveform.ndim == 2 and waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    if waveform.ndim == 2:
        waveform = waveform.squeeze(0)  # [T]

    waveform = waveform.to(torch.float32)

    if sr != SAMPLE_RATE:
        waveform = torchaudio.functional.resample(waveform, sr, SAMPLE_RATE)

    return waveform


def pad_or_truncate(waveform: torch.Tensor) -> torch.Tensor:
    """Force a waveform to exactly MAX_AUDIO_SAMPLES, as the model expects."""
    if waveform.shape[0] < MAX_AUDIO_SAMPLES:
        return torch.nn.functional.pad(waveform, (0, MAX_AUDIO_SAMPLES - waveform.shape[0]))
    return waveform[:MAX_AUDIO_SAMPLES]


def bytes_to_model_waveform(wav_bytes: bytes) -> torch.Tensor:
    """
    Mirrors IEMOCAPDataset._load_audio in dataset.py:
      - mono
      - resample to 16kHz
      - pad or truncate to exactly MAX_AUDIO_SAMPLES (8 seconds)
    Input must already be WAV — run to_wav_pcm16() first if the source
    is browser-recorded WebM/Opus.
    """
    return pad_or_truncate(bytes_to_full_waveform(wav_bytes))


def waveform_to_wav_bytes(waveform: torch.Tensor) -> bytes:
    """Float32 waveform in [-1, 1] -> 16kHz mono PCM16 WAV bytes (for Whisper)."""
    clamped = torch.clamp(waveform, -1.0, 1.0)
    pcm = (clamped * 32767.0).to(torch.int16).numpy().tobytes()
    return wrap_pcm16_as_wav(pcm)


def split_into_windows(
    waveform: torch.Tensor, window_samples: int = MAX_AUDIO_SAMPLES
) -> list[tuple[float, float, torch.Tensor]]:
    """
    Cut a waveform into consecutive model-sized windows.

    The model takes a fixed 8-second input, so a longer upload would otherwise
    be silently truncated to its first 8 seconds — one prediction standing in
    for the whole file. Windowing instead produces a genuine timeline, which
    is what the analysis chart is built to show.

    Returns (start_secs, end_secs, padded_waveform) per window. A trailing
    remainder shorter than half a window is folded into the previous one
    rather than emitted as a mostly-silent padded window of its own.
    """
    total = waveform.shape[0]
    if total == 0:
        return []
    if total <= window_samples:
        return [(0.0, total / SAMPLE_RATE, pad_or_truncate(waveform))]

    windows: list[tuple[float, float, torch.Tensor]] = []
    for start in range(0, total, window_samples):
        end = min(start + window_samples, total)

        # Fold a short tail into the window before it.
        if end - start < window_samples // 2 and windows:
            prev_start, _, _ = windows[-1]
            prev_start_sample = int(prev_start * SAMPLE_RATE)
            windows[-1] = (
                prev_start,
                end / SAMPLE_RATE,
                pad_or_truncate(waveform[prev_start_sample:end]),
            )
            break

        windows.append(
            (start / SAMPLE_RATE, end / SAMPLE_RATE, pad_or_truncate(waveform[start:end]))
        )

    return windows
