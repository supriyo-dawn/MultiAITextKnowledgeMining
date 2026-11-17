"""API routes for analytics and metrics."""

from fastapi import APIRouter
from sqlalchemy import func, select

from app.models.document import DocumentStatus
from app.models.db_models import EmbeddingDB, EntityDB, RelationshipDB
from app.core.database import async_session_factory
from app.api.routes.chunks import chunk_service
from app.services.document_service import get_document_count, get_documents_by_status
from app.services.knowledge_service import list_persisted_entities, list_persisted_relationships

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
@router.get("/summary")
async def get_analytics_summary():
    """Get counts for currently available document and chunk data."""
    status_counts = {
        status.value: len(await get_documents_by_status(status))
        for status in DocumentStatus
    }
    async with async_session_factory() as session:
        embedding_count = await session.scalar(select(func.count(EmbeddingDB.chunk_id))) or 0
        entity_count = await session.scalar(select(func.count(EntityDB.id))) or 0
        relationship_count = await session.scalar(select(func.count(RelationshipDB.id))) or 0
    return {
        "documents": {
            "total": await get_document_count(),
            "by_status": status_counts,
        },
        "chunks": await chunk_service.get_statistics(),
        "entities": {"total": entity_count, "available": True},
        "relationships": {"total": relationship_count, "available": True},
        "embeddings": {"total": embedding_count, "available": True},
    }


@router.get("/entities")
async def get_entity_analytics():
    """Return entity counts grouped by extracted label."""
    entities = await list_persisted_entities()
    by_type: dict[str, int] = {}
    for entity in entities:
        by_type[entity.label] = by_type.get(entity.label, 0) + 1
    return {"total": len(entities), "by_type": by_type, "available": True}


@router.get("/relationships")
async def get_relationship_analytics():
    """Return relationship counts grouped by relation type."""
    relationships = await list_persisted_relationships()
    by_type: dict[str, int] = {}
    for relationship in relationships:
        by_type[relationship.relation_type] = by_type.get(relationship.relation_type, 0) + 1
    return {"total": len(relationships), "by_type": by_type, "available": True}


@router.get("/performance")
async def get_performance_metrics():
    """Return metrics for the currently implemented processing pipeline."""
    return {
        "document_processing": {"available": True, "failed_documents": len(
            await get_documents_by_status(DocumentStatus.FAILED)
        )},
        "entity_extraction": {"available": True},
        "relationship_extraction": {"available": True},
        "embeddings": {"available": True},
    }
