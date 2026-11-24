"""Feedback loop: when you correct a label, save it so the model can learn from it.

Corrections go to data/feedback.csv (git-ignored, because it may hold real emails).
`python -m emailclf train` automatically includes feedback.csv in the training data.
"""

from __future__ import annotations

import csv

from . import config
from .data_io import Email, load_csv

FIELDS = ["id", "sender", "subject", "body", "label"]


def append_feedback(email: Email, correct_label: str) -> None:
    if correct_label not in config.LABELS:
        raise ValueError(f"label must be one of {config.LABELS}")
    new_file = not config.FEEDBACK_CSV.exists()
    with open(config.FEEDBACK_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(
            {"id": email.id, "sender": email.sender, "subject": email.subject, "body": email.body, "label": correct_label}
        )


def load_training_emails() -> list[Email]:
    """train.csv plus any corrections you have saved."""
    emails = load_csv(config.TRAIN_CSV)
    if config.FEEDBACK_CSV.exists():
        emails += load_csv(config.FEEDBACK_CSV)
    return [e for e in emails if e.label in config.LABELS]
