import json

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app.chain import ask
from app.retrieval import chroma_filter, rewrite_query, rrf


def fake_llm(replies):
    """Stand-in LLM: pops canned replies in order (a reply may be an Exception to raise)."""
    replies = list(replies)

    def _call(_prompt):
        r = replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return AIMessage(content=r)
    return RunnableLambda(_call)


GOOD = json.dumps({"answer": "18 days", "found": True, "cited_pages": [1]})


def test_sparse_finds_exact_keyword(retriever):
    docs = retriever.retrieve("VPN token", mode="sparse", rerank=False)
    assert docs[0].metadata["page"] == 2


def test_hybrid_returns_keyword_hit(retriever):
    docs = retriever.retrieve("director approval RM500", mode="hybrid", rerank=False)
    assert 3 in [d.metadata["page"] for d in docs]


def test_metadata_filter_applies_to_both_retrievers(retriever):
    for mode in ("dense", "sparse", "hybrid"):
        docs = retriever.retrieve("policy", {"category": "it"}, mode, False)
        assert docs and {d.metadata["category"] for d in docs} == {"it"}


def test_chroma_filter_shape():
    assert chroma_filter(None) is None
    assert chroma_filter({"a": 1}) == {"a": 1}
    assert chroma_filter({"a": 1, "b": 2}) == {"$and": [{"a": 1}, {"b": 2}]}


def test_rrf_rewards_agreement():
    from langchain_core.documents import Document
    d = lambda i: Document(page_content=i, metadata={"chunk_id": i})
    fused = rrf([[d("a"), d("b")], [d("c"), d("b")]])
    assert fused[0].metadata["chunk_id"] == "b"       # appears in both lists


def test_rewrite_falls_back_on_llm_failure():
    assert rewrite_query(fake_llm([RuntimeError("down")]), "what is it?") == "what is it?"


def test_ask_end_to_end_with_sources(retriever):
    r = ask("How many days of annual leave?", retriever, fake_llm(["annual leave days", GOOD]),
            rerank=False)
    assert r.found and r.answer == "18 days"
    assert [s.page for s in r.sources] == [1]
    assert r.rewritten_query == "annual leave days"


def test_bad_json_is_retried_then_succeeds(retriever):
    llm = fake_llm(["rq", "not json at all", "{broken", GOOD])
    assert ask("annual leave", retriever, llm, rerank=False).answer == "18 days"


def test_invented_citation_is_dropped(retriever):
    bad = json.dumps({"answer": "x", "found": True, "cited_pages": [99]})
    r = ask("annual leave", retriever, fake_llm(["rq", bad]), rerank=False)
    assert 99 not in [s.page for s in r.sources]


def test_no_results_skips_llm(retriever):
    llm = fake_llm([])  # any call would raise IndexError
    r = ask("anything", retriever, llm, filters={"category": "nope"}, mode="sparse",
            rerank=False, rewrite=False)
    assert not r.found and r.sources == []


def test_api_rejects_empty_question():
    from app.main import app
    c = TestClient(app)
    assert c.post("/ask", json={"question": ""}).status_code == 422
    assert c.post("/ask", json={"question": "   "}).status_code == 422
