from app.services.knowledge_service import extract_entities, extract_relationships


def test_extract_entities_deduplicates_capitalized_terms():
    entities = extract_entities("Alice works with Acme. Alice joined Acme.", "doc-1")
    assert {entity.text for entity in entities} == {"Alice", "Acme"}
    assert all(entity.document_id == "doc-1" for entity in entities)


def test_extract_relationships_only_links_nearby_entities():
    entities = extract_entities("Alice joined Acme.", "doc-2")
    relationships = extract_relationships("Alice joined Acme.", "doc-2", entities)
    assert len(relationships) == 1
    assert relationships[0].relation_type == "CO_OCCURS_WITH"


def test_empty_text_has_no_knowledge():
    assert extract_entities("", "doc-3") == []
