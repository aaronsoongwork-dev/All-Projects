"""
Central configuration. Loads from environment variables (.env in dev).
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# --- Dev switches ---
# DISABLE_AUTH skips JWT verification entirely and treats every caller as
# DEV_USER_ID. It exists so the frontend can be developed against a real
# running model before anyone has Supabase credentials. Guarded loudly at
# startup in main.py — never enable it on a deployed instance.
DISABLE_AUTH = _flag("DISABLE_AUTH")
DEV_USER_ID = os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000000")

# USE_MOCK_MODEL returns randomised predictions in the real response shape,
# so the full request path can be exercised before the trained checkpoint
# exists. Also engaged automatically if the checkpoint file is missing.
USE_MOCK_MODEL = _flag("USE_MOCK_MODEL")

# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL", f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json" if SUPABASE_URL else "")

# Persistence is optional: without credentials the API still serves
# predictions, it just can't save or list reports.
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SECRET_KEY)

# --- CORS ---
# Vite dev server defaults, plus anything in ALLOWED_ORIGINS (comma-separated)
# so the deployed frontend domain can be added without a code change.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")
    if o.strip()
]

# --- Whisper (speech-to-text, feeds the text branch of your fusion model) ---
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small.en")  # tiny.en/base.en/small.en/medium.en

# --- Your trained fusion model ---
# Path to the checkpoint train.py saves (outputs/models/fusion_model.pt).
# Copy that file into this project (e.g. into ./checkpoints/) once training
# is done, or point this at wherever it lives on the GPU box.
FUSION_MODEL_CHECKPOINT = os.getenv(
    "FUSION_MODEL_CHECKPOINT", "checkpoints/fusion_model.pt"
)

import multiprocessing

# --- Runtime ---
DEVICE = os.getenv("DEVICE", "cpu")
INFERENCE_WORKERS = int(os.getenv("INFERENCE_WORKERS", str(min(multiprocessing.cpu_count(), 4))))

# --- Audio format, must match dataset.py exactly ---
SAMPLE_RATE = 16_000
MAX_AUDIO_SECS = 8
MAX_AUDIO_SAMPLES = SAMPLE_RATE * MAX_AUDIO_SECS

# --- Live session chunking ---
# How much audio to buffer before running one prediction. The browser streams
# 16kHz mono PCM16 (see websocket_handler.py), which is 32000 bytes/second,
# so the default below is ~4 seconds of speech per prediction.
# This is independent of MAX_AUDIO_SECS above — that's the model's fixed
# input window; this is how often you re-run the model during a live session.
CHUNK_THRESHOLD_BYTES = int(os.getenv("CHUNK_THRESHOLD_BYTES", str(32000 * 3)))
