"""The full pipeline. One email in, one Prediction out.

    raw email
       |
       v
  [1] injection scan on the RAW text ----suspicious----> needs_review (model never sees it)
       |
  [2] clean (HTML, quoted replies, signatures)
       |
  [3] cheap rules ----------------------hit-------------> label (confidence 1.0, no model cost)
       |
  [4] PII redaction (LLM backend only: nothing personal leaves your machine)
       |
  [5] model: TF-IDF baseline  or  LLM few-shot
       |
  [6] confidence threshold: below it -> needs_review
"""

from __future__ import annotations

from . import config
from .baseline import BaselineClassifier
from .cleaning import build_text
from .data_io import Email
from .llm import LLMClassifier, LLMClient
from .pii import redact
from .rules import apply_rules
from .schemas import Prediction
from .security import injection_signals


class EmailPipeline:
    def __init__(
        self,
        backend: str = "baseline",  # "baseline" or "llm"
        threshold: float | None = None,
        use_rules: bool = True,
        clean: bool = True,
        redact_pii: bool = True,
        injection_guard: bool = True,
        hardened_prompt: bool = True,
        client: LLMClient | None = None,
        baseline: BaselineClassifier | None = None,
    ) -> None:
        self.backend = backend
        self.threshold = config.CONFIDENCE_THRESHOLD if threshold is None else threshold
        self.use_rules = use_rules
        self.clean = clean
        self.redact_pii = redact_pii
        self.injection_guard = injection_guard

        if backend == "baseline":
            self.model = baseline or BaselineClassifier.load()
        elif backend == "llm":
            self.model = LLMClassifier(client=client, hardened=hardened_prompt)
        else:
            raise ValueError("backend must be 'baseline' or 'llm'")

    def classify(self, email: Email) -> Prediction:
        # [1] scan the RAW text (hidden HTML and quoted text included)
        signals = injection_signals(f"{email.subject}\n{email.body}")
        if signals and self.injection_guard:
            return Prediction(
                label=config.REVIEW, confidence=0.0, source="injection_guard", raw_label="unknown",
                notes=[f"possible prompt injection: {', '.join(signals)}"],
            )

        # [2] clean
        text = build_text(email.subject, email.body, clean=self.clean)

        # [3] rules
        if self.use_rules:
            hit = apply_rules(text, email.sender)
            if hit:
                return Prediction(label=hit.label, confidence=1.0, source=f"rule:{hit.rule}", raw_label=hit.label)

        # [4] PII redaction, only needed when text leaves your machine
        notes: list[str] = []
        if self.backend == "llm" and self.redact_pii:
            text, counts = redact(text)
            if counts:
                notes.append(f"redacted: {counts}")

        # [5] model
        pred = self.model.predict(text)
        pred.notes = notes + pred.notes

        # [6] threshold
        if pred.label != config.REVIEW and pred.confidence < self.threshold:
            pred.notes.append(f"confidence {pred.confidence:.2f} < threshold {self.threshold:.2f}")
            pred.label = config.REVIEW
        return pred
