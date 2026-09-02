"""API routes for knowledge graph operations."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/entities")
async def list_entities():
    """List all extracted entities. (Phase 1 stub)"""
    return {"message": "Entity listing coming in Phase 7"}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """Get entity details. (Phase 1 stub)"""
    return {"message": "Entity details coming in Phase 7"}


@router.get("/relationships")
async def list_relationships():
    """List all extracted relationships. (Phase 1 stub)"""
    return {"message": "Relationship listing coming in Phase 7"}


@router.get("/graph")
async def get_graph():
    """Get full graph structure. (Phase 1 stub)"""
    return {"message": "Graph retrieval coming in Phase 7"}


@router.get("/neighbors/{entity_id}")
async def get_entity_neighbors(entity_id: str):
    """Get neighbors of an entity in the graph. (Phase 1 stub)"""
    return {"message": "Neighbor retrieval coming in Phase 7"}


@router.get("/path")
async def get_path():
    """Get shortest path between entities. (Phase 1 stub)"""
    return {"message": "Path finding coming in Phase 7"}
