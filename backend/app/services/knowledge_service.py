"""Deterministic local entity and relationship extraction."""

from datetime import timezone
import re
from uuid import uuid4

from sqlalchemy import delete, select

from app.ai.ner import extract_entity_spans
from app.core.database import async_session_factory
from app.models.knowledge import Entity, Relationship
from app.models.db_models import EntityDB, RelationshipDB

_entities: dict[str, Entity] = {}
_relationships: dict[str, Relationship] = {}

def extract_entities(text: str, document_id: str) -> list[Entity]:
    entities = []
    seen: set[tuple[str, str]] = set()
    for span in extract_entity_spans(text):
        key = (span.text.casefold(), span.label)
        if key in seen:
            continue
        seen.add(key)
        entity = Entity(
            document_id=document_id,
            text=span.text,
            label=span.label,
            confidence=span.confidence,
            start_position=span.start_position,
            end_position=span.end_position,
        )
        _entities[entity.id] = entity
        entities.append(entity)
    return entities


def extract_relationships(text: str, document_id: str, entities: list[Entity]) -> list[Relationship]:
    relationships = []
    for left_index, left in enumerate(entities):
        for right in entities[left_index + 1:]:
            if left.document_id != document_id or right.document_id != document_id or left.id == right.id:
                continue
            if right.start_position - left.end_position > 240:
                continue
            evidence = text[max(0, left.start_position - 60):min(len(text), right.end_position + 60)]
            relation_type = _relation_type(evidence)
            relationship = Relationship(document_id=document_id, source_entity_id=left.id, target_entity_id=right.id, relation_type=relation_type, evidence=evidence, confidence=0.55)
            _relationships[relationship.id] = relationship
            relationships.append(relationship)
    return relationships


def _relation_type(evidence: str) -> str:
    """Map a small, auditable verb vocabulary to relation types."""

    if re.search(r"\b(?:founded|created|developed|built)\b", evidence, re.IGNORECASE):
        return "CREATED"
    if re.search(r"\b(?:works?\s+with|partner(?:ed|s)?|collaborat(?:e|ed|es))\b", evidence, re.IGNORECASE):
        return "COLLABORATES_WITH"
    if re.search(r"\b(?:uses?|leverag(?:e|ed|es))\b", evidence, re.IGNORECASE):
        return "USES"
    return "CO_OCCURS_WITH"


def validate_relationship(relationship: Relationship, entities: dict[str, Entity]) -> bool:
    """Validate referential integrity and safe relation payload constraints."""

    source = entities.get(relationship.source_entity_id)
    target = entities.get(relationship.target_entity_id)
    return bool(
        source
        and target
        and source.document_id == relationship.document_id == target.document_id
        and source.id != target.id
        and relationship.evidence.strip()
        and relationship.relation_type.replace("_", "").isalnum()
        and 0.0 <= relationship.confidence <= 1.0
    )


async def persist_document_knowledge(document_id: str, text: str) -> tuple[list[Entity], list[Relationship]]:
    """Extract, validate, and upsert document knowledge in SQLite."""

    extracted = extract_entities(text, document_id)
    by_key: dict[tuple[str, str], Entity] = {}
    for entity in extracted:
        by_key.setdefault((entity.text.casefold(), entity.label), entity)
    entities = list(by_key.values())
    relationships = extract_relationships(text, document_id, entities)
    entity_map = {entity.id: entity for entity in entities}
    relationships = [item for item in relationships if validate_relationship(item, entity_map)]

    async with async_session_factory() as session:
        await session.execute(delete(RelationshipDB).where(RelationshipDB.document_id == document_id))
        await session.execute(delete(EntityDB).where(EntityDB.document_id == document_id))
        session.add_all([
            EntityDB(id=entity.id, document_id=document_id, text=entity.text, label=entity.label,
                     confidence=entity.confidence, start_position=entity.start_position, end_position=entity.end_position)
            for entity in entities
        ])
        session.add_all([
            RelationshipDB(id=relationship.id, document_id=document_id,
                           source_entity_id=relationship.source_entity_id, target_entity_id=relationship.target_entity_id,
                           relation_type=relationship.relation_type, confidence=relationship.confidence,
                           evidence=relationship.evidence)
            for relationship in relationships
        ])
        await session.commit()
    return entities, relationships


def _entity_from_db(row: EntityDB) -> Entity:
    return Entity(id=row.id, document_id=row.document_id, text=row.text, label=row.label,
                  confidence=row.confidence, start_position=row.start_position, end_position=row.end_position,
                  created_at=row.created_at.replace(tzinfo=timezone.utc) if row.created_at.tzinfo is None else row.created_at)


def _relationship_from_db(row: RelationshipDB) -> Relationship:
    return Relationship(id=row.id, document_id=row.document_id, source_entity_id=row.source_entity_id,
                        target_entity_id=row.target_entity_id, relation_type=row.relation_type,
                        confidence=row.confidence, evidence=row.evidence,
                        created_at=row.created_at.replace(tzinfo=timezone.utc) if row.created_at.tzinfo is None else row.created_at)


async def list_persisted_entities(document_id: str | None = None) -> list[Entity]:
    async with async_session_factory() as session:
        query = select(EntityDB).order_by(EntityDB.start_position)
        if document_id:
            query = query.where(EntityDB.document_id == document_id)
        return [_entity_from_db(row) for row in (await session.execute(query)).scalars().all()]


async def list_persisted_relationships(document_id: str | None = None) -> list[Relationship]:
    async with async_session_factory() as session:
        query = select(RelationshipDB).order_by(RelationshipDB.created_at)
        if document_id:
            query = query.where(RelationshipDB.document_id == document_id)
        return [_relationship_from_db(row) for row in (await session.execute(query)).scalars().all()]


def get_entities(document_id: str | None = None) -> list[Entity]:
    return [item for item in _entities.values() if document_id is None or item.document_id == document_id]


def get_relationships(document_id: str | None = None) -> list[Relationship]:
    return [item for item in _relationships.values() if document_id is None or item.document_id == document_id]


def get_entity(entity_id: str) -> Entity | None:
    return _entities.get(entity_id)


def clear_document_knowledge(document_id: str) -> None:
    for entity_id in [key for key, value in _entities.items() if value.document_id == document_id]:
        del _entities[entity_id]
    for relationship_id in [key for key, value in _relationships.items() if value.document_id == document_id]:
        del _relationships[relationship_id]
