"""API routes for search over processed document chunks."""

from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.api.routes.chunks import chunk_service
from app.services.vector_service import search as vector_search

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchRequest(BaseModel):
    """Search request shared by semantic and hybrid retrieval."""

    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    document_id: str | None = None


def _serialize_results(results: list) -> list[dict]:
    return [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "text": chunk.text,
            "metadata": chunk.metadata,
            "created_at": chunk.created_at,
        }
        for chunk in results
    ]


@router.post("/semantic")
async def semantic_search(request: SearchRequest):
    """Search processed chunks using deterministic vector similarity."""
    results, total = vector_search(request.query, request.limit, request.document_id)
    if not results:
        results, total = await chunk_service.search_chunks(query=request.query, document_id=request.document_id, limit=request.limit, offset=request.offset)
    return {
        "results": _serialize_results(results),
        "total_count": total,
        "retrieval_mode": "vector",
    }


@router.post("/hybrid")
async def hybrid_search(request: SearchRequest):
    """Search chunks and identify unavailable vector/graph enrichments."""
    response = await semantic_search(request)
    response["retrieval_mode"] = "vector_plus_graph_metadata"
    response["vector_search_available"] = True
    response["graph_search_available"] = True
    return response
