import pytest

from app.services.knowledge_service import (
    list_persisted_entities,
    list_persisted_relationships,
    persist_document_knowledge,
)


@pytest.mark.asyncio
async def test_knowledge_is_persisted_and_relationships_are_validated():
    entities, relationships = await persist_document_knowledge(
        "doc-persistent",
        "Alice works with Acme University.",
    )

    persisted_entities = await list_persisted_entities("doc-persistent")
    persisted_relationships = await list_persisted_relationships("doc-persistent")

    assert len(entities) == 2
    assert len(persisted_entities) == 2
    assert len(persisted_relationships) == 1
    assert persisted_relationships[0].relation_type == "COLLABORATES_WITH"
    assert persisted_relationships[0].source_entity_id != persisted_relationships[0].target_entity_id
    assert all(item.document_id == "doc-persistent" for item in persisted_relationships)
