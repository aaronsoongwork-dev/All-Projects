"""Retrieval: dense + sparse (BM25) -> RRF fusion -> metadata filter -> cross-encoder rerank.
Also: query rewriting."""
import logging
import re

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .models import get_reranker

log = logging.getLogger("docmind.retrieval")


def tokenize(text: str) -> list[str]:
    # BM25Retriever's default just does text.split() (no lowercasing / punctuation handling)
    return re.findall(r"\w+", text.lower())


def chroma_filter(filters: dict | None) -> dict | None:
    """Chroma wants {"k": v} for one condition and {"$and": [...]} for several."""
    if not filters:
        return None
    items = [{k: v} for k, v in filters.items()]
    return items[0] if len(items) == 1 else {"$and": items}


def rrf(rankings: list[list[Document]], k: int = 60) -> list[Document]:
    """Reciprocal Rank Fusion: score = sum(1 / (k + rank)). Merges lists whose raw scores
    (cosine vs BM25) are not comparable, using only ranks."""
    scores: dict[str, float] = {}
    docs: dict[str, Document] = {}
    for ranking in rankings:
        for rank, d in enumerate(ranking, start=1):
            cid = d.metadata["chunk_id"]
            docs[cid] = d
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    return [docs[c] for c in sorted(scores, key=scores.get, reverse=True)]


class HybridRetriever:
    def __init__(self, store, fetch_k: int = 15, top_k: int = 4):
        self.store, self.fetch_k, self.top_k = store, fetch_k, top_k
        raw = store.get(include=["documents", "metadatas"])
        self.all_docs = [Document(page_content=t, metadata=m)
                         for t, m in zip(raw["documents"], raw["metadatas"])]
        self._bm25_cache: dict[tuple, BM25Retriever | None] = {}

    def _bm25(self, filters: dict | None):
        key = tuple(sorted((filters or {}).items()))
        if key not in self._bm25_cache:
            docs = [d for d in self.all_docs
                    if all(d.metadata.get(k) == v for k, v in (filters or {}).items())]
            self._bm25_cache[key] = (
                BM25Retriever.from_documents(docs, preprocess_func=tokenize, k=self.fetch_k)
                if docs else None)
        return self._bm25_cache[key]

    def dense(self, query, filters=None):
        return self.store.similarity_search(query, k=self.fetch_k, filter=chroma_filter(filters))

    def sparse(self, query, filters=None):
        bm25 = self._bm25(filters)
        return bm25.invoke(query) if bm25 else []

    def retrieve(self, query: str, filters: dict | None = None,
                 mode: str = "hybrid", rerank: bool = True) -> list[Document]:
        if mode == "dense":
            cands = self.dense(query, filters)
        elif mode == "sparse":
            cands = self.sparse(query, filters)
        else:
            cands = rrf([self.dense(query, filters), self.sparse(query, filters)])
        cands = cands[: self.fetch_k]
        reranker = get_reranker() if rerank else None
        if reranker and cands:
            scores = reranker.predict([(query, d.page_content) for d in cands])
            cands = [d for _, d in sorted(zip(scores, cands), key=lambda x: x[0], reverse=True)]
        return cands[: self.top_k]


REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Rewrite the user's question as ONE standalone search query for a document search engine. "
     "Resolve pronouns using the chat history, expand abbreviations, keep key names and numbers. "
     "Output only the query, nothing else."),
    ("human", "Chat history:\n{history}\n\nQuestion: {question}"),
])


def rewrite_query(llm, question: str, history: list[str] | None = None) -> str:
    try:
        chain = REWRITE_PROMPT | llm | StrOutputParser()
        out = chain.invoke({"question": question, "history": "\n".join(history or []) or "(none)"})
        return out.strip().strip('"') or question
    except Exception:  # rewriting is an optimisation: never let it break the request
        log.warning("query rewrite failed, using original question", exc_info=True)
        return question
