from app.ai.ner import extract_entity_spans


def test_ner_prioritizes_structured_entities_and_preserves_offsets():
    text = "Alice emailed research@example.org on 2026-11-17 from https://example.org."

    entities = extract_entity_spans(text)

    assert [(item.text, item.label) for item in entities] == [
        ("Alice", "PERSON_OR_NAME"),
        ("research@example.org", "EMAIL"),
        ("2026-11-17", "DATE"),
        ("https://example.org", "URL"),
    ]
    assert all(text[item.start_position:item.end_position] == item.text for item in entities)


def test_ner_extracts_organizations_and_acronyms_without_nested_spans():
    text = "Acme University partnered with WHO and Acme University."

    entities = extract_entity_spans(text)

    assert [(item.text, item.label) for item in entities] == [
        ("Acme University", "ORG"),
        ("WHO", "ACRONYM"),
        ("Acme University", "ORG"),
    ]


def test_ner_is_deterministic_for_empty_and_punctuation_input():
    assert extract_entity_spans("") == []
    assert extract_entity_spans("  ... ") == []
