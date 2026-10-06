"""
Multi-AI Text Knowledge Mining & Knowledge Graph System
Backend main application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, chunks, knowledge, search, chat, analytics
from app.core.config import settings
from app.core.logging import setup_logging

from app.core.database import init_db, shutdown_db

# Setup logging
setup_logging(settings.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Multi-AI Knowledge Graph System")
    await init_db()
    yield
    await shutdown_db()
    logger.info("Shutting down Multi-AI Knowledge Graph System")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Multi-AI Text Knowledge Mining & Knowledge Graph System",
        description="Academic project: document ingestion, NER, relationship extraction, knowledge graphs, and RAG",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(documents.router)
    app.include_router(chunks.router)
    app.include_router(knowledge.router)
    app.include_router(search.router)
    app.include_router(chat.router)
    app.include_router(analytics.router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Multi-AI Knowledge Graph System",
            "docs": "/docs",
            "version": "0.1.0",
        }

    logger.info("FastAPI application created successfully")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
