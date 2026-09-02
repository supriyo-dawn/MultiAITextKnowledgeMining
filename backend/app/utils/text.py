"""
Text processing utilities: cleaning, normalization, and basic processing.
"""

import re
from typing import Optional


def clean_text(text: str, remove_extra_whitespace: bool = True) -> str:
    """
    Clean text: remove control chars, normalize whitespace, etc.

    Args:
        text: Raw text to clean
        remove_extra_whitespace: If True, reduce multiple spaces to single space

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove control characters (but keep newlines, tabs)
    text = "".join(char if ord(char) >= 32 or char in "\n\t\r" else "" for char in text)

    # Normalize whitespace if requested
    if remove_extra_whitespace:
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
        # Replace multiple newlines with double newline
        text = re.sub(r"\n\n+", "\n\n", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace while preserving paragraph structure.

    Args:
        text: Text to normalize

    Returns:
        Text with normalized whitespace
    """
    # Split by double newlines (paragraphs)
    paragraphs = text.split("\n\n")

    # Clean each paragraph
    cleaned_paragraphs = []
    for para in paragraphs:
        # Replace newlines with spaces within paragraph
        para = " ".join(para.split())
        if para:
            cleaned_paragraphs.append(para)

    # Rejoin with double newlines
    return "\n\n".join(cleaned_paragraphs)


def extract_sentences(text: str) -> list[str]:
    """
    Simple sentence extraction (basic, not perfect).
    For production, use spaCy or similar.

    Args:
        text: Text to split into sentences

    Returns:
        List of sentences
    """
    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", text)

    # Filter empty sentences and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def get_text_statistics(text: str) -> dict:
    """
    Get basic text statistics.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with character_count, word_count, line_count
    """
    return {
        "character_count": len(text),
        "word_count": len(text.split()),
        "line_count": len(text.split("\n")),
        "paragraph_count": len(text.split("\n\n")),
    }
