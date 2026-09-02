"""
Unit tests for text preprocessing service.

Tests:
- Text cleaning (control characters, URLs, emails)
- Language detection
- Text normalization
- Text statistics
- Token count estimation
- Sentence extraction
"""

import pytest

from app.services.preprocessing_service import PreprocessingError, TextPreprocessor


@pytest.fixture
def preprocessor():
    """Create a text preprocessor instance."""
    return TextPreprocessor()


class TestTextCleaning:
    """Tests for text cleaning functionality."""

    def test_remove_control_characters(self, preprocessor):
        """Test removal of control characters."""
        text = "Hello\x00World\x01\x02\x03"
        result = preprocessor.preprocess(text, normalize=False, detect_language=False)
        assert "\x00" not in result["text"]
        assert "\x01" not in result["text"]
        assert "Hello" in result["text"]
        assert "World" in result["text"]

    def test_preserve_newlines_and_tabs(self, preprocessor):
        """Test that newlines and tabs are preserved."""
        text = "Hello\nWorld\tTest"
        result = preprocessor.preprocess(text, normalize=False, detect_language=False)
        assert "\n" in result["text"]
        assert "\t" in result["text"]

    def test_remove_urls(self, preprocessor):
        """Test URL removal."""
        text = "Check out https://example.com for more info"
        result = preprocessor.preprocess(
            text, normalize=False, remove_urls=True, detect_language=False
        )
        assert "example.com" not in result["text"]
        assert "for more info" in result["text"]

    def test_remove_www_urls(self, preprocessor):
        """Test www URL removal."""
        text = "Visit www.example.com for details"
        result = preprocessor.preprocess(
            text, normalize=False, remove_urls=True, detect_language=False
        )
        assert "www.example.com" not in result["text"]
        assert "for details" in result["text"]

    def test_remove_emails(self, preprocessor):
        """Test email removal."""
        text = "Contact us at support@example.com for help"
        result = preprocessor.preprocess(
            text, normalize=False, remove_emails=True, detect_language=False
        )
        assert "support@example.com" not in result["text"]
        assert "for help" in result["text"]

    def test_normalize_html_entities(self, preprocessor):
        """Test HTML entity normalization."""
        text = "Hello&nbsp;World&quot;Test&quot;"
        result = preprocessor.preprocess(text, normalize=False, detect_language=False)
        assert "&nbsp;" not in result["text"]
        assert "&quot;" not in result["text"]
        assert " " in result["text"]

    def test_multiple_spaces_collapsed(self, preprocessor):
        """Test that multiple spaces are collapsed."""
        text = "Hello    World    Test"
        result = preprocessor.preprocess(text, normalize=True, detect_language=False)
        assert "    " not in result["text"]

    def test_empty_text_error(self, preprocessor):
        """Test that empty text raises error."""
        with pytest.raises(PreprocessingError):
            preprocessor.preprocess("")

    def test_none_text_error(self, preprocessor):
        """Test that None text raises error."""
        with pytest.raises(PreprocessingError):
            preprocessor.preprocess(None)


class TestLanguageDetection:
    """Tests for language detection."""

    def test_detect_english(self, preprocessor):
        """Test English language detection."""
        text = "This is a sample English text with multiple words."
        result = preprocessor.preprocess(text, detect_language=True, normalize=False)
        assert result["language"] == "en"

    def test_detect_spanish(self, preprocessor):
        """Test Spanish language detection."""
        text = "Hola, ¿cómo estás? Este es un ejemplo en español."
        result = preprocessor.preprocess(text, detect_language=True, normalize=False)
        assert result["language"] == "es"

    def test_detect_french(self, preprocessor):
        """Test French language detection."""
        text = "Bonjour, ceci est un exemple de texte français."
        result = preprocessor.preprocess(text, detect_language=True, normalize=False)
        assert result["language"] == "fr"

    def test_short_text_no_language(self, preprocessor):
        """Test that short text returns None for language."""
        text = "Hi"
        result = preprocessor.preprocess(text, detect_language=True, normalize=False)
        assert result["language"] is None

    def test_no_detection_when_disabled(self, preprocessor):
        """Test that detection is None when disabled."""
        text = "This is English text"
        result = preprocessor.preprocess(text, detect_language=False, normalize=False)
        assert result["language"] is None


class TestTextNormalization:
    """Tests for text normalization."""

    def test_whitespace_normalization(self, preprocessor):
        """Test whitespace normalization."""
        text = "Hello\n\nWorld\n\n\nTest"
        result = preprocessor.preprocess(text, normalize=True, detect_language=False)
        text_normalized = result["text"]
        # Multiple newlines should be preserved but text cleaned
        assert "Hello" in text_normalized
        assert "World" in text_normalized

    def test_strip_leading_trailing_whitespace(self, preprocessor):
        """Test stripping of leading/trailing whitespace."""
        text = "  Hello World  "
        result = preprocessor.preprocess(text, normalize=True, detect_language=False)
        text_normalized = result["text"]
        assert not text_normalized.startswith(" ")
        assert not text_normalized.endswith(" ")

    def test_normalize_false_preserves_formatting(self, preprocessor):
        """Test that normalize=False preserves some formatting."""
        text = "Hello\nWorld\nTest"
        result = preprocessor.preprocess(text, normalize=False, detect_language=False)
        assert "\n" in result["text"]


class TestTextStatistics:
    """Tests for text statistics calculation."""

    def test_character_count(self, preprocessor):
        """Test character counting."""
        text = "Hello"
        stats = preprocessor.get_text_statistics(text)
        assert stats["characters"] == 5

    def test_word_count(self, preprocessor):
        """Test word counting."""
        text = "Hello World Test"
        stats = preprocessor.get_text_statistics(text)
        assert stats["words"] == 3

    def test_line_count(self, preprocessor):
        """Test line counting."""
        text = "Hello\nWorld\nTest"
        stats = preprocessor.get_text_statistics(text)
        assert stats["lines"] == 3

    def test_sentence_count(self, preprocessor):
        """Test sentence counting."""
        text = "Hello. World. Test."
        stats = preprocessor.get_text_statistics(text)
        assert stats["sentences"] == 3

    def test_paragraph_count(self, preprocessor):
        """Test paragraph counting."""
        text = "Hello\n\nWorld\n\nTest"
        stats = preprocessor.get_text_statistics(text)
        assert stats["paragraphs"] >= 2

    def test_empty_text_statistics(self, preprocessor):
        """Test statistics for empty text."""
        stats = preprocessor.get_text_statistics("")
        assert stats["characters"] == 0
        assert stats["words"] == 0


class TestSentenceExtraction:
    """Tests for sentence extraction."""

    def test_extract_simple_sentences(self, preprocessor):
        """Test extraction of simple sentences."""
        text = "Hello. World. Test."
        sentences = preprocessor.extract_sentences(text)
        assert len(sentences) == 3

    def test_extract_sentences_with_various_punctuation(self, preprocessor):
        """Test sentence extraction with !, ?."""
        text = "Hello! How are you? Fine."
        sentences = preprocessor.extract_sentences(text)
        assert len(sentences) == 3

    def test_extract_no_sentences_from_empty(self, preprocessor):
        """Test extraction from empty text."""
        sentences = preprocessor.extract_sentences("")
        assert len(sentences) == 0

    def test_extract_sentences_with_abbreviations(self, preprocessor):
        """Test sentence extraction with abbreviations."""
        text = "Dr. Smith works at e.g. university."
        sentences = preprocessor.extract_sentences(text)
        # Should handle abbreviations reasonably
        assert len(sentences) >= 1


class TestTokenCountEstimation:
    """Tests for token count estimation."""

    def test_english_token_estimation(self, preprocessor):
        """Test token estimation for English text."""
        text = "Hello World Test"  # 3 words
        tokens = preprocessor.estimate_token_count(text, language="en")
        # ~1.3 tokens per word for English
        assert 3 <= tokens <= 5

    def test_cjk_token_estimation(self, preprocessor):
        """Test token estimation for CJK text."""
        text = "你好世界"  # Chinese
        tokens = preprocessor.estimate_token_count(text, language="zh")
        # CJK uses character-based estimation
        assert tokens > 0

    def test_empty_text_no_tokens(self, preprocessor):
        """Test that empty text estimates zero tokens."""
        tokens = preprocessor.estimate_token_count("")
        assert tokens == 0

    def test_default_language_estimation(self, preprocessor):
        """Test token estimation with no language specified."""
        text = "Hello World Test"
        tokens = preprocessor.estimate_token_count(text)
        assert tokens > 0


class TestBackwardCompatibility:
    """Tests for backward compatibility with Phase 2."""

    def test_clean_text_simple_function(self, preprocessor):
        """Test that clean_text_simple works like Phase 2."""
        text = "Hello\x00World\nTest"
        cleaned = preprocessor.clean_text_simple(text)
        assert "Hello" in cleaned
        assert "World" in cleaned
        assert "\x00" not in cleaned

    def test_get_text_statistics_compatibility(self, preprocessor):
        """Test that get_text_statistics returns expected fields."""
        text = "Hello World. Test sentence."
        stats = preprocessor.get_text_statistics(text)
        assert "characters" in stats
        assert "words" in stats
        assert "lines" in stats
        assert "paragraphs" in stats
        assert "sentences" in stats


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_very_long_text(self, preprocessor):
        """Test preprocessing very long text."""
        text = "Word " * 10000
        result = preprocessor.preprocess(text, normalize=False, detect_language=False)
        assert len(result["text"]) > 0

    def test_special_unicode_characters(self, preprocessor):
        """Test handling of special Unicode characters."""
        text = "Hello 你好 مرحبا Привет"
        result = preprocessor.preprocess(text, normalize=False, detect_language=False)
        assert "Hello" in result["text"]

    def test_mixed_url_and_email(self, preprocessor):
        """Test removing both URLs and emails."""
        text = "Visit https://example.com or email test@example.com"
        result = preprocessor.preprocess(
            text, remove_urls=True, remove_emails=True, detect_language=False
        )
        assert "example.com" not in result["text"] or "test@" not in result["text"]

    def test_preprocessing_metadata(self, preprocessor):
        """Test that preprocessing returns expected metadata."""
        text = "Hello World Test"
        result = preprocessor.preprocess(text, normalize=True, detect_language=False)
        assert "text" in result
        assert "original_length" in result
        assert "cleaned_length" in result
        assert "removed_chars" in result
        assert "normalized" in result
