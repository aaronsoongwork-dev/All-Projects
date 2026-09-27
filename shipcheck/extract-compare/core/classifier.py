import json
import os
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from openrouter import OpenRouter

load_dotenv()


@dataclass
class ClassificationResult:
    """Encapsulates the outcome of an email classification."""
    category: str
    confidence: float | None = None
    probabilities: dict[str, float] = field(default_factory=dict)
    raw_response: Any = None

    @property
    def is_bl_comparison(self) -> bool:
        return self.category == "BL_COMPARISON"

    def summary(self) -> str:
        conf_str = f" (confidence: {self.confidence:.4f})" if self.confidence is not None else ""
        lines = [f"Category: {self.category}{conf_str}"]
        if self.probabilities:
            lines.append("Probabilities:")
            for opt, prob in sorted(self.probabilities.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {opt}: {prob:.4f}")
        return "\n".join(lines)


class EmailClassifier:
    """Classifies incoming shipping emails into predefined operational categories."""

    DEFAULT_MODEL = "~typesafe/jev-latest"

    DEFAULT_OPTIONS = {  # noqa: RUF012
        "BL_COMPARISON": (
            "The email is CURRENTLY presenting a Shipping Instruction and a draft "
            "Bill of Lading TOGETHER and asking for them to be checked/compared "
            "against each other RIGHT NOW — e.g. 'Attached are the SI and draft BL "
            "for checking'. The email should reference or include BOTH documents "
            "as already available, not merely mention BL/SI terminology. "
            "Do NOT choose this for: (a) an email asking someone to SEND or "
            "PREPARE a draft BL so it CAN be checked later — e.g. 'Please assist "
            "to send the draft BL for [ref] for checking asap' is a REQUEST, not "
            "a comparison, since no document is being checked in this email; "
            "(b) a bulk status/reminder email like 'list of outstanding BL, please "
            "action the pending items' — this is a general reminder, not a request "
            "to check one specific SI against one specific BL. If attachments are "
            "empty, this is almost never BL_COMPARISON."
        ),
        "SI_REQUEST": "Request to prepare new shipping instructions (phrases like \"request SI/Shipping Instructions\" or \"find Shipping Instructions\".",
        "INVOICE_QUERY": (
            "The email is actively questioning, disputing, or requesting action on "
            "a charge, invoice amount, or payment — not merely mentioning the word "
            "'invoice' as one item in a document checklist (e.g. a list of required "
            "documents that includes 'Original invoice' is NOT itself an invoice "
            "query). An automated/system notification reporting that a billing "
            "process completed successfully with no action needed is GENERAL, not "
            "INVOICE_QUERY."
        ),
        "GENERAL": (
            "Operational correspondence that doesn't fit the other categories — "
            "including requests to send/prepare a draft BL for future checking, "
            "bulk status updates or reminders about outstanding documents, and "
            "automated/system-generated notifications."
        ),
        "SPAM": "Unsolicited advertising, promotional campaigns, phishing, or scams"
    }

    DEFAULT_INSTRUCTIONS = (
        "Which category best classifies this inbound email for a shipping "
        "operations team? Judge by what the email is actually asking for RIGHT "
        "NOW, not by which shipping-related keywords appear in it."
    )

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        options: dict[str, str] | None = None,
        instructions: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.options = options or self.DEFAULT_OPTIONS
        self.instructions = instructions or self.DEFAULT_INSTRUCTIONS

    def _resolve_api_key(self, api_key: str | None = None) -> str:
        resolved = api_key or self.api_key or os.environ.get("OPENROUTER_API_KEY")
        if not resolved:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. Please set it in your .env file or pass it to classify()."
            )
        return resolved

    def build_choice_question(self, instructions: str, criteria: dict[str, str]) -> dict:
        """Helper to build a Jev choice question payload."""
        return {
            "type": "choice",
            "instructions": instructions,
            "criteria": criteria,
        }

    def classify_email(
        self,
        state: dict | str,
        api_key: str | None = None,
    ):
        """
        Classifies an email using Jev decision model via OpenRouter's alpha.decisions endpoint.
        Returns the raw DecisionsResponse object.
        """
        resolved_api_key = self._resolve_api_key(api_key)
        questions = {
            "category": self.build_choice_question(
                instructions=self.instructions,
                criteria=self.options,
            )
        }

        with OpenRouter(api_key=resolved_api_key, timeout_ms=10000) as client:
            return client.alpha.decisions.create(
                model=self.model,
                state=state,
                questions=questions,
            )

    def classify(
        self,
        email: Any,
        api_key: str | None = None,
    ) -> ClassificationResult:
        """
        High-level OOP method: classifies an email and returns a typed ClassificationResult.
        Accepts an EmailMessage instance, a dict, or a string.
        """
        state = email.to_dict() if hasattr(email, "to_dict") else email
        raw_response = self.classify_email(state=state, api_key=api_key)

        answer = raw_response.answers.get("category")
        if not answer:
            raise RuntimeError("Classifier response did not contain 'category' answer")

        choice = getattr(answer, "choice", str(answer))
        confidence = getattr(answer, "confidence", None)
        probabilities = getattr(answer, "probabilities", {}) or {}

        return ClassificationResult(
            category=choice,
            confidence=confidence,
            probabilities=probabilities,
            raw_response=raw_response,
        )


# --- State Definition for standalone testing ---
SAMPLE_STATE = {
    "email_id": "email_206",
    "from": "support@webmail-verify.co",
    "subject": "Dear Valued Customer, update your account to avoid suspension",
    "body": "CONGRATULATIONS!!! Your email address has been selected in our monthly draw. Click here to claim your $1,000 gift card now: http://bit.ly/claim-prize-now",
    "attachments": []
}


def main():
    classifier = EmailClassifier()

    print(f"Using model: {classifier.model}")
    print("State to classify:")
    print(json.dumps(SAMPLE_STATE, indent=2))
    print("-" * 50)

    try:
        result = classifier.classify(email=SAMPLE_STATE)
    except ValueError as e:
        print(f"\n[Configuration Notice]: {e}")
        print("To run this classifier, ensure OPENROUTER_API_KEY is present in your .env file.")
        return
    except Exception as e:
        print(f"\n[Error calling OpenRouter]: {e}")
        return

    print("\nClassification Results:")
    print(result.summary())

    if result.raw_response and getattr(result.raw_response, "usage", None):
        usage = result.raw_response.usage
        print(f"\nTokens used: input={usage.input_tokens}, output={usage.output_tokens}")


if __name__ == "__main__":
    main()