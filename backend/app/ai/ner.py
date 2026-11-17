"""Deterministic, dependency-free named-entity extraction.

The extractor is intentionally conservative: it uses ordered regular
expressions rather than an opaque model, so identical input always produces
identical spans, labels, and confidences.  Higher-priority expressions claim
their spans first to prevent nested or overlapping entities.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True, slots=True)
class EntitySpan:
    """A deterministic entity span produced from source text."""

    text: str
    label: str
    confidence: float
    start_position: int
    end_position: int


_PATTERNS: tuple[tuple[str, float, re.Pattern[str]], ...] = (
    (
        "EMAIL",
        0.99,
        re.compile(r"(?<![\w.+-])[\w.!#$%&'*+/=?^_`{|}~-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])"),
    ),
    (
        "URL",
        0.98,
        re.compile(r"(?<![\w])https?://[^\s<>()]+", re.IGNORECASE),
    ),
    (
        "DATE",
        0.95,
        re.compile(
            r"(?<!\w)(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2})(?!\w)"
        ),
    ),
    (
        "ORG",
        0.91,
        re.compile(
            r"(?<!\w)(?:[A-Z][\w&.-]*\s+){0,5}"
            r"(?:Inc\.?|Corp\.?|Corporation|LLC|Ltd\.?|"
            r"University|Institute|Company|学校)(?!\w)"
        ),
    ),
    (
        "ACRONYM",
        0.88,
        re.compile(r"(?<!\w)[A-Z][A-Z0-9&.-]{1,}(?!\w)"),
    ),
    (
        "PERSON_OR_NAME",
        0.78,
        re.compile(
            r"(?<!\w)(?:[A-Z][a-z]+(?:['-][A-Z][a-z]+)?"
            r"(?:\s+[A-Z][a-z]+(?:['-][A-Z][a-z]+)?){0,3})(?!\w)"
        ),
    ),
)


def _trim_entity(text: str, start: int, end: int) -> tuple[str, int, int]:
    """Remove punctuation accidentally captured at a boundary."""

    while start < end and text[start] in "([{":
        start += 1
    while end > start and text[end - 1] in ".,;:!?)]}":
        end -= 1
    return text[start:end], start, end


def extract_entity_spans(text: str) -> list[EntitySpan]:
    """Extract non-overlapping entities in stable source order.

    Empty or whitespace-only input returns no spans.  Duplicate mentions are
    retained because offsets are valuable to downstream relationship and
    citation logic; callers can deduplicate by normalized text when needed.
    """

    if not text or not text.strip():
        return []

    claimed: list[tuple[int, int]] = []
    candidates: list[EntitySpan] = []
    for label, confidence, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            value, start, end = _trim_entity(text, match.start(), match.end())
            if not value or any(start < other_end and end > other_start for other_start, other_end in claimed):
                continue
            claimed.append((start, end))
            candidates.append(EntitySpan(value, label, confidence, start, end))

    return sorted(candidates, key=lambda item: (item.start_position, item.end_position))
