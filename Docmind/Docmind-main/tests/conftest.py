import os
os.environ["EMBEDDINGS_PROVIDER"] = "fake"   # no model downloads in tests
os.environ["RERANKER_MODEL"] = "none"

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

PAGES = [
    ("hr", "Employee handbook. Annual leave is 18 days per year. Probation lasts 3 months."),
    ("it", "IT policy. Laptops must use full disk encryption. VPN token rotates every 30 days."),
    ("finance", "Finance policy. Expense claims above RM500 need director approval within 7 days."),
]


@pytest.fixture(scope="session")
def pdf_path(tmp_path_factory):
    p = tmp_path_factory.mktemp("d") / "handbook.pdf"
    c = canvas.Canvas(str(p), pagesize=A4)
    for _, text in PAGES:
        c.drawString(72, 750, text)
        c.showPage()
    c.save()
    return str(p)


@pytest.fixture()
def retriever(pdf_path, tmp_path):
    from app.ingest import get_store, load_and_split
    from app.retrieval import HybridRetriever
    store = get_store(str(tmp_path / "db"), collection="test_docs")
    chunks = load_and_split(pdf_path, 800)
    for ch in chunks:                      # category per page, to test metadata filtering
        ch.metadata["category"] = PAGES[ch.metadata["page"] - 1][0]
    store.add_documents(chunks, ids=[c.metadata["chunk_id"] for c in chunks])
    return HybridRetriever(store, fetch_k=10, top_k=2)
