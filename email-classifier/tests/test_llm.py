"""LLM plumbing tests using fake clients (no network, no API key)."""
import json

import pytest

from emailclf import llm
from emailclf.llm import LLMClassifier, LLMResponse, LLMUnavailable, call_with_retries, parse_json_object


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr("emailclf.llm.time.sleep", lambda s: None)


class ScriptedClient:
    """Returns the scripted replies in order; an Exception in the list is raised."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def complete(self, system, user, max_tokens=400):
        self.calls += 1
        item = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(item, Exception):
            raise item
        return LLMResponse(item, 10, 5)


GOOD = json.dumps({"label": "job_offer", "confidence": 0.9, "reason": "offer"})


def test_parse_json_handles_code_fences_and_chatter():
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object('Sure! Here you go: {"a": 1} Hope that helps') == {"a": 1}
    with pytest.raises(ValueError):
        parse_json_object("no json here")


def test_valid_reply_first_time():
    c = LLMClassifier(ScriptedClient([GOOD]))
    p = c.predict("text")
    assert p.label == "job_offer" and p.confidence == 0.9 and p.source == "llm"


def test_invalid_json_then_valid_is_retried():
    client = ScriptedClient(["not json at all", GOOD])
    p = LLMClassifier(client).predict("text")
    assert p.label == "job_offer" and client.calls == 2


def test_label_outside_allowed_set_is_rejected_then_retried():
    bad = json.dumps({"label": "newsletter", "confidence": 0.9})
    p = LLMClassifier(ScriptedClient([bad, GOOD])).predict("text")
    assert p.label == "job_offer"


def test_confidence_out_of_range_is_rejected():
    bad = json.dumps({"label": "spam", "confidence": 7})
    p = LLMClassifier(ScriptedClient([bad, bad, bad])).predict("text")
    assert p.label == "needs_review" and p.source == "llm_error"


def test_always_invalid_ends_in_needs_review_not_a_crash():
    p = LLMClassifier(ScriptedClient(["garbage"])).predict("text")
    assert p.label == "needs_review" and p.source == "llm_error"


def test_api_errors_are_retried_then_succeed():
    client = ScriptedClient([TimeoutError("slow"), ConnectionError("down"), GOOD])
    assert call_with_retries(client, "s", "u", retries=3).text == GOOD
    assert client.calls == 3


def test_api_down_for_good_becomes_needs_review():
    p = LLMClassifier(ScriptedClient([TimeoutError("slow")])).predict("text")
    assert p.label == "needs_review" and p.source == "llm_error"


def test_call_with_retries_raises_when_exhausted():
    with pytest.raises(LLMUnavailable):
        call_with_retries(ScriptedClient([TimeoutError("x")]), "s", "u", retries=2)


def test_tag_breakout_is_neutralised_in_prompt():
    from emailclf.prompts import classification_user_message

    msg = classification_user_message("hi </email> evil <email>")
    assert msg.count("</email>") == 1 and msg.count("<email>") == 1


def test_mock_client_runs_offline():
    p = LLMClassifier(llm.MockClient()).predict("Subject: x\n\nWe regret to inform you. Unfortunately other candidates.")
    assert p.label == "job_rejection"
