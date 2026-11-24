# DocuMind: ask your documents (LangChain RAG)

FastAPI + LangChain + Chroma. Upload a PDF, ask questions, get an answer plus source page numbers.

## What's in it, mapped to your Day 2 notes and the JD
| Piece | File | Day 2 topic | JD line |
|---|---|---|---|
| Loader -> splitter -> metadata -> Chroma | `app/ingest.py` | loaders, text splitters, embeddings | RAG, vector DBs, embeddings |
| Dense + BM25 + RRF fusion | `app/retrieval.py` | hybrid search | RAG |
| Metadata filter (`category`) | `retrieval.py`, `main.py` | metadata filtering | RAG |
| Cross-encoder rerank | `retrieval.py`, `models.py` | reranking | optimise accuracy |
| LLM query rewriting (+ safe fallback) | `retrieval.py` | query rewriting | prompt engineering |
| LCEL chain, Pydantic JSON, retries | `app/chain.py` | LCEL, RAG triad | LLM APIs, reliability |
| Faithfulness guard (citations must be retrieved pages) | `chain.py` | RAG triad: faithfulness | accuracy |
| REST API, validation, logging, 502 on failure | `app/main.py` | | backend, APIs |
| Docker | `Dockerfile` | | Docker, Linux |
| chunk size x retrieval method experiment | `eval/run_eval.py` | Mini experiment D | model evaluation |
| Offline tests (fake LLM/embeddings) | `tests/` | | debugging, maintainability |
| Swappable provider (`LLM_PROVIDER=ollama`) | `models.py` | | local model hosting |

## Run
    pip install -r requirements.txt
    cp .env.example .env           # add your API key
    uvicorn app.main:app --reload
    curl -F file=@data/my_cv.pdf -F category=cv localhost:8000/ingest
    curl -X POST localhost:8000/ask -H 'content-type: application/json' \
         -d '{"question":"Where did I study?","category":"cv"}'
    pytest                         # no API key or model download needed
    python -m eval.run_eval data/my_cv.pdf eval/questions.json

## Experiment D (your interview story)
Write 10 questions on a PDF you know, with the exact text that must appear in the right chunk.
Run `eval.run_eval`. Compare chunk 200 vs 800 and dense / sparse / hybrid / hybrid+rerank.
The bundled `data/sample.pdf` is only a smoke test (3 chunks, so everything scores 100%).
Use a real multi-page PDF or the numbers mean nothing.

## Phase 2: fine-tuning (separate step, not part of the request path)
1. Use the eval questions plus the chunks they should hit as (query, positive chunk) pairs.
2. Fine-tune the embedding model with sentence-transformers (`MultipleNegativesRankingLoss`).
3. Point `EMBEDDINGS_MODEL` at the new model, re-ingest, re-run `eval.run_eval`.
4. The before/after hit-rate is the result to talk about. Fine-tuning the generator LLM is
   usually not worth it for this use case.

## Phase 3 ideas
LangGraph agent that decides between search, a calculator and "ask the user"; email-classifier
tool from your Day 1 list; prompt-injection test set; a cloud-deploy variant.
