"""PII redaction: mask personal data BEFORE text is sent to a third-party LLM API.

Placeholders use [SQUARE BRACKETS] (not <angle brackets>) so they can never be confused with
the <email> tags that wrap the message in the prompt. (A test caught exactly that bug.)

Limits (be honest about these in an interview):
  * Regex catches emails, phone numbers, card-like numbers and ID-like numbers.
  * It does NOT catch names or street addresses. That needs an NER model
    (e.g. Microsoft Presidio or spaCy). This is a first line of defence, not a guarantee.
"""

from __future__ import annotations

import re

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")
_ID = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{6}-\d{2}-\d{4}\b")  # SSN-like, Malaysian IC-like
_PHONE = re.compile(r"(?<![\w.])\+?\(?\d[\d\s().\-]{7,}\d(?![\w])")


def _phone_sub(match: re.Match) -> str:
    digits = re.sub(r"\D", "", match.group(0))
    # Only treat it as a phone number if it has 9-15 digits (avoids dates and small numbers).
    return "[PHONE]" if 9 <= len(digits) <= 15 else match.group(0)


def redact(text: str) -> tuple[str, dict[str, int]]:
    """Return (redacted_text, counts_by_type)."""
    counts = {"EMAIL": 0, "CARD": 0, "ID": 0, "PHONE": 0}

    def make_sub(tag: str):
        def _sub(_m: re.Match) -> str:
            counts[tag] += 1
            return f"[{tag}]"

        return _sub

    text = _EMAIL.sub(make_sub("EMAIL"), text)
    text = _ID.sub(make_sub("ID"), text)
    text = _CARD.sub(make_sub("CARD"), text)

    def phone(m: re.Match) -> str:
        out = _phone_sub(m)
        if out == "[PHONE]":
            counts["PHONE"] += 1
        return out

    text = _PHONE.sub(phone, text)
    return text, {k: v for k, v in counts.items() if v}
