"""Ingestion: load PDF -> split -> attach metadata -> embed into Chroma."""
import logging
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import get_settings
from .models import get_embeddings

log = logging.getLogger("docmind.ingest")
COLLECTION = "docmind"


def load_and_split(pdf_path: str, chunk_size: int, category: str = "general") -> list[Document]:
    pages = PyPDFLoader(pdf_path).load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_size // 10, add_start_index=True
    )
    chunks = splitter.split_documents(pages)
    source = Path(pdf_path).name
    for i, c in enumerate(chunks):
        page = int(c.metadata.get("page", 0)) + 1          # PyPDF pages are 0-indexed
        c.metadata = {
            "source": source,
            "page": page,
            "category": category,                           # <- metadata filtering uses this
            "chunk_id": f"{source}:p{page}:c{i}",
        }
    log.info("split %s into %d chunks (chunk_size=%d)", source, len(chunks), chunk_size)
    return chunks


def get_store(persist_dir: str | None = None, collection: str = COLLECTION) -> Chroma:
    return Chroma(
        collection_name=collection,
        embedding_function=get_embeddings(),
        persist_directory=persist_dir or get_settings().chroma_dir,
        collection_metadata={"hnsw:space": "cosine"},
    )


def ingest_pdf(pdf_path: str, category: str = "general", chunk_size: int | None = None,
               store: Chroma | None = None) -> int:
    s = get_settings()
    chunks = load_and_split(pdf_path, chunk_size or s.chunk_size, category)
    store = store or get_store()
    store.add_documents(chunks, ids=[c.metadata["chunk_id"] for c in chunks])
    return len(chunks)
