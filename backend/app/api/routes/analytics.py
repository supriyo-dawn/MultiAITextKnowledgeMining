"""API routes for analytics and metrics."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
async def get_analytics_summary():
    """Get overall analytics summary. (Phase 1 stub)"""
    return {"message": "Analytics coming in Phase 13"}


@router.get("/entities")
async def get_entity_analytics():
    """Get entity extraction analytics. (Phase 1 stub)"""
    return {"message": "Entity analytics coming in Phase 13"}


@router.get("/relationships")
async def get_relationship_analytics():
    """Get relationship extraction analytics. (Phase 1 stub)"""
    return {"message": "Relationship analytics coming in Phase 13"}


@router.get("/performance")
async def get_performance_metrics():
    """Get model performance metrics. (Phase 1 stub)"""
    return {"message": "Performance metrics coming in Phase 13"}
