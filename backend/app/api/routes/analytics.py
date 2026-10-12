"""API routes for analytics and metrics."""

from fastapi import APIRouter

from app.models.document import DocumentStatus
from app.api.routes.chunks import chunk_service
from app.services.document_service import get_document_count, get_documents_by_status
from app.services.knowledge_service import get_entities, get_relationships

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
@router.get("/summary")
async def get_analytics_summary():
    """Get counts for currently available document and chunk data."""
    status_counts = {
        status.value: len(await get_documents_by_status(status))
        for status in DocumentStatus
    }
    return {
        "documents": {
            "total": await get_document_count(),
            "by_status": status_counts,
        },
        "chunks": await chunk_service.get_statistics(),
        "entities": {"total": len(get_entities()), "available": True},
        "relationships": {"total": len(get_relationships()), "available": True},
        "embeddings": {"total": 0, "available": False},
    }


@router.get("/entities")
async def get_entity_analytics():
    """Return entity analytics when entity extraction is available."""
    return {"total": 0, "by_type": {}, "available": False}


@router.get("/relationships")
async def get_relationship_analytics():
    """Return relationship analytics when extraction is available."""
    return {"total": 0, "by_type": {}, "available": False}


@router.get("/performance")
async def get_performance_metrics():
    """Return metrics for the currently implemented processing pipeline."""
    return {
        "document_processing": {"available": True, "failed_documents": len(
            await get_documents_by_status(DocumentStatus.FAILED)
        )},
        "entity_extraction": {"available": False},
        "relationship_extraction": {"available": False},
        "embeddings": {"available": False},
    }
