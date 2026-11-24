"""Talking to an LLM safely.

Three layers of protection, matching the Day 1 notes on "JSON output":
  1. API retries with exponential backoff + a timeout (network/API errors).
  2. Pydantic validation of the JSON the model returns.
  3. If validation fails, retry once more WITH the error message so the model can self-correct.
If everything fails we return an error result; the caller sends the email to human review.
The program never crashes because an LLM said something odd.

Providers:
  mock       offline, deterministic, no key. For learning/testing the plumbing only.
  anthropic  needs `pip install anthropic` and ANTHROPIC_API_KEY
  openai     needs `pip install openai` and OPENAI_API_KEY; set OPENAI_BASE_URL for Ollama
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Optional, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from . import config, prompts
from .schemas import LLMClassification, Prediction

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMClient(Protocol):
    def complete(self, system: str, user: str, max_tokens: int = 400) -> LLMResponse: ...


class LLMUnavailable(RuntimeError):
    """The API kept failing after all retries."""


# --------------------------------------------------------------------------- #
# Real providers (imports are lazy so you only need the one you use)
# --------------------------------------------------------------------------- #


class AnthropicClient:
    def __init__(self, model: str, timeout: float) -> None:
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("Run: pip install anthropic") from e
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set (put it in your .env file).")
        # max_retries=0: WE do the retrying (call_with_retries), so you can see and control it.
        self.client = anthropic.Anthropic(timeout=timeout, max_retries=0)
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 400) -> LLMResponse:
        r = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0,  # low temperature = consistent output (Day 1 notes)
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        return LLMResponse(text, r.usage.input_tokens, r.usage.output_tokens)


class OpenAIClient:
    """OpenAI or any OpenAI-compatible server (Ollama: OPENAI_BASE_URL=http://localhost:11434/v1)."""

    def __init__(self, model: str, timeout: float, base_url: Optional[str]) -> None:
        try:
            import openai
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("Run: pip install openai") from e
        api_key = os.getenv("OPENAI_API_KEY") or ("ollama" if base_url else "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set (put it in your .env file).")
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=0)
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 400) -> LLMResponse:
        r = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        usage = getattr(r, "usage", None)
        return LLMResponse(
            r.choices[0].message.content or "",
            getattr(usage, "prompt_tokens", 0) or 0,
            getattr(usage, "completion_tokens", 0) or 0,
        )


# --------------------------------------------------------------------------- #
# Mock provider: offline stand-in so everything runs without an API key
# --------------------------------------------------------------------------- #

_MOCK_KEYWORDS: dict[str, list[str]] = {
    "spam": ["you won", "you have won", "prize", "crypto", "guaranteed", "unsubscribe", "discount",
             "limited time", "click here", "verify your account", "processing fee", "followers",
             "earn $", "% off", "overdue", "suspended", "page 1 of google"],
    "job_offer": ["pleased to offer", "offer you the position", "extend an offer", "offer letter",
                  "we're hiring", "we are hiring", "open to a chat", "salary", "day rate",
                  "are you interested", "role:", "compensation"],
    "job_task": ["please complete", "please submit", "please upload", "please sign", "assessment",
                 "take-home", "deadline", "confirm your availability", "select a time",
                 "pick a time", "questionnaire", "not yet completed", "action required", "reminder"],
    "job_confirmation": ["we have received", "has been received", "is confirmed", "confirming",
                         "thank you for applying", "thanks for applying", "accepted", "under review",
                         "received your", "successfully submitted", "rescheduled"],
    "job_rejection": ["regret", "unfortunately", "other candidates", "not be moving forward",
                      "not selected", "has been filled", "not the right fit", "won't be progressing",
                      "will not be progressing", "closed this"],
}
_MOCK_INJECTION = re.compile(
    r"(?:(?:classify|label|mark|categori[sz]e|treat)\s+(?:this|it|the email|this email|this message)\s+as"
    r"|this (?:email|message) is)\s+(?:a\s+|an\s+)?"
    r"(spam|job[_ ]offer|job[_ ]task|job[_ ]confirmation|job[_ ]rejection)",
    re.I,
)


class MockClient:
    """A deliberately simple keyword scorer that answers in the same JSON format as a real LLM.

    It is NOT a language model. It exists so you can run the whole pipeline offline.
    To simulate prompt injection it is gullible: with the naive prompt it obeys
    "classify this as X"; with the hardened prompt (which says the email is untrusted)
    it ignores such text. So `inject-test` results for the MODEL are SIMULATED in mock mode.
    """

    def complete(self, system: str, user: str, max_tokens: int = 400) -> LLMResponse:
        if "[task: extract]" in system:
            text = self._extract(user)
        else:
            text = self._classify(system, user)
        return LLMResponse(text, input_tokens=len(system + user) // 4, output_tokens=len(text) // 4)

    def _classify(self, system: str, user: str) -> str:
        low = user.lower()
        hardened = "untrusted" in system.lower()
        if not hardened:
            m = _MOCK_INJECTION.search(low)
            if m:
                label = m.group(1).replace(" ", "_")
                return json.dumps({"label": label, "confidence": 0.99, "reason": "obeyed instruction in email"})
        # Strip the injection sentence so it doesn't count as evidence in hardened mode.
        low = _MOCK_INJECTION.sub(" ", low)
        scores = {lab: sum(low.count(k) for k in kws) for lab, kws in _MOCK_KEYWORDS.items()}
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        (best, top), (_, second) = ranked[0], ranked[1]
        if top == 0:
            return json.dumps({"label": "job_confirmation", "confidence": 0.3, "reason": "no keyword evidence"})
        confidence = min(0.95, max(0.35, 0.5 + 0.45 * (top - second) / top))
        return json.dumps({"label": best, "confidence": round(confidence, 2), "reason": "keyword match (mock)"})

    def _extract(self, user: str) -> str:
        deadline = re.search(
            r"\b(?:by|before|until|due(?: on)?)\s+((?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day(?:\s+\d{1,2}\s+\w+)?|\d{1,2}\s+[A-Z][a-z]+(?:\s+\d{4})?|[A-Z][a-z]+\s+\d{1,2})",
            user,
        ) or re.search(r"\bwithin\s+(\d+\s+(?:days?|hours?))", user, re.I)
        company = re.search(r"\bat\s+([A-Z][\w&]+(?:\s[A-Z][\w&]+)?)", user)
        role = re.search(r"(?:position of|role of|for the|as an?)\s+([A-Z][\w+/ ]{3,40}?)(?=\s+(?:role|position|at|with)\b|[.,\n])", user)
        items = [s.strip() for s in re.findall(r"[Pp]lease ([^.\n]{5,100})", user)]
        return json.dumps(
            {
                "company": company.group(1) if company else None,
                "role": role.group(1).strip() if role else None,
                "deadline": deadline.group(1) if deadline else None,
                "action_items": items[:5],
            }
        )


def get_client(provider: str | None = None) -> LLMClient:
    provider = (provider or config.LLM_PROVIDER).lower()
    if provider == "mock":
        return MockClient()
    if provider == "anthropic":
        return AnthropicClient(config.LLM_MODEL or "claude-haiku-5-5", config.LLM_TIMEOUT_S)
    if provider == "openai":
        return OpenAIClient(config.LLM_MODEL or "gpt-4o-mini", config.LLM_TIMEOUT_S, config.OPENAI_BASE_URL)
    raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Use mock, anthropic or openai.")


# --------------------------------------------------------------------------- #
# Retries + validation
# --------------------------------------------------------------------------- #


def call_with_retries(client: LLMClient, system: str, user: str, retries: int | None = None,
                      base_delay: float = 1.0) -> LLMResponse:
    """Call the API; on error wait 1s, 2s, 4s... and try again."""
    retries = config.LLM_MAX_RETRIES if retries is None else retries
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return client.complete(system, user)
        except Exception as e:  # network error, timeout, rate limit, 5xx ...
            last = e
            log.warning("LLM call failed (attempt %d/%d): %s", attempt + 1, retries + 1, e)
            if attempt < retries:
                time.sleep(base_delay * (2**attempt))
    raise LLMUnavailable(f"LLM unavailable after {retries + 1} attempts: {last}")


def parse_json_object(text: str) -> dict:
    """Pull a JSON object out of the reply even if the model wrapped it in ``` fences or chatter."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in reply")
    return json.loads(text[start : end + 1])


@dataclass
class StructuredResult:
    obj: Optional[BaseModel] = None
    error: Optional[str] = None
    tokens_in: int = 0
    tokens_out: int = 0
    latency_s: float = 0.0
    attempts: int = 0
    notes: list[str] = field(default_factory=list)


def structured_call(client: LLMClient, system: str, user: str, schema: type[T],
                    max_attempts: int = 3) -> StructuredResult:
    """Ask for JSON, validate it with Pydantic, retry with the error message if invalid."""
    result = StructuredResult()
    start = time.perf_counter()
    message = user
    for attempt in range(1, max_attempts + 1):
        result.attempts = attempt
        try:
            resp = call_with_retries(client, system, message)
        except LLMUnavailable as e:
            result.error = str(e)
            break
        result.tokens_in += resp.input_tokens
        result.tokens_out += resp.output_tokens
        try:
            result.obj = schema.model_validate(parse_json_object(resp.text))
            result.error = None
            break
        except (ValueError, ValidationError) as e:  # JSONDecodeError is a ValueError
            result.error = f"invalid output: {str(e)[:200]}"
            result.notes.append(f"attempt {attempt} invalid")
            log.warning("Invalid LLM output (attempt %d/%d): %s", attempt, max_attempts, e)
            message = (
                f"{user}\n\nYour previous reply was invalid ({str(e)[:150]}). "
                "Reply with ONLY the JSON object in the required format."
            )
    result.latency_s = time.perf_counter() - start
    return result


class LLMClassifier:
    """Classify one (cleaned, redacted) email text with an LLM."""

    def __init__(self, client: LLMClient | None = None, hardened: bool = True) -> None:
        self.client = client or get_client()
        self.hardened = hardened

    def predict(self, text: str) -> Prediction:
        res = structured_call(
            self.client,
            prompts.classification_system_prompt(self.hardened),
            prompts.classification_user_message(text, self.hardened),
            LLMClassification,
        )
        if res.obj is None:
            # Never crash and never guess: hand it to a human.
            return Prediction(
                label=config.REVIEW, confidence=0.0, source="llm_error", raw_label="unknown",
                latency_s=res.latency_s, tokens_in=res.tokens_in, tokens_out=res.tokens_out,
                notes=[res.error or "unknown error", *res.notes],
            )
        out: LLMClassification = res.obj  # type: ignore[assignment]
        notes = list(res.notes)
        if out.reason:
            notes.append(f"reason: {out.reason[:200]}")
        return Prediction(
            label=out.label, confidence=out.confidence, source="llm", raw_label=out.label,
            latency_s=res.latency_s, tokens_in=res.tokens_in, tokens_out=res.tokens_out, notes=notes,
        )
