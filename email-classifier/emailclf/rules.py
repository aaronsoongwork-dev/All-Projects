"""Cheap, high-precision rules that run BEFORE any model.

Why: rules are free, instant and predictable. If a rule fires, we skip the model (and
the LLM cost). The price: rules must be PRECISE (almost never wrong), because a wrong
rule is a confident wrong answer. Check them with:  python -m emailclf rules-report
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import config


@dataclass
class RuleHit:
    label: str
    rule: str


_REJECTION = re.compile(
    r"we regret to inform you|will not be moving forward|not be moving forward with your|"
    r"decided to (move|go) forward with other candidates|decided to pursue other candidates|"
    r"decided not to (proceed|move forward) with your (application|candidacy)",
    re.I,
)

_SPAM_PATTERNS = {
    "won-prize": re.compile(r"\byou(?:'ve| have)\s+won\b|claim your (prize|reward|gift)", re.I),
    "guaranteed-returns": re.compile(r"guaranteed\s+\d+%|\d+%\s+guaranteed\s+returns?", re.I),
    "earn-per-day": re.compile(r"earn\s+(up to\s+)?[$rm]{1,2}\s?\d[\d,]*\s*(per|a|/)\s*(day|week|hour)", re.I),
}


def _domain(sender: str) -> str:
    match = re.search(r"@([A-Za-z0-9.\-]+)", sender or "")
    return match.group(1).lower() if match else ""


def apply_rules(text: str, sender: str = "") -> RuleHit | None:
    """Return a RuleHit if a rule is confident enough to decide, else None (ask the model)."""
    domain = _domain(sender)

    if domain in config.BLOCKED_DOMAINS:
        return RuleHit("spam", "blocked-domain")

    if _REJECTION.search(text):
        return RuleHit("job_rejection", "rejection-phrase")

    # Spam rules are skipped for trusted job platforms (their marketing footers look spammy).
    if domain not in config.TRUSTED_JOB_DOMAINS:
        for name, pattern in _SPAM_PATTERNS.items():
            if pattern.search(text):
                return RuleHit("spam", name)

    return None
