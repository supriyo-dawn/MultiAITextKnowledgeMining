"""API routes for knowledge graph operations."""

from collections import deque

from fastapi import APIRouter, Query

from app.services.knowledge_service import (
    get_entities,
    get_entity as find_entity,
    get_relationships,
    list_persisted_entities,
    list_persisted_relationships,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/entities")
async def list_entities(document_id: str | None = None):
    """List locally extracted entities."""
    entities = await list_persisted_entities(document_id)
    return {"available": True, "entities": entities, "total_count": len(entities)}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """Get a locally extracted entity."""
    entity = next((item for item in await list_persisted_entities() if item.id == entity_id), find_entity(entity_id))
    return {"available": True, "entity": entity, "entity_id": entity_id}


@router.get("/relationships")
async def list_relationships(document_id: str | None = None):
    """List locally extracted relationships."""
    relationships = await list_persisted_relationships(document_id)
    return {"available": True, "relationships": relationships, "total_count": len(relationships)}


@router.get("/graph")
async def get_graph():
    """Get the locally extracted graph structure."""
    entities = await list_persisted_entities()
    relationships = await list_persisted_relationships()
    return {"available": True, "nodes": entities, "edges": relationships}


@router.get("/neighbors/{entity_id}")
async def get_entity_neighbors(entity_id: str):
    """Get locally extracted neighbors for an entity."""
    relationships = [
        item for item in await list_persisted_relationships()
        if item.source_entity_id == entity_id or item.target_entity_id == entity_id
    ]
    return {"available": True, "entity_id": entity_id, "neighbors": relationships}


@router.get("/path")
async def get_path(source_id: str = Query(...), target_id: str = Query(...)):
    """Find a shortest path through locally extracted relationships."""
    adjacency: dict[str, list[str]] = {}
    for relationship in await list_persisted_relationships():
        adjacency.setdefault(relationship.source_entity_id, []).append(relationship.target_entity_id)
        adjacency.setdefault(relationship.target_entity_id, []).append(relationship.source_entity_id)
    queue = deque([(source_id, [source_id])])
    visited = {source_id}
    while queue:
        current, path = queue.popleft()
        if current == target_id:
            return {"available": True, "path": path}
        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return {"available": True, "path": []}
