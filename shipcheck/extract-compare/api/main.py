"""
Production-ready FastAPI application for ShipCheck backend.
Connects with the ShipCheck React frontend.
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure repository root is on sys.path
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

load_dotenv()

from api.db import init_db
from api.routes import classify, compare, health, emails, comparisons, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    init_db()
    yield
    # Shutdown cleanup if any


app = FastAPI(
    title="ShipCheck Backend Service",
    description="Backend API powering the ShipCheck shipping operations frontend.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware configured for React frontend (Vite / CRA / Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits localhost:5173, localhost:3000, and preview domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api namespace
app.include_router(classify.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(emails.router, prefix="/api")
app.include_router(comparisons.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(auth.router)

# Also alias without /api prefix for convenience
app.include_router(classify.router)
app.include_router(compare.router)
app.include_router(emails.router)
app.include_router(comparisons.router)
app.include_router(health.router)


@app.get("/v1/models", summary="Compatibility endpoint for local AI model discovery")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "shipcheck-classifier", "object": "model", "owned_by": "shipcheck"}
        ]
    }


@app.get("/", summary="Root status and documentation link")
async def root():
    return {
        "service": "ShipCheck Backend API",
        "status": "online",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "emails_list": "GET /api/emails",
            "emails_batch_sync": "POST /api/emails/batch",
            "classify": "POST /api/classify",
            "compare_files": "POST /api/compare",
            "compare_text": "POST /api/compare/text",
            "comparisons_list": "GET /api/comparisons",
        },
    }
