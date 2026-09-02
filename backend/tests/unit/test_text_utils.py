"""Unit tests for text utilities."""

import pytest

from app.utils.text import (
    clean_text,
    extract_sentences,
    get_text_statistics,
    normalize_whitespace,
)


class TestCleanText:
    """Tests for text cleaning."""

    def test_remove_control_characters(self):
        """Test removal of control characters."""
        text = "Hello\x00World\x01Test"
        cleaned = clean_text(text)
        assert "\x00" not in cleaned
        assert "\x01" not in cleaned
        assert "HelloWorldTest" in cleaned

    def test_preserve_newlines(self):
        """Test that newlines are preserved."""
        text = "Line 1\nLine 2\nLine 3"
        cleaned = clean_text(text)
        assert "\n" in cleaned
        assert "Line 1" in cleaned

    def test_reduce_extra_spaces(self):
        """Test reduction of multiple spaces."""
        text = "Hello    World    Test"
        cleaned = clean_text(text, remove_extra_whitespace=True)
        assert "    " not in cleaned
        assert "Hello World Test" in cleaned

    def test_reduce_extra_newlines(self):
        """Test reduction of multiple newlines."""
        text = "Para 1\n\n\n\nPara 2"
        cleaned = clean_text(text, remove_extra_whitespace=True)
        assert "\n\n\n" not in cleaned
        assert "Para 1\n\nPara 2" in cleaned

    def test_strip_whitespace(self):
        """Test stripping of leading/trailing whitespace."""
        text = "   Hello World   "
        cleaned = clean_text(text)
        assert cleaned == "Hello World"

    def test_empty_string(self):
        """Test empty string handling."""
        assert clean_text("") == ""

    def test_whitespace_only(self):
        """Test whitespace-only string."""
        assert clean_text("   \n\n   ") == ""

    def test_preserve_tabs(self):
        """Test that tabs are preserved."""
        text = "Col1\tCol2\tCol3"
        cleaned = clean_text(text)
        assert "\t" in cleaned


class TestNormalizeWhitespace:
    """Tests for whitespace normalization."""

    def test_normalize_paragraph_whitespace(self):
        """Test normalization within paragraphs."""
        text = "Line 1\n  Line 2\nLine 3\n\nPara 2"
        normalized = normalize_whitespace(text)

        # Should have double newline between paragraphs
        assert "\n\n" in normalized
        # Each paragraph should have single spaces
        parts = normalized.split("\n\n")
        for part in parts:
            assert "  " not in part

    def test_empty_paragraphs_removed(self):
        """Test removal of empty paragraphs."""
        text = "\n\n\n\n"
        normalized = normalize_whitespace(text)
        assert normalized == ""

    def test_preserve_paragraph_structure(self):
        """Test that paragraph structure is preserved."""
        text = "Para 1\n\nPara 2\n\nPara 3"
        normalized = normalize_whitespace(text)
        parts = normalized.split("\n\n")
        assert len(parts) == 3
        assert parts[0] == "Para 1"
        assert parts[1] == "Para 2"
        assert parts[2] == "Para 3"


class TestExtractSentences:
    """Tests for sentence extraction."""

    def test_extract_basic_sentences(self):
        """Test extraction of basic sentences."""
        text = "First sentence. Second sentence. Third sentence."
        sentences = extract_sentences(text)

        assert len(sentences) == 3
        assert sentences[0] == "First sentence."
        assert sentences[1] == "Second sentence."
        assert sentences[2] == "Third sentence."

    def test_multiple_punctuation_marks(self):
        """Test sentences with different punctuation."""
        text = "Question? Answer! Statement."
        sentences = extract_sentences(text)

        assert len(sentences) == 3
        assert "Question?" in sentences
        assert "Answer!" in sentences
        assert "Statement." in sentences

    def test_empty_string(self):
        """Test empty string handling."""
        sentences = extract_sentences("")
        assert sentences == []

    def test_no_periods(self):
        """Test text without periods (single 'sentence')."""
        text = "No punctuation here"
        sentences = extract_sentences(text)
        assert len(sentences) >= 1

    def test_multiple_spaces_between_sentences(self):
        """Test handling of multiple spaces."""
        text = "First.  Second.   Third."
        sentences = extract_sentences(text)

        # Should still extract three sentences
        assert any("First" in s for s in sentences)
        assert any("Second" in s for s in sentences)
        assert any("Third" in s for s in sentences)


class TestGetTextStatistics:
    """Tests for text statistics."""

    def test_character_count(self):
        """Test character count."""
        text = "Hello"
        stats = get_text_statistics(text)
        assert stats["character_count"] == 5

    def test_word_count(self):
        """Test word count."""
        text = "Hello world test"
        stats = get_text_statistics(text)
        assert stats["word_count"] == 3

    def test_line_count(self):
        """Test line count."""
        text = "Line 1\nLine 2\nLine 3"
        stats = get_text_statistics(text)
        assert stats["line_count"] == 3

    def test_paragraph_count(self):
        """Test paragraph count."""
        text = "Para 1\n\nPara 2\n\nPara 3"
        stats = get_text_statistics(text)
        assert stats["paragraph_count"] == 3

    def test_empty_text_statistics(self):
        """Test statistics for empty text."""
        text = ""
        stats = get_text_statistics(text)
        assert stats["character_count"] == 0
        assert stats["word_count"] == 0

    def test_complex_text_statistics(self):
        """Test statistics for complex text."""
        text = """This is paragraph one.
It has multiple lines.

This is paragraph two.
It also has lines."""

        stats = get_text_statistics(text)
        assert stats["character_count"] > 0
        assert stats["word_count"] > 4
        assert stats["line_count"] > 3
        assert stats["paragraph_count"] >= 2
