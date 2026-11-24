"""Mini experiment D: how often is the right chunk retrieved?
Compares chunk sizes x retrieval modes on YOUR questions with known answers.

  python -m eval.run_eval data/my_cv.pdf eval/questions.json
questions.json: [{"question": "...", "expected": "text that must appear in the right chunk"}, ...]
"""
import json
import sys
import tempfile

from app.config import get_settings
from app.ingest import get_store, load_and_split
from app.retrieval import HybridRetriever

CONFIGS = [("dense", False), ("sparse", False), ("hybrid", False), ("hybrid", True)]


def hit_rate(retriever, questions, mode, rerank, k):
    hits = 0
    for q in questions:
        docs = retriever.retrieve(q["question"], None, mode, rerank)[:k]
        hits += any(q["expected"].lower() in d.page_content.lower() for d in docs)
    return hits / len(questions)


def run(pdf, questions, chunk_sizes=(200, 800), k=None):
    s = get_settings()
    k = k or s.top_k
    rows = []
    for size in chunk_sizes:
        with tempfile.TemporaryDirectory() as tmp:
            store = get_store(tmp, collection=f"eval_{size}")
            chunks = load_and_split(pdf, size)
            store.add_documents(chunks, ids=[c.metadata["chunk_id"] for c in chunks])
            r = HybridRetriever(store, fetch_k=s.fetch_k, top_k=k)
            for mode, rerank in CONFIGS:
                rows.append((size, len(chunks), f"{mode}{'+rerank' if rerank else ''}",
                             hit_rate(r, questions, mode, rerank, k)))
    return rows


if __name__ == "__main__":
    pdf, qfile = sys.argv[1], sys.argv[2]
    qs = json.load(open(qfile))
    print(f"{len(qs)} questions, hit@{get_settings().top_k}\n")
    print(f"{'chunk':>6} {'#chunks':>8}  {'method':<16} hit-rate")
    for size, n, method, rate in run(pdf, qs):
        print(f"{size:>6} {n:>8}  {method:<16} {rate:.0%}")
