import logging
import shutil
import tempfile
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .chain import AskResult, ask
from .ingest import get_store, ingest_pdf
from .config import get_settings
from .models import get_llm
from .retrieval import HybridRetriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("docmind.api")
app = FastAPI(title="DocuMind", description="Ask your documents (LangChain RAG)")

_state: dict = {}


def pipeline():
    """Lazy singletons; rebuilt after each ingest so BM25 sees new chunks."""
    if "retriever" not in _state:
        s = get_settings()
        _state["retriever"] = HybridRetriever(get_store(), fetch_k=s.fetch_k, top_k=s.top_k)
        _state["llm"] = get_llm()
    return _state["retriever"], _state["llm"]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    category: str | None = Field(None, description="metadata filter")
    mode: Literal["dense", "sparse", "hybrid"] = "hybrid"
    rerank: bool = True
    rewrite: bool = True
    history: list[str] = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(file: UploadFile = File(...), category: str = Form("general")):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, prefix=file.filename[:-4] + "_") as tmp:
        shutil.copyfileobj(file.file, tmp)
    n = ingest_pdf(tmp.name, category=category)
    _state.clear()
    return {"filename": file.filename, "chunks": n, "category": category}


@app.post("/ask", response_model=AskResult)
def ask_endpoint(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(422, "question must not be blank")
    retriever, llm = pipeline()
    try:
        return ask(req.question, retriever, llm,
                   filters={"category": req.category} if req.category else None,
                   mode=req.mode, rerank=req.rerank, rewrite=req.rewrite, history=req.history)
    except Exception:
        log.exception("ask failed after retries")
        raise HTTPException(502, "The language model failed to return a valid answer. Try again.")
