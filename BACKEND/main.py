"""
BACKEND/main.py
Production-grade FastAPI application entry point
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from BACKEND.config import get_settings
from BACKEND.routes import router

settings = get_settings()

# ─── Logging setup ────────────────────────────────────────────────────────────
logger.remove()
logger.add(sys.stderr, level="INFO",
           format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")
logger.add("BACKEND/app.log", rotation="10 MB", retention="7 days", level="DEBUG")


# ─── Startup / Shutdown ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info(f"  ProofSAR AI v{settings.app_version} starting …")
    logger.info(f"  Environment : {settings.app_env}")
    logger.info(f"  Docs        : http://{settings.app_host}:{settings.app_port}/docs")
    logger.info("=" * 60)

    # Pre-load ML model so first request is fast
    try:
        from ML.train_model import load_model
        load_model()
        logger.success("ML model loaded")
    except Exception as e:
        logger.warning(f"ML model pre-load failed (will load on first request): {e}")

    # Ensure audit dir exists
    os.makedirs("AUDIT",   exist_ok=True)
    os.makedirs("REPORTS", exist_ok=True)
    os.makedirs("AUTH",    exist_ok=True)

    # Database Initialization
    try:
        from BACKEND.database import init_db
        from AUTH.auth import seed_default_users
        init_db()
        seed_default_users()
        logger.success("PostgreSQL/SQLite database initialized and seeded")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    yield   # ← app is running

    logger.info("ProofSAR AI shutting down …")


# ─── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title       = settings.app_name,
    description = (
        "**ProofSAR AI** — Explainable Anti-Money Laundering & SAR Generation System.\n\n"
        "Detects suspicious transactions using ML + C++ rules, explains decisions via SHAP, "
        "generates regulator-ready SAR reports, and maintains a tamper-proof audit log."
    ),
    version     = settings.app_version,
    docs_url    = "/docs",
    redoc_url   = "/redoc",
    lifespan    = lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.allow_origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ─── Request timing middleware ────────────────────────────────────────────────
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start   = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.3f}s"
    response.headers["X-PoweredBy"]    = "ProofSAR-AI"
    return response


# ─── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code = 500,
        content     = {
            "error":   "Internal server error",
            "detail":  str(exc),
            "path":    str(request.url.path),
            "service": "ProofSAR AI"
        }
    )


# ─── Mount all routes ─────────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")

# Alias without prefix for convenience
app.include_router(router)


# ─── Root endpoint ────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "service":     "ProofSAR AI",
        "version":     settings.app_version,
        "status":      "operational",
        "docs":        "/docs",
        "health":      "/health",
        "description": "Explainable AML & SAR Generation System"
    }


# ─── Dev entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "BACKEND.main:app",
        host    = settings.app_host,
        port    = settings.app_port,
        reload  = not settings.is_production,
        workers = 1,
    )
