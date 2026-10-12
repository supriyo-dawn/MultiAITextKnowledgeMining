"""Deterministic local entity and relationship extraction."""

import re
from collections import defaultdict

from app.models.knowledge import Entity, Relationship

_entities: dict[str, Entity] = {}
_relationships: dict[str, Relationship] = {}

_ENTITY_PATTERN = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2,})\b")


def extract_entities(text: str, document_id: str) -> list[Entity]:
    entities = []
    seen: set[tuple[str, str]] = set()
    for match in _ENTITY_PATTERN.finditer(text):
        value = match.group(0)
        label = "ORG" if value.isupper() or any(token in value.lower() for token in ("inc", "corp", "llc", "university")) else "ENTITY"
        key = (value.lower(), label)
        if key in seen:
            continue
        seen.add(key)
        entity = Entity(document_id=document_id, text=value, label=label, confidence=0.7, start_position=match.start(), end_position=match.end())
        _entities[entity.id] = entity
        entities.append(entity)
    return entities


def extract_relationships(text: str, document_id: str, entities: list[Entity]) -> list[Relationship]:
    relationships = []
    for left_index, left in enumerate(entities):
        for right in entities[left_index + 1:]:
            if right.start_position - left.end_position > 240:
                continue
            evidence = text[max(0, left.start_position - 60):min(len(text), right.end_position + 60)]
            relationship = Relationship(document_id=document_id, source_entity_id=left.id, target_entity_id=right.id, evidence=evidence, confidence=0.55)
            _relationships[relationship.id] = relationship
            relationships.append(relationship)
    return relationships


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
