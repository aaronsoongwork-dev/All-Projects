"""
Health check and system info route.
"""
import os
from fastapi import APIRouter
from api.schemas import HealthResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check() -> HealthResponse:
    has_openrouter = bool(os.environ.get("OPENROUTER_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        providers={
            "openrouter": has_openrouter,
            "anthropic": has_anthropic,
        },
    )

