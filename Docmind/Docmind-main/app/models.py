"""Model factories. Swapping providers is a config change, not a code change."""
from functools import lru_cache

from .config import get_settings


def get_embeddings():
    s = get_settings()
    if s.embeddings_provider == "fake":  # tests only: deterministic, not semantic
        from langchain_core.embeddings import DeterministicFakeEmbedding
        return DeterministicFakeEmbedding(size=256)
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=s.embeddings_model,
        encode_kwargs={"normalize_embeddings": True},  # cosine similarity = dot product
    )


def get_llm():
    """temperature=0 (consistent, fewer hallucinations); retries are done in LCEL, not the SDK."""
    s = get_settings()
    if s.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=s.llm_model, temperature=0,
                                      timeout=s.llm_timeout, max_retries=5)
    if s.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=s.llm_model, temperature=0, timeout=s.llm_timeout, max_retries=0)
    if s.llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=s.llm_model, temperature=0, timeout=s.llm_timeout, max_retries=0)
    if s.llm_provider == "ollama":  # fully local model hosting
        from langchain_ollama import ChatOllama
        return ChatOllama(model=s.llm_model, temperature=0, client_kwargs={"timeout": s.llm_timeout})
    raise ValueError(f"Unknown LLM_PROVIDER: {s.llm_provider}")


@lru_cache(maxsize=1)
def get_reranker():
    """Cross-encoder: reads (query, chunk) TOGETHER, so it is slower but more accurate than embeddings."""
    s = get_settings()
    if s.reranker_model.lower() == "none":
        return None
    from sentence_transformers import CrossEncoder
    return CrossEncoder(s.reranker_model)
