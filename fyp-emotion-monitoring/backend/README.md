# Emotion Recognition Backend

FastAPI service for audio transcription and multimodal emotion recognition.
The backend serves the trained fusion model used by the React frontend. It does
not train the model.

## Architecture

```text
Audio upload or microphone
          |
          v
Audio decoding and preprocessing
          |
          +--> Faster-Whisper -- English transcript
          |
          +--> Emotion2Vec Large -- voice features
                              |
EmoBERTa-large -------------+
                              v
                   Fusion classifier
                              |
             fused emotion + modality results
```

The production fusion model uses:

- **Audio:** `iic/emotion2vec_plus_large` through FunASR
- **Text:** `tae898/emoberta-large`
- **Speech-to-text:** Faster-Whisper, configured as `small.en` by default
- **Labels:** `Neutral`, `Happy`, `Sad`, `Angry`, and `Frustrated`

The model internally keeps `Frustrated` as a separate class. The frontend maps
it to `Angry` when displaying charts and summaries.

## Project Files

| File | Purpose |
| --- | --- |
| `main.py` | FastAPI application, startup, health and upload routes |
| `websocket_handler.py` | Live PCM16 WebSocket pipeline |
| `models/emotion_model.py` | Emotion2Vec + EmoBERTa fusion model and inference |
| `models/stt.py` | Faster-Whisper transcription |
| `models/audio_utils.py` | WAV conversion, resampling, windows, and preprocessing |
| `auth.py` | Supabase JWT and local development authentication |
| `storage.py` | Optional Supabase report and audio persistence |
| `checkpoints/` | Local model checkpoints; not committed to Git |

## Requirements

- Python 3.11 or newer
- `ffmpeg` available on `PATH`
- Approximately 2 GB for the fusion checkpoint
- Additional disk space for Emotion2Vec, EmoBERTa, and Faster-Whisper caches

Install `ffmpeg`:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

## Installation

From the `backend` directory:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the trained checkpoint into the backend:

```bash
mkdir -p checkpoints
cp /path/to/iemocap_e2v_large_model.pt checkpoints/iemocap_e2v_large_model.pt
```

The checkpoint path must match `FUSION_MODEL_CHECKPOINT` in `backend/.env`.

## Environment Variables

Create `backend/.env`. Do not commit it.

```env
DISABLE_AUTH=true
DEV_USER_ID=00000000-0000-0000-0000-000000000000
USE_MOCK_MODEL=false

FUSION_MODEL_CHECKPOINT=checkpoints/iemocap_e2v_large_model.pt
```

For optional Supabase persistence, also configure:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your-server-side-key
SUPABASE_JWKS_URL=https://your-project.supabase.co/auth/v1/.well-known/jwks.json
```

Use `DISABLE_AUTH=true` only for local development. For a deployed instance,
set it to `false` and configure Supabase authentication.

## Running the Server

```bash
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Useful URLs:

- API documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

The health response reports model state, labels, and the configured audio and
text model names.

## API Routes

### `GET /api/health`

Returns backend and model status. This route does not require authentication.

### `POST /api/analyze-file`

Accepts an audio upload as multipart form data. Supported formats depend on
`ffmpeg`, including WAV, MP3, M4A, OGG, FLAC, and WebM.

Files are decoded to 16 kHz mono audio and split into eight-second model
windows. Each window returns a transcript and emotion result.

### `WS /ws/live-session`

Live sessions use raw 16 kHz mono PCM16 frames, not MediaRecorder WebM chunks.

Handshake:

```json
{"token":"<jwt>","format":"pcm16","sampleRate":16000}
```

The server replies with `ready`, processes buffered audio, and sends readings:

```json
{
  "type": "reading",
  "transcript": "Example text.",
  "emotion": {
    "top_label": "Happy",
    "confidence": 0.82,
    "modality_weights": {"audio": 0.61, "text": 0.39},
    "audio_emotion": {"label": "Happy", "confidence": 0.74},
    "text_emotion": {"label": "Neutral", "confidence": 0.58}
  }
}
```

Send `{"action":"end"}` to flush the final buffer and close the session.

### `GET /api/reports`

Returns saved reports when Supabase persistence is configured.

## Inference Details

- Audio is resampled to 16 kHz mono and padded or truncated to eight seconds.
- Live chunks use voice activity and silence checks before transcription, and
  Faster-Whisper applies its built-in VAD to reduce pause hallucinations.
- Audio preprocessing includes gating, normalization, dynamic-range
  compression, and high-pass filtering.
- Faster-Whisper is forced to English and runs locally.
- The fusion model returns a fused prediction plus audio-only and text-only
  comparison predictions.
- The live UI uses a five-second rolling emotion window for the current result.

## Supabase Persistence

Persistence is optional. If enabled, configure:

1. An `emotion_reports` table with `id`, `user_id`, `data`, and `created_at`.
2. An `audio-uploads` storage bucket.
3. Appropriate Row Level Security policies.

Without Supabase configuration, predictions still work but reports are not
saved or listed.

## Troubleshooting

### Checkpoint not found

Confirm the file exists and the path is relative to `backend`:

```bash
ls -lh checkpoints/iemocap_e2v_large_model.pt
```

### `ffmpeg` not found

Install `ffmpeg` and confirm it is available:

```bash
ffmpeg -version
```

### Slow transcription

Use `WHISPER_MODEL_SIZE=tiny.en` or `base.en` for lower latency. `small.en` is
more accurate but requires more CPU time. A CUDA-capable machine can use
`DEVICE=cuda` if the installed PyTorch build supports it.

### Mock results appear

Set `USE_MOCK_MODEL=false` and confirm the checkpoint exists. The startup log
will state whether mock mode is active.
