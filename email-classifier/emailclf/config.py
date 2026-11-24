"""Central settings. Everything tunable lives here or in the .env file."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")  # silently does nothing if there is no .env file

# --------------------------------------------------------------------------- #
# The five classes. Edit the descriptions: the LLM prompt is built from them.
# --------------------------------------------------------------------------- #
LABELS = ["spam", "job_offer", "job_task", "job_confirmation", "job_rejection"]
REVIEW = "needs_review"  # the "I'm not sure, a human should look" bucket

LABEL_DESCRIPTIONS = {
    "spam": "Unsolicited junk: scams, phishing, mass marketing, fake job schemes "
    "(e.g. 'earn $500/day', or a 'job' that asks you to pay a fee).",
    "job_offer": "A genuine job offer, OR a real recruiter reaching out about a "
    "specific role/opportunity.",
    "job_task": "The candidate must DO something: finish an assessment, submit "
    "documents, pick or confirm an interview slot, sign forms. Often has a deadline.",
    "job_confirmation": "Confirms something already done or arranged: application "
    "received, interview confirmed, submission received, offer acceptance confirmed, "
    "status update with no decision.",
    "job_rejection": "The employer declines the candidate or closes the role "
    "without hiring.",
}

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
OUTPUT_DIR = ROOT / "outputs"

TRAIN_CSV = DATA_DIR / "train.csv"
TEST_CSV = DATA_DIR / "test.csv"
INJECTION_CSV = DATA_DIR / "injection_tests.csv"
FEEDBACK_CSV = DATA_DIR / "feedback.csv"  # grows when you correct labels (git-ignored)
BASELINE_MODEL_PATH = MODELS_DIR / "baseline.joblib"


# --------------------------------------------------------------------------- #
# Environment-driven settings
# --------------------------------------------------------------------------- #
def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _optional_float(name: str) -> float | None:
    raw = os.getenv(name, "").strip()
    try:
        return float(raw) if raw else None
    except ValueError:
        return None


# Below this confidence the email goes to the "needs_review" bucket.
CONFIDENCE_THRESHOLD = _float("CONFIDENCE_THRESHOLD", 0.6)

# "mock" (offline, no key needed) | "anthropic" | "openai" (also works for Ollama)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").strip().lower()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()  # empty = sensible default per provider
LLM_TIMEOUT_S = _float("LLM_TIMEOUT_S", 30.0)
LLM_MAX_RETRIES = int(_float("LLM_MAX_RETRIES", 3))
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip() or None  # e.g. Ollama

# Optional: price per MILLION tokens, to estimate cost in `compare`.
# Look these up on your provider's pricing page. Left empty = tokens only.
PRICE_IN_PER_MTOK = _optional_float("PRICE_IN_PER_MTOK")
PRICE_OUT_PER_MTOK = _optional_float("PRICE_OUT_PER_MTOK")

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com").strip()
IMAP_USER = os.getenv("IMAP_USER", "").strip()
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")

# Never send more than this many characters of an email to the LLM (cost control).
MAX_EMAIL_CHARS = 4000

# --------------------------------------------------------------------------- #
# Sender rules (used by rules.py). Edit these for your own inbox.
# --------------------------------------------------------------------------- #
# Mail from these domains is never auto-labelled as spam by the cheap rules.
TRUSTED_JOB_DOMAINS = {
    "greenhouse.io",
    "lever.co",
    "myworkday.com",
    "smartrecruiters.com",
    "brightwave-hr.example",
    "nordlane.example",
}
# Mail from these domains is always spam.
BLOCKED_DOMAINS = {
    "free-prizes.example",
    "quick-cash-now.example",
}
