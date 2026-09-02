"""API routes for semantic search operations."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/semantic")
async def semantic_search():
    """Search documents using semantic similarity. (Phase 1 stub)"""
    return {"message": "Semantic search coming in Phase 8"}


@router.post("/hybrid")
async def hybrid_search():
    """Hybrid search combining vector and graph retrieval. (Phase 1 stub)"""
    return {"message": "Hybrid search coming in Phase 9"}
